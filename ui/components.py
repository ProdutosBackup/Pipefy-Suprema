import streamlit as st

def render_inbox(cards):
    if not cards:
        st.info("Nenhum card na caixa de entrada.")
        return

    CAMPOS_PRINCIPAIS = [
        "Nome do clube/Nombre del club/Club name",
        "Tipo do evento/ Tipo del evento/ Game type",
        "DATA E HORA/DATE AND TIME",
        "PROTOCOLO"
    ]

    for card in cards:
        node = card.get("node", {})
        title = node.get("title", "Sem título")
        fields = node.get("fields", [])

        principais = []
        secundarios = []

        for f in fields:
            if not f.get("value"):
                continue
            if f.get("name") in CAMPOS_PRINCIPAIS:
                principais.append(f)
            else:
                secundarios.append(f)

        with st.container(border=True):
            st.markdown(f"### 📋 {title}")

            if principais:
                colunas = st.columns(len(principais))
                for i, f in enumerate(principais):
                    with colunas[i]:
                        label_limpo = f.get('name', '').split('/')[0].strip()
                        st.markdown(f"**{label_limpo}**")
                        st.write(f.get('value', ''))

            if secundarios:
                st.write("")
                with st.expander("Ver detalhes completos do evento"):
                    for f in secundarios:
                        st.markdown(f"**{f.get('name', '')}:** {f.get('value', '')}")
