import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from api.pipefy_client import fetch_cards_by_phase, move_card_to_phase, duplicate_card
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
