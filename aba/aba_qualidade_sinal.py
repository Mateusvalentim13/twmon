import streamlit as st
import pandas as pd

def destacar_sinal(valor):
    try:
        num = float(valor)
        if num == -999:
            return ''
        if num > 75:
            return 'background-color: red; color: white;'
    except (ValueError, TypeError):
        return ''
    return ''

def exibir(dfs_por_arquivo):
    st.title("Qualidade do Sinal")
    st.write("Níveis de sinal **RSSIB** e **RSSIL**. Valores acima de 75 indicam sinal **ruim**.")

    # Sempre reprocessa os arquivos carregados
    sinal_processado = {
        nome: processar_sinal(df) for nome, df in dfs_por_arquivo.items()
    }

    for nome_arquivo, resultado in sinal_processado.items():
        st.subheader(f"📄 {nome_arquivo}")
        
        if resultado is None:
            
            continue

        df_sinal, colunas_falhas = resultado

        linhas_por_pagina = st.slider(
            f"Linhas por página - {nome_arquivo}", 10, 200, 50, step=10, key=f"slider_{nome_arquivo}"
        )
        pagina = st.number_input(
            f"Página - {nome_arquivo}", min_value=1, value=1, step=1, key=f"pagina_{nome_arquivo}"
        )
        ini = (pagina - 1) * linhas_por_pagina
        fim = ini + linhas_por_pagina

        df_exibir = df_sinal.iloc[ini:fim].fillna('')

        styled = df_exibir.style.map(
            lambda v: destacar_sinal(v),
            subset=colunas_falhas
        )
        st.dataframe(styled, use_container_width=True)

@st.cache_data
def processar_sinal(df):
    colunas_sinal = [
        col for col in df.columns
        if isinstance(col, str) and (
            col.strip().upper().strip("'\"").endswith("RSSIB") or
            col.strip().upper().strip("'\"").endswith("RSSIL")
        )
    ]

    if not colunas_sinal:
        return None

    df_sinal = df[colunas_sinal].copy()

    # Tratar valores inválidos
    df_sinal = df_sinal.applymap(lambda x: pd.NA if str(x).strip().lower() in ['none', '-999'] else x)

    # Remover colunas sem nenhuma falha
    colunas_com_falha = [
        col for col in df_sinal.columns
        if pd.to_numeric(df_sinal[col], errors='coerce').gt(75).any()
    ]

    if not colunas_com_falha:
        return None

    df_sinal = df_sinal[colunas_com_falha].copy()

    # Adicionar timestamp (se existir)
    for ts_col in ['timestamp', 'TIMESTAMP', 'TS']:
        if ts_col in df.columns:
            df_sinal.insert(0, 'timestamp', df[ts_col])
            break

    return df_sinal.reset_index(drop=True), colunas_com_falha
