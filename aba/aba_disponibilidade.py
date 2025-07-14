import streamlit as st
import pandas as pd
import numpy as np

def exibir(dfs_por_arquivo, limiar_variacao):
    st.subheader("✅ Disponibilidade dos Instrumentos")

    if "disponibilidade_processada" not in st.session_state:
        st.session_state["disponibilidade_processada"] = {
            nome: calcular_disponibilidade(df, nome)
            for nome, df in dfs_por_arquivo.items()
        }

    resultados = st.session_state["disponibilidade_processada"]

    for nome_arquivo, resultado in resultados.items():
        if resultado is None:
            continue

        disponibilidade_geral, por_instr = resultado
        if disponibilidade_geral is None or por_instr is None:
            continue

        total_leituras = len(dfs_por_arquivo[nome_arquivo]) * len(por_instr)
        falhas = sum((100 - v) / 100 * len(dfs_por_arquivo[nome_arquivo]) for v in por_instr.values())

        st.markdown(f"### 📄 Arquivo: `{nome_arquivo}`")
        st.table(pd.DataFrame({
            "Total Leituras": [total_leituras],
            "Falhas": [int(falhas)],
            "Disponibilidade": [f"{disponibilidade_geral:.2f}%"]
        }))

        with st.expander(f"📊 Detalhamento por Instrumento - `{nome_arquivo}`"):
            ordem = st.selectbox("Ordenar por:", ["Maior porcentagem", "Menor porcentagem"], key=f"ordem_{nome_arquivo}")
            filtro_busca = st.text_input("🔍 Buscar instrumento:", key=f"filtro_{nome_arquivo}")

            df_indisp = pd.DataFrame(por_instr.items(), columns=["Instrumento", "Disponibilidade (%)"])
            if filtro_busca:
                df_indisp = df_indisp[df_indisp["Instrumento"].str.contains(filtro_busca, case=False)]

            df_indisp.sort_values("Disponibilidade (%)", ascending=(ordem == "Menor porcentagem"), inplace=True)
            st.dataframe(df_indisp, use_container_width=True)

@st.cache_data
def calcular_disponibilidade(df, nome_arquivo):
    col_digitais = [col for col in df.columns if col.lower().endswith(('_digit', '_hz', '_mm', '_kpa'))]
    if not col_digitais:
        return None

    df_local = df.copy()
    df_local[col_digitais] = df_local[col_digitais].apply(pd.to_numeric, errors='coerce')
    df_local.replace([-999, -998], np.nan, inplace=True)

    total_linhas = len(df_local)
    if total_linhas == 0 or len(col_digitais) == 0:
        return None

    total_lacunas = df_local[col_digitais].isna().sum().sum()
    disponibilidade_geral = 100 * (1 - (total_lacunas / (total_linhas * len(col_digitais))))

    disponibilidade_por_instr = {
        col: 100 * (1 - df_local[col].isna().sum() / total_linhas)
        for col in col_digitais
    }

    return disponibilidade_geral, disponibilidade_por_instr
