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
        cards(last: 50) {
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


def fetch_card_by_id(card_id):
    query = """
    query ($cardId: ID!) {
        card(id: $cardId) {
            id
            title
            fields {
                name
                value
            }
        }
    }
    """
    data = _post(query, variables={"cardId": card_id})
    
    # Log em caso de erro na resposta GraphQL
    if "errors" in data:
        raise Exception(f"Erro GraphQL: {data['errors'][0].get('message')}")
        
    return data.get("data", {}).get("card", {})


def move_card_to_phase(card_id, phase_id):
    query = """
    mutation ($cardId: ID!, $destinationPhaseId: ID!) {
      moveCardToPhase(input: {
        card_id: $cardId,
        destination_phase_id: $destinationPhaseId
      }) {
        card { id title }
      }
    }
    """
    data = _post(query, variables={
        "cardId": card_id,
        "destinationPhaseId": phase_id
    })
    return data.get("data", {}).get("moveCardToPhase", {})


def duplicate_card(card_id, pipe_id, phase_id):
    card_data = fetch_card_by_id(card_id)
    if not card_data:
        raise Exception("Card não encontrado")

    title = card_data.get("title", "")
    fields_attributes = [
        {"field_id": f["id"], "value": f.get("value", "")}
        for f in card_data.get("fields", [])
        if f.get("id")
    ]

    query = """
    mutation ($pipeId: ID!, $phaseId: ID!, $title: String!, $fieldsAttributes: [FieldInput!]!) {
      createCard(input: {
        pipe_id: $pipeId,
        phase_id: $phaseId,
        title: $title,
        fields_attributes: $fieldsAttributes
      }) {
        card {
          id
          title
          fields { name value }
        }
      }
    }
    """
    data = _post(query, variables={
        "pipeId": pipe_id,
        "phaseId": phase_id,
        "title": title,
        "fieldsAttributes": fields_attributes
    })
    return data.get("data", {}).get("createCard", {})
