import os
import requests

PIPEFY_API = "https://api.pipefy.com/graphql"

def _headers():
    token = os.environ.get("PIPEFY_TOKEN")
    if not token:
        raise ValueError("PIPEFY_TOKEN não definido nas variáveis de ambiente")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def _post(query, variables=None):
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    resp = requests.post(PIPEFY_API, json=payload, headers=_headers())
    resp.raise_for_status()

    json_resp = resp.json()
    if "errors" in json_resp:
        msgs = "; ".join(e.get("message", "Erro Desconhecido") for e in json_resp["errors"])
        raise Exception(f"Erro GraphQL: {msgs}")

    return json_resp

def fetch_cards_by_phase(phase_id):
    query = """
    query ($phaseId: ID!) {
      phase(id: $phaseId) {
        cards {
          edges {
            node {
              id
              title
              fields {
                name
                value
              }
            }
          }
        }
      }
    }
    """
    data = _post(query, variables={"phaseId": phase_id})
    return data.get("data", {}).get("phase", {}).get("cards", {}).get("edges", [])

def fetch_phases(pipe_id):
    query = """
    query ($pipeId: ID!) {
      pipe(id: $pipeId) {
        phases {
          id
          name
        }
      }
    }
    """
    data = _post(query, variables={"pipeId": pipe_id})
    return data.get("data", {}).get("pipe", {}).get("phases", [])
