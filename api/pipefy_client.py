import json
import os
import re
import requests
from urllib.parse import urlparse

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
              labels { id name color }
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
            pipe { id }
            current_phase { id name }
            fields {
                name
                value
                field { id }
            }
        }
    }
    """
    data = _post(query, variables={"cardId": card_id})
    
    # Log em caso de erro na resposta GraphQL
    if "errors" in data:
        raise Exception(f"Erro GraphQL: {data['errors'][0].get('message')}")
        
    return data.get("data", {}).get("card", {})


def fetch_card_full(card_id):
    query = """
    query ($cardId: ID!) {
      card(id: $cardId) {
        id title
        current_phase {
          id
          name
          fields { id label }
        }
        pipe { id organization { id } }
        fields { name value field { id } }
      }
    }
    """
    data = _post(query, variables={"cardId": card_id})
    if "errors" in data:
        raise Exception(f"Erro GraphQL: {data['errors'][0].get('message')}")
    return data.get("data", {}).get("card", {})


def incrementar_titulo(titulo):
    import re
    match = re.search(r'\((\d+)\)$', titulo)
    if match:
        num = int(match.group(1)) + 1
        return re.sub(r'\(\d+\)$', f'({num})', titulo)
    return f"{titulo} (2)"


def clone_card(card_id):
    card = fetch_card_full(card_id)

    pipe_id = card["pipe"]["id"]
    phase_id = card["current_phase"]["id"]
    title = incrementar_titulo(card["title"])

    fields_attributes = []
    for f in card.get("fields", []):
        val = f.get("value")
        field_node = f.get("field")

        if not val or not field_node or not field_node.get("id"):
            continue

        if isinstance(val, str) and val.strip().startswith("[") and val.strip().endswith("]"):
            try:
                parsed_val = json.loads(val)
                if isinstance(parsed_val, list) and len(parsed_val) > 0 and isinstance(parsed_val[0], str) and "app.pipefy.com/storage" in parsed_val[0]:
                    continue
                val = parsed_val
            except json.JSONDecodeError:
                pass
        elif isinstance(val, str) and "app.pipefy.com/storage" in val:
            continue

        fields_attributes.append({
            "field_id": field_node["id"],
            "field_value": val
        })

    query = """
    mutation ($pipeId: ID!, $phaseId: ID!, $title: String!, $fieldsAttributes: [FieldValueInput]) {
        createCard(input: {
            pipe_id: $pipeId,
            phase_id: $phaseId,
            title: $title,
            fields_attributes: $fieldsAttributes
        }) {
            card { id title }
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
    mutation ($pipeId: ID!, $phaseId: ID!, $title: String!, $fieldsAttributes: [FieldValueInput!]!) {
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


def update_card_field(card_id, field_id, new_value):
    query = """
    mutation ($cardId: ID!, $fieldId: ID!, $newValue: [UndefinedInput]) {
      updateCardField(input: {
        card_id: $cardId,
        field_id: $fieldId,
        new_value: $newValue
      }) {
        clientMutationId
      }
    }
    """
    data = _post(query, variables={
        "cardId": card_id,
        "fieldId": field_id,
        "newValue": new_value
    })
    return data.get("data", {}).get("updateCardField", {})


def fetch_phase_fields(phase_id):
    query = """
    query ($phaseId: ID!) {
      phase(id: $phaseId) {
        fields {
          id
          label
        }
      }
    }
    """
    data = _post(query, variables={"phaseId": phase_id})
    return data.get("data", {}).get("phase", {}).get("fields", [])


def fetch_start_form_fields(pipe_id):
    query = """
    query ($pipeId: ID!) {
      pipe(id: $pipeId) {
        start_form_fields {
          id
          label
        }
      }
    }
    """
    data = _post(query, variables={"pipeId": pipe_id})
    return data.get("data", {}).get("pipe", {}).get("start_form_fields", [])


def create_card(pipe_id, phase_id, title, fields_attributes, label_ids=None):
    query = """
    mutation ($pipeId: ID!, $phaseId: ID!, $title: String!, $fieldsAttributes: [FieldValueInput!]!, $labelIds: [ID!]) {
      createCard(input: {
        pipe_id: $pipeId,
        phase_id: $phaseId,
        title: $title,
        fields_attributes: $fieldsAttributes,
        label_ids: $labelIds
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
        "fieldsAttributes": fields_attributes,
        "labelIds": label_ids
    })
    return data.get("data", {}).get("createCard", {})


def update_card_labels(card_id, label_ids):
    query = """
    mutation($cardId: ID!, $labelIds: [ID!]) {
      updateCard(input: {id: $cardId, label_ids: $labelIds}) {
        card { id }
      }
    }
    """
    data = _post(query, variables={
        "cardId": card_id,
        "labelIds": label_ids
    })
    return data.get("data", {}).get("updateCard", {})


def upload_attachment(card_id, file_obj):
    token = os.environ.get("PIPEFY_TOKEN")
    if not token:
        raise ValueError("PIPEFY_TOKEN não definido")

    file_obj.seek(0)
    files = {
        'file': (file_obj.filename, file_obj, file_obj.content_type)
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.post(
        f"https://api.pipefy.com/v1/cards/{card_id}/attachments",
        files=files,
        headers=headers
    )
    if response.status_code == 200:
        return True
    else:
        raise Exception(f"Erro no envio: {response.status_code} - {response.text}")
