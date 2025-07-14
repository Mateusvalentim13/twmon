import streamlit as st
import streamlit.components.v1 as components
from datetime import time
import pandas as pd
import base64
import re

from aba import (
    aba_arquivos,
    aba_bateria,
    aba_congelamento,
    aba_continuidade,
    aba_mudanca_de_patamar,
    aba_falhas,
    aba_disponibilidade,
    aba_relatorio,
    aba_qualidade_sinal
)
from utils.auth import tela_login
from utils.encoded_image import encoded_image
from utils.kalunga import get_kalunga_base64
from components.monitoramento import gerar_html_monitoramento

st.set_page_config(page_title="TWmon - Health Check", layout="wide")
pd.set_option("styler.render.max_elements", 2_000_000)

if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "ultima_contagem_falhas" not in st.session_state:
    st.session_state["ultima_contagem_falhas"] = 0

if not st.session_state["logado"]:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tela_login()
    st.stop()

st.image(base64.b64decode(encoded_image), width=400)

# Escolha da tela
st.sidebar.title("TWmon - Health Check")
tela = st.sidebar.radio("Escolha a tela:", ["Tela de diagnóstico", "Tela de monitoramento"])

# Upload de arquivos
uploaded_files = st.sidebar.file_uploader(
    "Selecione os arquivos .DAT",
    type=["dat", "csv"],
    accept_multiple_files=True,
    key="uploader_arquivos"
)

# Detecta e atualiza arquivos carregados
if uploaded_files:
    arquivos_novos = [f.name for f in uploaded_files]
    arquivos_anteriores = st.session_state.get("nomes_arquivos_carregados", [])

    if set(arquivos_novos) != set(arquivos_anteriores):

        for chave in [
            "dados_processados",
            "falhas_processadas",
            "congelamentos_processados",
            "disponibilidade_processada",
            "patamares_processados",
            "bateria_processada"
        ]:
            st.session_state.pop(chave, None)
        st.session_state["arquivos_enviados"] = uploaded_files
        st.session_state["nomes_arquivos_carregados"] = arquivos_novos

arquivos_enviados = st.session_state.get("arquivos_enviados", [])

if arquivos_enviados:
    st.sidebar.write("Arquivos carregados:")
    for f in arquivos_enviados:
        st.sidebar.markdown(f"- {f.name}")

if tela == "Tela de diagnóstico":
    dfs_por_arquivo = {}
    chart_type = "Linha"
    hora_inicio = time(0, 0)
    hora_fim = time(23, 59)
    limiar_variacao = 0.05
    data_inicio = data_fim = None

    abas = st.tabs([
        "📁 Arquivos",
        "🔴 Falhas de comunicação",
        "📈 Mudança de patamar",
        "✅ Disponibilidade",
        "🔋 Status das Baterias",
        "❄️ Dados Congelados",
        "⏰ Continuidade Temporal",
        "📶 Qualidade do Sinal",
        "📄 Relatórios"
    ])

    with abas[0]:
        if arquivos_enviados:
            nomes_arquivos = [arquivo.name for arquivo in arquivos_enviados]
            st.subheader("Arquivos Carregados:")
            st.write(nomes_arquivos)

            if (
                "falhas_processadas" in st.session_state
                and "disponibilidade_processada" in st.session_state
                and "dados_processados" in st.session_state
            ):
                from components.dashboard import painel_resumo
                painel_resumo()

            with st.sidebar.expander("⚙️ Parâmetros de Visualização", expanded=True):
                st.markdown("### 📊 Tipo de Gráfico")
                chart_type = st.radio(
                    "Visualização para bateria:",
                    ["Linha"], index=0,
                    key="tipo_grafico_aba_arquivos"
                )

                st.markdown("---")
                st.markdown("### 🕒 Intervalo de Horário")
                hora_inicio = st.time_input("Hora de início", value=time(0, 0))
                hora_fim = st.time_input("Hora de fim", value=time(23, 59))

                st.markdown("---")
                st.markdown("### 📉 Limiar de Variação")
                limiar_variacao = st.number_input("Variação (%)", min_value=0.0, value=5.0, step=0.1) / 100

            dfs_por_arquivo = aba_arquivos.exibir(
                arquivos_enviados, hora_inicio, hora_fim, limiar_variacao
            )

            for nome_arquivo, df in dfs_por_arquivo.items():
                if not df.empty and "timestamp" in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                    df.dropna(subset=['timestamp'], inplace=True)

            todos_ts = pd.concat([
                df['timestamp'] for df in dfs_por_arquivo.values()
                if 'timestamp' in df.columns and not df['timestamp'].isnull().all()
            ])
            data_min = todos_ts.min().date()
            data_max = todos_ts.max().date()

            with st.sidebar.expander("🗅️ Intervalo de Datas", expanded=True):
                data_inicio = st.date_input("Data de início", value=data_min, min_value=data_min, max_value=data_max)
                data_fim = st.date_input("Data de fim", value=data_max, min_value=data_min, max_value=data_max)

            filtro_data_inicial = pd.to_datetime(f"{data_inicio} {hora_inicio}")
            filtro_data_final = pd.to_datetime(f"{data_fim} {hora_fim}")

            for nome_arquivo in dfs_por_arquivo:
                if 'timestamp' in dfs_por_arquivo[nome_arquivo].columns:
                    df = dfs_por_arquivo[nome_arquivo]
                    df = df[(df['timestamp'] >= filtro_data_inicial) & (df['timestamp'] <= filtro_data_final)]
                    dfs_por_arquivo[nome_arquivo] = df

            if dfs_por_arquivo:
                st.session_state["dados_processados"] = dfs_por_arquivo

        else:
            st.info("Nenhum arquivo carregado ainda.")
            st.markdown("---")
            st.markdown("👈 Use a barra lateral para carregar arquivos .DAT ou .CSV")

    if dfs_por_arquivo:
        with abas[1]:
            aba_falhas.exibir(dfs_por_arquivo, limiar_variacao)
        with abas[2]:
            aba_mudanca_de_patamar.exibir(dfs_por_arquivo, limiar_variacao)
        with abas[3]:
            aba_disponibilidade.exibir(dfs_por_arquivo, limiar_variacao)
        with abas[4]:
            aba_bateria.exibir(dfs_por_arquivo, chart_type)
        with abas[5]:
            aba_congelamento.exibir(dfs_por_arquivo)
        with abas[6]:
            aba_continuidade.exibir(dfs_por_arquivo)
        with abas[7]:
            aba_qualidade_sinal.exibir(dfs_por_arquivo)
        with abas[8]:
            aba_relatorio.exibir_relatorio_falhas(dfs_por_arquivo)

elif tela == "Tela de monitoramento":
    st.markdown("### 📱 Tela de Monitoramento")

    if "dados_processados" in st.session_state:
        tags_unicas = list({
            re.match(r"^([A-Za-z0-9]+)", col).group(1)
            for df in st.session_state["dados_processados"].values()
            for col in df.columns if re.match(r"^([A-Za-z0-9]+)", col)
        })

        tags_filtradas = st.sidebar.multiselect(
            "Filtrar por TAG (instrumento):",
            sorted(tags_unicas),
            default=tags_unicas
        )

        html_monitoramento = gerar_html_monitoramento(
            st.session_state["dados_processados"],
            get_kalunga_base64(),
            st.session_state.get("falhas_processadas"),
            tags_desejadas=tags_filtradas
        )
        components.html(html_monitoramento, height=850, scrolling=False)


st.markdown("""
    <style>
        #MainMenu {visibility:hidden;}
        footer {visibility:hidden;}
        header {visibility:hidden;}
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
        #custom-footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: #0E1117;
            color: white;
            text-align: center;
            padding: 10px;
            font-size: 13px;
            z-index: 100;
        }
    </style>
    <div id="custom-footer">
        © 2025 TECWISE LATAM — Todos os direitos reservados.
    </div>
""", unsafe_allow_html=True)
