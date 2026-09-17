import os
import json
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from api.pipefy_client import fetch_cards_by_phase, fetch_cards_search, fetch_card_by_id, move_card_to_phase, duplicate_card, clone_card, update_card_field, fetch_phase_fields, create_card, fetch_start_form_fields, update_card_labels
from utils.helpers import transform_pipefy_card, sort_cards_by_date

import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()

TEMPLATES_PATH = os.path.join(os.path.dirname(__file__), "templates.json")
LOCAL_CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "firebase-key.json")


def _get_firebase_credentials():
    raw = os.environ.get("FIREBASE_CREDENTIALS")
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raise RuntimeError("FIREBASE_CREDENTIALS está presente mas é um JSON inválido.")
    if os.path.exists(LOCAL_CREDENTIALS_PATH):
        with open(LOCAL_CREDENTIALS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    raise RuntimeError(
        "Credenciais do Firebase ausentes. Defina a env var FIREBASE_CREDENTIALS "
        "ou crie o arquivo local firebase-key.json."
    )


_credentials = _get_firebase_credentials()
firebase_admin.initialize_app(credentials.Certificate(_credentials))
db = firestore.client()
TEMPLATES_COLL = db.collection("templates_pipefy")
TORNEIOS_COLL = db.collection("torneios_ids")


def migrar_templates_file():
    if not os.path.exists(TEMPLATES_PATH):
        return
    if not TEMPLATES_COLL.limit(1).get():
        try:
            with open(TEMPLATES_PATH, "r", encoding="utf-8") as f:
                templates = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return
        if not isinstance(templates, list):
            return
        for i in range(0, len(templates), 500):
            batch = db.batch()
            for t in templates[i:i + 500]:
                batch.set(TEMPLATES_COLL.document(), t)
            batch.commit()
    os.rename(TEMPLATES_PATH, TEMPLATES_PATH + ".migrado")
    print("[MIGRAÇÃO] templates.json transferido para Firestore (templates_pipefy).")


migrar_templates_file()

app = Flask(
    __name__,
    template_folder="front",
    static_folder="front",
    static_url_path=""
)

app.secret_key = 'sua_chave_secreta_super_segura_aqui'

COLUNAS = {
    "Caixa de entrada":     {"id": "326331441"},
    "Analise de estrutura": {"id": "326331442"},
    "Criacao":              {"id": "326331443"},
    "Lobby":                {"id": "326331444"},
    "Concluido":            {"id": "326331445"},
}

@app.route("/")
def index():
    if not session.get('logado'):
        return redirect(url_for('login_page'))
    colunas = {}
    for slug, cfg in COLUNAS.items():
        try:
            raw = fetch_cards_by_phase(cfg["id"])
            colunas[slug] = {
                "id": cfg["id"],
                "cards": sort_cards_by_date([transform_pipefy_card(e) for e in raw])
            }
        except Exception as e:
            print(f"[ERRO] {slug}: {e}")
            colunas[slug] = {"id": cfg["id"], "cards": []}
    return render_template("index.html", colunas=colunas)

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/api/auth", methods=["POST"])
def api_auth():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    senha = data.get("senha", "").strip()

    caminho_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'usuarios.json')

    usuarios_permitidos = {}
    try:
        with open(caminho_json, 'r', encoding='utf-8') as f:
            usuarios_permitidos = json.load(f)
    except Exception as e:
        print(f"Erro ao ler usuarios.json: {e}")
        return jsonify({"success": False, "error": "Erro interno no servidor de autenticação."}), 500

    if email in usuarios_permitidos and str(usuarios_permitidos[email]) == str(senha):
        session['logado'] = True
        session['email'] = email
        return jsonify({"success": True})

    return jsonify({"success": False, "error": "E-mail ou senha incorretos."}), 401

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login_page'))


@app.route("/api/mover-card", methods=["POST"])
def mover_card():
    data = request.get_json(silent=True) or {}
    card_id = data.get("card_id")
    fase_destino_id = data.get("fase_destino_id")
    if not card_id or not fase_destino_id:
        return jsonify({"success": False, "error": "card_id e fase_destino_id são obrigatórios"}), 400
    try:
        move_card_to_phase(card_id, fase_destino_id)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/duplicar-card", methods=["POST"])
def duplicar_card():
    data = request.get_json(silent=True) or {}
    card_id = data.get("card_id")
    fase_id = data.get("fase_id")
    pipe_id = os.environ.get("PIPEFY_PIPE_ID")
    if not card_id or not fase_id:
        return jsonify({"success": False, "error": "card_id e fase_id são obrigatórios"}), 400
    if not pipe_id:
        return jsonify({"success": False, "error": "PIPEFY_PIPE_ID não configurado"}), 500
    try:
        result = duplicate_card(card_id, pipe_id, fase_id)
        card_node = result.get("card", {})
        return jsonify({
            "success": True,
            "card": {
                "id": card_node.get("id"),
                "titulo": card_node.get("title", ""),
                "clube": "",
                "jogo": "",
                "data_hora": "",
                "protocolo": f"#{card_node.get('id', '')}",
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/cards/<card_id>/clone", methods=["POST"])
def clonar_card(card_id):
    try:
        result = clone_card(card_id)
        card_node = result.get("card", {})
        return jsonify({
            "success": True,
            "card": {
                "id": card_node.get("id"),
                "titulo": card_node.get("title", ""),
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/cards/<card_id>/upload", methods=["POST"])
def api_upload_imagem(card_id):
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "Nenhum arquivo enviado"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "Arquivo vazio"}), 400
    try:
        from api.pipefy_client import upload_attachment
        upload_attachment(card_id, file)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/cards/<card_id>")
def card_detalhes(card_id):
    try:
        card = fetch_card_by_id(card_id)
        if not card:
            return jsonify({"success": False, "error": "Card não encontrado"}), 404
        return jsonify({
            "success": True,
            "card": {
                "id": card.get("id"),
                "titulo": card.get("title", ""),
                "pipe_id": card.get("pipe", {}).get("id"),
                "current_phase": {"id": card.get("current_phase", {}).get("id"), "name": card.get("current_phase", {}).get("name")},
                "campos": [
                    {"name": f.get("name", ""), "value": f.get("value", ""), "field_id": f.get("field", {}).get("id")}
                    for f in card.get("fields", [])
                ]
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/buscar")
def buscar_cards():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"success": True, "cards": []})

    pipe_id = os.environ.get("PIPEFY_PIPE_ID")
    if not pipe_id:
        return jsonify({"success": False, "error": "PIPEFY_PIPE_ID não configurado"}), 500

    try:
        raw = fetch_cards_search(pipe_id, q)
        cards = []
        for e in raw:
            card = transform_pipefy_card(e)
            node = e.get("node", {})
            phase = node.get("current_phase", {}) or {}
            card["fase_id"] = phase.get("id")
            card["fase_nome"] = phase.get("name")
            cards.append(card)
        return jsonify({"success": True, "cards": cards})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/cards/<card_id>/fields", methods=["PUT"])
def atualizar_campo(card_id):
    data = request.get_json(silent=True) or {}
    field_id = data.get("field_id")
    new_value = data.get("new_value")
    if not field_id or new_value is None:
        return jsonify({"success": False, "error": "field_id e new_value são obrigatórios"}), 400
    try:
        update_card_field(card_id, field_id, new_value)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/pipe-fields")
def api_pipe_fields():
    pipe_id = os.environ.get("PIPEFY_PIPE_ID")
    if not pipe_id:
        return jsonify({"success": False, "error": "PIPEFY_PIPE_ID não configurado"}), 500
    try:
        fields = fetch_start_form_fields(pipe_id)
        return jsonify({"success": True, "fields": [{"id": f["id"], "label": f["label"]} for f in fields]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/criar-card", methods=["POST"])
def criar_card():
    data = request.get_json(silent=True) or {}
    pipe_id = os.environ.get("PIPEFY_PIPE_ID")
    phase_id = data.get("phase_id")
    title = data.get("title", "Novo Card")
    fields = data.get("fields", [])
    label_ids = data.get("label_ids", [])
 
    if not pipe_id:
        return jsonify({"success": False, "error": "PIPEFY_PIPE_ID não configurado"}), 500
    if not phase_id:
        return jsonify({"success": False, "error": "phase_id é obrigatório"}), 400
    if not isinstance(fields, list):
        return jsonify({"success": False, "error": "fields deve ser uma lista"}), 400

    try:
        fields_attributes = []
        for f in fields:
            val = f.get("value", "")
            if isinstance(val, list):
                final_val = val
            else:
                final_val = str(val)
            fields_attributes.append({"field_id": f["field_id"], "field_value": final_val})
        result = create_card(pipe_id, phase_id, title, fields_attributes, label_ids)
        card_node = result.get("card", {})
        return jsonify({
            "success": True,
            "card": {
                "id": card_node.get("id"),
                "titulo": card_node.get("title", ""),
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/templates")
def listar_templates():
    docs = TEMPLATES_COLL.order_by("__name__").stream()
    templates = [d.to_dict() for d in docs]
    return jsonify({"success": True, "templates": templates})


@app.route("/api/salvar-template", methods=["POST"])
def salvar_template():
    data = request.get_json(silent=True) or {}
    card_id = data.get("card_id")
    clube_customizado = (data.get("clube_customizado") or "").strip()
    evento_customizado = (data.get("evento_customizado") or "").strip()
    
    if not card_id:
        return jsonify({"success": False, "error": "card_id é obrigatório"}), 400
    try:
        card = fetch_card_by_id(card_id)
        fields = {f["name"]: f["value"] for f in card.get("fields", [])}
        
        template = {
            "liga": fields.get("Liga/Union", ""),
            "clube": clube_customizado or fields.get("Nome do clube/Nombre del club/Club name", ""),
            "nome_evento": evento_customizado or fields.get("Nome do evento/Nombre del evento/Name of the event", ""),
            "garantido": fields.get("Premiação garantida/Garantizado/Prize pool", "0"),
            "card_id_origem": card_id,
            "criado_em": datetime.utcnow().isoformat(),
            "campos_completos": fields
        }

        doc_ref = TEMPLATES_COLL.document()
        doc_ref.set(template)
        template["id"] = doc_ref.id
        return jsonify({"success": True, "template": template})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/salvar-template-form", methods=["POST"])
def salvar_template_form():
    try:
        data = request.get_json(silent=True) or {}

        # 1. Validações Iniciais
        if not isinstance(data, dict):
            return jsonify({"success": False, "error": "Payload inválido. Esperado JSON (Dictionary)."}), 400

        liga = data.get("liga", "")
        clube = data.get("clube", "")
        fields = data.get("fields", [])

        # 2. Defesa de Tipagem (Evita AttributeError no laço for)
        if not isinstance(fields, list):
            return jsonify({"success": False, "error": "Formato de 'fields' inválido. Esperada uma Lista."}), 400

        # 3. Extração Segura de Dados do Template
        nome_evento = "Novo Evento"
        garantido = "0"

        for f in fields:
            if not isinstance(f, dict): continue  # Ignora itens corrompidos dentro do array

            # O front agora envia 'nome_pipefy' e 'valor'
            nome_pipefy = str(f.get("nome_pipefy", "")).lower()
            valor_campo = str(f.get("valor", ""))

            if "evento" in nome_pipefy:
                nome_evento = valor_campo
            if "premia" in nome_pipefy or "garantido" in nome_pipefy:
                garantido = valor_campo

        # 4. Montagem Estrutural
        template = {
            "liga": liga,
            "clube": clube,
            "nome_evento": nome_evento,
            "garantido": garantido,
            "criado_em": datetime.utcnow().isoformat(),
            "campos_completos": fields
        }

        # 5. Gravação no Firestore com ID auto-gerado
        doc_ref = TEMPLATES_COLL.document()
        doc_ref.set(template)
        template["id"] = doc_ref.id

        return jsonify({"success": True, "template": template}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()  # Loga o erro real no terminal do Python
        return jsonify({"success": False, "error": f"Erro interno no servidor: {str(e)}"}), 500


@app.route("/api/deletar-template-batch", methods=["POST"])
def deletar_template_batch():
    data = request.get_json(silent=True) or {}
    template_ids = data.get("template_ids", [])
    if not isinstance(template_ids, list) or not template_ids:
        return jsonify({"success": False, "error": "template_ids é obrigatório"}), 400
    try:
        batch = db.batch()
        excluidos = 0
        for tid in template_ids:
            ref = TEMPLATES_COLL.document(str(tid))
            if ref.get().exists:
                batch.delete(ref)
                excluidos += 1
        if excluidos == 0:
            return jsonify({"success": False, "error": "Nenhum template encontrado para exclusão"}), 404
        batch.commit()
        return jsonify({"success": True, "excluidos": excluidos})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/deletar-template", methods=["POST"])
def deletar_template():
    data = request.get_json(silent=True) or {}
    template_id = data.get("template_id")
    if not template_id:
        return jsonify({"success": False, "error": "template_id é obrigatório"}), 400
    try:
        ref = TEMPLATES_COLL.document(str(template_id))
        if not ref.get().exists:
            return jsonify({"success": False, "error": "Template não encontrado"}), 404
        ref.delete()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/atualizar-labels", methods=["POST"])
def atualizar_labels():
    data = request.get_json(silent=True) or {}
    card_id = data.get("card_id")
    label_ids = data.get("label_ids", [])
    if not card_id:
        return jsonify({"success": False, "error": "card_id é obrigatório"}), 400
    try:
        update_card_labels(card_id, label_ids)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/salvar-torneio", methods=["POST"])
def salvar_torneio():
    data = request.get_json(silent=True) or {}
    nome_torneio = (data.get("nome_torneio") or "").strip()
    id_clas = data.get("id_clas")
    responsavel = (data.get("responsavel") or "").strip()
    data_torneio = (data.get("data_torneio") or "").strip()
    status = (data.get("status") or "pendente").strip()

    if not nome_torneio:
        return jsonify({"success": False, "error": "nome_torneio é obrigatório"}), 400
    if id_clas is None or id_clas == "":
        return jsonify({"success": False, "error": "id_clas é obrigatório"}), 400
    if not responsavel:
        return jsonify({"success": False, "error": "responsavel é obrigatório"}), 400
    if not data_torneio:
        return jsonify({"success": False, "error": "data_torneio é obrigatório"}), 400

    try:
        torneio = {
            "nome_torneio": nome_torneio,
            "id_clas": int(id_clas),
            "responsavel": responsavel,
            "data_torneio": data_torneio,
            "status": status
        }
        doc_ref = TORNEIOS_COLL.document(str(id_clas))
        doc_ref.set(torneio, merge=True)
        torneio_result = dict(torneio)
        torneio_result["id"] = doc_ref.id
        return jsonify({"success": True, "torneio": torneio_result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/torneios")
def listar_torneios():
    try:
        docs = TORNEIOS_COLL.order_by("__name__").stream()
        torneios = [d.to_dict() for d in docs]
        return jsonify({"success": True, "torneios": torneios})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/deletar-torneio/<id_clas>", methods=["DELETE"])
def deletar_torneio(id_clas):
    try:
        ref = TORNEIOS_COLL.document(str(id_clas))
        if not ref.get().exists:
            return jsonify({"success": False, "error": "Torneio não encontrado"}), 404
        ref.delete()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
