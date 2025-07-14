import pandas as pd
import csv
from io import StringIO
import streamlit as st
import io
from utils import destacar_qtd_leituras

def exibir(arquivos, hora_inicio, hora_fim, limiar_variacao):
    if not arquivos:
        st.markdown(
            "<h4 style='padding-top: 2rem;'>Use a barra lateral para carregar os arquivos e configurar os filtros.</h4>",
            unsafe_allow_html=True
        )
        return None

    if "dados_processados" not in st.session_state:
        st.session_state["dados_processados"] = carregar_dados(arquivos)

    dfs_por_arquivo = st.session_state["dados_processados"]

    return dfs_por_arquivo

@st.cache_data(show_spinner="Carregando arquivos...")
def carregar_dados(arquivos):
    dfs_por_arquivo = {}
    for arquivo in arquivos:
        nome = arquivo.name.lower()
        if nome.endswith(".csv"):
            df = processar_csv(arquivo)
        elif nome.endswith(".dat"):
            df = processar_dat(arquivo)
        else:
            st.warning(f"Tipo de arquivo não suportado: {arquivo.name}")
            continue

        if not df.empty:
            dfs_por_arquivo[arquivo.name] = df
    return dfs_por_arquivo

@st.cache_data
def processar_csv(arquivo):
    try:
        arquivo.seek(0)
        with io.TextIOWrapper(arquivo, encoding='utf-8', errors='ignore') as f:
            linhas = f.readlines()

        nomes_colunas = linhas[1].strip().split(',')
        dados = [lin.strip() for i, lin in enumerate(linhas) if i > 2]
        dados_csv = '\n'.join([','.join(nomes_colunas)] + dados)

        df = pd.read_csv(StringIO(dados_csv))
        df.columns = df.columns.str.strip().str.lower()

        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        else:
            st.error(f"❌ Nenhuma coluna de timestamp encontrada em `{arquivo.name}`.")
            return pd.DataFrame()

        return df

    except Exception as e:
        st.error(f"Erro ao processar `{arquivo.name}`: {e}")
        return pd.DataFrame()

@st.cache_data
def processar_dat(arquivo):
    try:
        texto = arquivo.read().decode("utf-8", errors='ignore')
        f = StringIO(texto)
        linhas = list(csv.reader(f, delimiter=','))

        linha_colunas_idx = None
        possiveis_nomes = ['timestamp', 'data', 'datahora', 'tempo', 'datetime']

        for i, linha in enumerate(linhas[:20]):
            linha_normalizada = [
                c.strip().lower().replace('"', '').replace(',', '') for c in linha
            ]
            if any(p in linha_normalizada for p in possiveis_nomes):
                linha_colunas_idx = i
                break

        if linha_colunas_idx is None:
            st.error(f"❌ Cabeçalho com campo de tempo ('timestamp', 'data', etc.) não encontrado em `{arquivo.name}`.")
            return pd.DataFrame()

        colunas_raw = linhas[linha_colunas_idx]
        colunas = [c.strip().lower().replace('"', '').replace(',', '') for c in colunas_raw]

        dados = linhas[linha_colunas_idx + 1:]
        dados_validos = [linha for linha in dados if len(linha) == len(colunas)]

        if len(dados_validos) < len(dados):
            st.warning(f"{len(dados) - len(dados_validos)} linhas ignoradas em `{arquivo.name}` devido a inconsistências.")

        df = pd.DataFrame(dados_validos, columns=colunas)

        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

        return df

    except Exception as e:
        st.error(f"Erro ao processar `{arquivo.name}`: {e}")
        return pd.DataFrame()
