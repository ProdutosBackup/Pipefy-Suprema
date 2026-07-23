import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from api.pipefy_client import fetch_cards_by_phase, fetch_card_by_id, move_card_to_phase, duplicate_card, clone_card, update_card_field, fetch_phase_fields, create_card, fetch_start_form_fields, update_card_labels
from utils.helpers import transform_pipefy_card, sort_cards_by_date

load_dotenv()

TEMPLATES_PATH = os.path.join(os.path.dirname(__file__), "templates.json")

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
    if not os.path.exists(TEMPLATES_PATH):
        return jsonify({"success": True, "templates": []})
    with open(TEMPLATES_PATH, "r") as f:
        dados = json.load(f)
    return jsonify({"success": True, "templates": dados})


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
            "id": f"tmpl_{int(time.time())}",
            "liga": fields.get("Liga/Union", ""),
            "clube": clube_customizado or fields.get("Nome do clube/Nombre del club/Club name", ""),
            "nome_evento": evento_customizado or fields.get("Nome do evento/Nombre del evento/Name of the event", ""),
            "garantido": fields.get("Premiação garantida/Garantizado/Prize pool", "0"),
            "card_id_origem": card_id,
            "criado_em": datetime.utcnow().isoformat(),
            "campos_completos": fields
        }
        
        templates = []
        if os.path.exists(TEMPLATES_PATH):
            with open(TEMPLATES_PATH, "r") as f:
                templates = json.load(f)
        
        templates.append(template)
        with open(TEMPLATES_PATH, "w") as f:
            json.dump(templates, f, indent=2)
        return jsonify({"success": True, "template": template})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/deletar-template", methods=["POST"])
def deletar_template():
    data = request.get_json(silent=True) or {}
    template_id = data.get("template_id")
    if not template_id:
        return jsonify({"success": False, "error": "template_id é obrigatório"}), 400
    try:
        if not os.path.exists(TEMPLATES_PATH):
            return jsonify({"success": False, "error": "Nenhum template encontrado"}), 404
        with open(TEMPLATES_PATH, "r") as f:
            templates = json.load(f)
        novos = [t for t in templates if t.get("id") != template_id]
        if len(novos) == len(templates):
            return jsonify({"success": False, "error": "Template não encontrado"}), 404
        with open(TEMPLATES_PATH, "w") as f:
            json.dump(novos, f, indent=2)
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
