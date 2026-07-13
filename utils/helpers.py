from datetime import datetime


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
        "labels": node.get("labels", []),
    }


def sort_cards_by_date(cards_list):
    def parse_date(card):
        # Limpeza rigorosa: remove espaços normais e non-breaking spaces (\xa0)
        data_str = card.get("data_hora", "").strip().replace('\xa0', ' ')
        if not data_str:
            return datetime.min

        # 1. Tentar formato brasileiro
        try:
            return datetime.strptime(data_str, "%d/%m/%Y %H:%M")
        except ValueError:
            pass

        # 2. Tentar formato ISO
        try:
            return datetime.strptime(data_str[:10], "%Y-%m-%d")
        except ValueError:
            pass

        print(f"[DEBUG FALHA] Formato não reconhecido: {repr(data_str)}")
        return datetime.min

    return sorted(cards_list, key=parse_date, reverse=True)
