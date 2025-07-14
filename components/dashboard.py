import streamlit as st
from streamlit_extras.metric_cards import style_metric_cards

def painel_resumo():
    falhas = "-"
    disponibilidade = "-"
    sensores = "-"

    # Falhas
    if "falhas_processadas" in st.session_state:
        falhas = str(len(st.session_state["falhas_processadas"]))

    # Disponibilidade
    if "disponibilidade_processada" in st.session_state:
        df = st.session_state["disponibilidade_processada"]
        if not df.empty and "Disponibilidade" in df.columns:
            media = df["Disponibilidade"].mean() * 100
            disponibilidade = f"{media:.1f}%"

    # Sensores analisados
    if "dados_processados" in st.session_state:
        df = st.session_state["dados_processados"]
        if not df.empty and "TAG" in df.columns:
            sensores = str(df["TAG"].nunique())

    # Renderização
    st.markdown("### 📊 Visão Geral")
    col1, col2, col3 = st.columns(3)
    col1.metric("Falhas detectadas", falhas)
    col2.metric("Disponibilidade", disponibilidade)
    col3.metric("Sensores analisados", sensores)

    style_metric_cards(
        background_color="#1e1e1e",
        border_color="#333333",
        border_left_color="#00BFFF"
    )
