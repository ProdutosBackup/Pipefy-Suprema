def transform_pipefy_card(edge):
    node = edge.get("node", {})
    fields = {f.get("name", ""): f.get("value", "") for f in node.get("fields", [])}
    return {
        "id": node.get("id"),
        "titulo": node.get("title", ""),
        "clube": fields.get("Nome do clube/Nombre del club/Club name", ""),
        "jogo": fields.get("Modalidade/Modalidad/Type:", ""),
        "data_hora": fields.get("Data e hora/Date and time", ""),
        "protocolo": f"#{node.get('id', '')}",
    }
