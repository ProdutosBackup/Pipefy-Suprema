import os
from dotenv import load_dotenv
from flask import Flask, render_template
from api.pipefy_client import fetch_cards_by_phase
from utils.helpers import transform_pipefy_card

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
            colunas[slug] = [transform_pipefy_card(e) for e in raw]
        except Exception as e:
            print(f"[ERRO] {slug}: {e}")
            colunas[slug] = []
    return render_template("index.html", colunas=colunas)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
