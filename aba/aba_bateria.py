import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def exibir(dfs_por_arquivo, chart_type):
    st.subheader("🔋 Verificação de Bateria")

    if "bateria_processada" not in st.session_state:
        st.session_state["bateria_processada"] = {
            nome: processar_bateria(df) for nome, df in dfs_por_arquivo.items()
        }

    encontrou_bateria = any(st.session_state["bateria_processada"].values())

    for nome_arquivo, resultado in st.session_state["bateria_processada"].items():
        # Evita erro se arquivo foi removido
        if nome_arquivo not in dfs_por_arquivo or resultado is None:
            continue

        df_resumo, campos_bateria = resultado
        if df_resumo.empty:
            continue

        st.markdown(f"### 📄 Arquivo: `{nome_arquivo}`")
        styled = df_resumo.style.map(
            lambda v: "background-color: red; color: white;" if v > 0 else "", subset=["Leituras < 3.3V"]
        ).map(
            lambda v: "background-color: orange; color: black;" if v > 0 else "", subset=["Leituras < 3.45V"]
        )
        st.dataframe(styled, use_container_width=True)

        with st.expander("📊 Gráficos e Métricas de Bateria"):
            busca = st.text_input("🔍 Buscar instrumento de bateria:", key=f"busca_{nome_arquivo}")
            campos_filtrados = [c for c in campos_bateria if busca.lower() in c.lower()]

            for campo in campos_filtrados:
                if "timestamp" not in dfs_por_arquivo[nome_arquivo].columns:
                    st.warning(f"O campo 'timestamp' não existe em `{nome_arquivo}`.")
                    continue

                df_plot = dfs_por_arquivo[nome_arquivo][["timestamp", campo]].dropna()
                df_plot[campo] = pd.to_numeric(df_plot[campo], errors="coerce")
                df_plot = df_plot[(df_plot[campo] >= 0) & (df_plot[campo] <= 5)]
                df_plot.sort_values("timestamp", inplace=True)

                alerta = df_plot[(df_plot[campo] > 3.3) & (df_plot[campo] < 3.45)]
                critico = df_plot[df_plot[campo] <= 3.3]

                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=df_plot["timestamp"], y=df_plot[campo],
                    mode='lines', name="Tensão", line=dict(width=2)
                ))

                fig.add_trace(go.Scatter(
                    x=alerta["timestamp"], y=alerta[campo],
                    mode='markers', name="Alerta (3.3V–3.45V)",
                    marker=dict(color="orange", size=6, symbol="circle")
                ))

                fig.add_trace(go.Scatter(
                    x=critico["timestamp"], y=critico[campo],
                    mode='markers', name="Crítico (≤3.3V)",
                    marker=dict(color="red", size=8, symbol="diamond")
                ))

                fig.update_layout(
                    title=f"Tensão da Bateria – {campo}",
                    xaxis_title="Timestamp",
                    yaxis_title="Tensão (V)",
                    yaxis_range=[2.5, 5.1],
                    height=350
                )
                st.plotly_chart(fig, use_container_width=True)

    #//if not encontrou_bateria:
       #// st.info("Nenhum campo relacionado à bateria foi encontrado nos arquivos.")


@st.cache_data
def processar_bateria(df):
    # Palavras-chave ampliadas
    palavras_chave = ['battery', 'batt', '_batteryvoltage']
    campos_bateria = [
        c for c in df.columns
        if any(palavra in c.lower() for palavra in palavras_chave)
    ]

    #//if not campos_bateria:
        #//st.warning("⚠️ Nenhum campo de bateria encontrado. Colunas disponíveis:")
       #// st.write(df.columns.tolist())
        #//return None

    resumo = []

    for campo in campos_bateria:
        df[campo] = pd.to_numeric(df[campo], errors='coerce')
        df_validos = df[(df[campo] >= 0) & (df[campo] <= 5)]
        alerta = df_validos[(df_validos[campo] < 3.45) & (df_validos[campo] > 3.3)]
        critico = df_validos[df_validos[campo] <= 3.3]

        resumo.append({
            "Campo de Bateria": campo,
            "Leituras < 3.45V": len(alerta),
            "Leituras < 3.3V": len(critico)
        })

    df_resumo = pd.DataFrame(resumo)
    return df_resumo, campos_bateria
