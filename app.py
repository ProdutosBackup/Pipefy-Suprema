import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from api.pipefy_client import fetch_cards_by_phase, fetch_card_by_id, move_card_to_phase, duplicate_card, clone_card, update_card_field
from utils.helpers import transform_pipefy_card, sort_cards_by_date

load_dotenv()

app = Flask(
    __name__,
    template_folder="front",
    static_folder="front",
    static_url_path=""
)

COLUNAS = {
    "Caixa de entrada":     {"id": "326331441"},
    "Analise de estrutura": {"id": "326331442"},
    "Criacao":              {"id": "326331443"},
    "Lobby":                {"id": "326331444"},
    "Concluido":            {"id": "326331445"},
}

@app.route("/")
def index():
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
