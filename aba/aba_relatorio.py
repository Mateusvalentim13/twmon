import streamlit as st
import pandas as pd
from fpdf import FPDF
import numpy as np
import base64
import tempfile
from datetime import datetime
from utils.encoded_image import encoded_image

@st.cache_data
def carregar_logo_tempfile():
    logo_data = base64.b64decode(encoded_image)
    temp_logo = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    temp_logo.write(logo_data)
    temp_logo.close()
    return temp_logo.name

def map_titulo_para_chave(titulo):
    return {
        "Falhas de Comunicacao": "falhas_processadas",
        "Mudanca de Patamar": "patamares_processados",
        "Disponibilidade": "disponibilidade_processada",
        "Status da Bateria": "bateria_processada",
        "Dados Congelados": "congelamentos_processados",
        "Continuidade Temporal": "continuidade_processada",
        "Qualidade do Sinal": "sinal_processado"
    }.get(titulo)

def contar_registros(dados, titulo):
    if dados is None:
        return 0
    if isinstance(dados, tuple):
        if titulo == "Status da Bateria":
            return int(sum(dados[0]["Leituras < 3.3V"] > 0))
        if titulo == "Disponibilidade":
            return len(dados[1])
    elif isinstance(dados, pd.DataFrame):
        return len(dados)
    return 0

def incluir_secao_falhas_tabela(pdf, titulo, nome_arquivo):
    try:
        pdf.set_font("Arial", 'B', 12)
        pdf.set_text_color(0)
        pdf.cell(0, 8, f"- {titulo}", ln=True)
        pdf.set_font("Arial", '', 10)

        chave = map_titulo_para_chave(titulo)
        dados = st.session_state.get(chave, {}).get(nome_arquivo)

        if dados is None or (isinstance(dados, pd.DataFrame) and dados.empty):
            pdf.cell(0, 6, "OK: Nenhuma falha detectada para este tipo.", ln=True)
            pdf.ln(2)
            return

        linhas = min(10, len(dados))

        if isinstance(dados, tuple) and titulo == "Status da Bateria":
            dados = dados[0]

        if isinstance(dados, tuple) and titulo == "Disponibilidade":
            geral, por_instr = dados
            pdf.cell(0, 6, f"Disponibilidade geral: {geral:.2f}%", ln=True)
            for inst, val in por_instr.items():
                pdf.cell(0, 6, f"- {inst}: {val:.2f}%", ln=True)
        elif isinstance(dados, pd.DataFrame):
            colunas = list(dados.columns[:3])
            header = " | ".join([str(c) for c in colunas])
            pdf.set_font("Arial", 'B', 10)
            pdf.multi_cell(0, 6, header)
            pdf.set_font("Arial", '', 10)
            for i in range(linhas):
                linha = dados.iloc[i]
                valores = " | ".join([str(linha[c]) for c in colunas])
                pdf.multi_cell(0, 6, valores)
            if len(dados) > linhas:
                pdf.cell(0, 6, f"... e mais {len(dados) - linhas} registros.", ln=True)

        pdf.ln(2)

    except Exception as e:
        pdf.set_font("Arial", '', 11)
        pdf.multi_cell(0, 6, f"ATENCAO: Erro ao gerar secao: {str(e)}")
        pdf.ln(2)

def exibir_relatorio_falhas(dfs_por_arquivo):
    st.subheader("Relatorio de Falhas por Arquivo")

    if not dfs_por_arquivo:
        st.info("Nenhum arquivo carregado.")
        return

    st.markdown("### Selecione os tipos de falhas a incluir no relatorio:")
    incluir_comunicacao = st.checkbox("Falhas de comunicacao", value=True)
    incluir_patamar = st.checkbox("Mudanca de patamar", value=True)
    incluir_disponibilidade = st.checkbox("Disponibilidade", value=True)
    incluir_bateria = st.checkbox("Status da bateria", value=True)
    incluir_congelamento = st.checkbox("Dados congelados", value=True)
    incluir_continuidade = st.checkbox("Continuidade temporal", value=True)
    incluir_sinal = st.checkbox("Qualidade do sinal (RSSIB/RSSIL > 75)", value=True)

    opcoes_ativas = {
        "Falhas de Comunicacao": incluir_comunicacao,
        "Mudanca de Patamar": incluir_patamar,
        "Disponibilidade": incluir_disponibilidade,
        "Status da Bateria": incluir_bateria,
        "Dados Congelados": incluir_congelamento,
        "Continuidade Temporal": incluir_continuidade,
        "Qualidade do Sinal": incluir_sinal
    }

    if st.button("Gerar Relatorio em PDF"):
        with st.spinner("Gerando o PDF, por favor aguarde..."):
            try:
                logo_path = carregar_logo_tempfile()
                pdf = FPDF()
                pdf.set_auto_page_break(auto=True, margin=15)

                # SUMÁRIO
                pdf.add_page()
                pdf.image(logo_path, x=10, y=10, w=50)
                pdf.ln(25)
                pdf.set_font("Arial", 'B', 16)
                pdf.set_fill_color(30, 144, 255)
                pdf.set_text_color(255)
                pdf.cell(0, 10, "Resumo do Relatorio", ln=True, fill=True)
                pdf.set_text_color(0)
                pdf.set_font("Arial", '', 11)

                for nome_arquivo in dfs_por_arquivo:
                    pdf.ln(4)
                    pdf.set_font("Arial", 'B', 12)
                    pdf.cell(0, 8, f"{nome_arquivo}", ln=True)
                    pdf.set_font("Arial", '', 11)
                    falhas_encontradas = False
                    for titulo, ativo in opcoes_ativas.items():
                        if not ativo:
                            continue
                        chave = map_titulo_para_chave(titulo)
                        dados = st.session_state.get(chave, {}).get(nome_arquivo)
                        if titulo == "Disponibilidade" and isinstance(dados, tuple):
                            geral, _ = dados
                            pdf.cell(0, 6, f"- {titulo}: {geral:.2f}%", ln=True)
                            falhas_encontradas = True
                        else:
                            count = contar_registros(dados, titulo)
                            if count > 0:
                                pdf.cell(0, 6, f"- {titulo}: {count}", ln=True)
                                falhas_encontradas = True
                    if not falhas_encontradas:
                        pdf.cell(0, 6, "- Nenhuma falha detectada", ln=True)

                # RELATÓRIO DETALHADO
                for nome_arquivo in dfs_por_arquivo:
                    pdf.add_page()
                    pdf.image(logo_path, x=10, y=10, w=50)
                    pdf.ln(25)
                    pdf.set_fill_color(30, 144, 255)
                    pdf.set_text_color(255)
                    pdf.set_font("Arial", 'B', 16)
                    pdf.cell(0, 10, "GeoWise - Relatorio de Falhas", ln=True, fill=True)
                    pdf.set_text_color(0)
                    pdf.set_font("Arial", 'B', 12)
                    pdf.cell(0, 10, f"Arquivo: {nome_arquivo}", ln=True)
                    pdf.ln(2)
                    for titulo, ativo in opcoes_ativas.items():
                        if ativo:
                            incluir_secao_falhas_tabela(pdf, titulo, nome_arquivo)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    pdf.output(tmp.name)
                    tmp.flush()
                    with open(tmp.name, "rb") as f:
                        pdf_bytes = f.read()

                st.download_button(
                    label="Baixar Relatorio em PDF",
                    data=pdf_bytes,
                    file_name="relatorio_geowise.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Erro ao gerar o PDF: {e}")
