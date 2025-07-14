
from typing import Dict, List
import pandas as pd
import re
from random import randint

def gerar_html_monitoramento(dados_processados: Dict[str, pd.DataFrame], img_base64: str, falhas_df=None, tags_desejadas: List[str] = None) -> str:
    cont_falhas = 0
    coordenadas_sensores = {}
    falhas_reais = set()
    sensores_agrupados = {}
    popup_dict = {}
    cor_dict = {}

    if falhas_df is not None and not falhas_df.empty:
        for col in falhas_df.columns:
            sensores_com_falha = falhas_df[col].dropna().astype(str).str.extract(r"([A-Za-z0-9_-]+)")[0].dropna().unique()
            falhas_reais.update(sensores_com_falha)

    for nome_arquivo, df in dados_processados.items():
        if "timestamp" not in df.columns.str.lower():
            continue

        col_ts = next((c for c in df.columns if c.lower() == "timestamp"), None)
        if col_ts is None:
            continue

        df[col_ts] = pd.to_datetime(df[col_ts], errors="coerce")
        df.dropna(subset=[col_ts], inplace=True)

        for col in df.columns:
            if col == col_ts:
                continue

            match = re.match(r"^([A-Za-z0-9]+)", col)
            if not match:
                continue

            prefixo = match.group(1)
            if tags_desejadas and prefixo not in tags_desejadas:
                continue

            if prefixo not in sensores_agrupados:
                sensores_agrupados[prefixo] = {
                    "campos": {},
                    "timestamp": df[col_ts].iloc[-1] if not df.empty else "N/A"
                }

            ultima = df[col].dropna().iloc[-1] if not df[col].dropna().empty else "N/A"
            sensores_agrupados[prefixo]["campos"][col] = ultima

    for sensor_prefixo, dados in sensores_agrupados.items():
        if sensor_prefixo not in coordenadas_sensores:
            coordenadas_sensores[sensor_prefixo] = {
                "top": f"{randint(15, 75)}%",
                "left": f"{randint(10, 85)}%"
            }

        campos = dados["campos"]
        timestamp = dados["timestamp"]
        congelado = "Sim" if sum(pd.Series(list(campos.values())).nunique() < 3 for _ in campos) else "Não"

        tem_falha_real = sensor_prefixo in falhas_reais
        cor = "red" if tem_falha_real else "green"
        if tem_falha_real:
            cont_falhas += 1

        digit = next((v for k, v in campos.items() if "DIGIT" in k.upper()), "N/A")
        temp = next((v for k, v in campos.items() if "TEMP" in k.upper()), "N/A")
        bateria = next((v for k, v in campos.items() if "BATTERY" in k.upper()), "N/A")
        sinal = next((v for k, v in campos.items() if "RSSI" in k.upper()), "N/A")

        popup = (
            f"<strong>{sensor_prefixo}</strong><br>"
            f"Última Leitura - DIGIT: {digit}<br>"
            f"Última Leitura - TEMP: {temp}<br>"
            f"Mudança de patamar: {'Sim' if 'patamar' in campos else 'Não'}<br>"
            f"Disponibilidade: {'100%' if not tem_falha_real else '0%'}<br>"
            f"Bateria: {bateria}<br>"
            f"Dados congelados: {congelado}<br>"
            f"Nível de sinal: {sinal}<br>"
            f"Timestamp: {timestamp}"
        )

        popup_dict[sensor_prefixo] = popup
        cor_dict[sensor_prefixo] = cor

    html_base = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                margin: 0;
                overflow: hidden;
                font-family: Arial, sans-serif;
                background-color: #0e1117;
            }}
            .image-container {{
                position: relative;
                width: 100%;
                height: 100vh;
                overflow: hidden;
            }}
            .image-container img {{
                width: 100%;
                height: 100%;
                object-fit: cover;
                display: block;
            }}
            .sensor-wrapper {{
                position: absolute;
                transform: translate(-50%, -50%);
                z-index: 10;
                cursor: pointer;
            }}
            .marker {{
                width: 16px;
                height: 16px;
                border-radius: 50%;
                border: 2px solid black;
            }}
            .popup {{
                display: none;
                position: absolute;
                background-color: white;
                color: black;
                padding: 8px;
                border-radius: 4px;
                white-space: nowrap;
                z-index: 99999;
                box-shadow: 0 2px 10px rgba(0,0,0,0.4);
            }}
        </style>
    </head>
    <body>
        
        <div class="image-container">
            <img src="data:image/jpeg;base64,{img_base64}" />
            {"".join([
                f'''
                <div id="marker_{tag}" class="sensor-wrapper" style="top: {coordenadas_sensores[tag]['top']}; left: {coordenadas_sensores[tag]['left']};" onclick="togglePopup('{tag}')">
                    <div class="marker" style="background-color: {cor_dict[tag]};"></div>
                </div>
                <div id="popup_{tag}" class="popup">{popup_dict[tag]}</div>
                '''
                for tag in sensores_agrupados
            ])}
        </div>
        <script>
            function togglePopup(tag) {{
                document.querySelectorAll('.popup').forEach(p => p.style.display = 'none');
                const popup = document.getElementById("popup_" + tag);
                const marker = document.getElementById("marker_" + tag);
                const rect = marker.getBoundingClientRect();
                popup.style.top = (rect.top - popup.offsetHeight - 10) + "px";
                popup.style.left = (rect.left + 20) + "px";
                popup.style.display = "block";
            }}

            document.addEventListener("click", function(event) {{
                if (!event.target.closest('.sensor-wrapper')) {{
                    document.querySelectorAll('.popup').forEach(p => p.style.display = 'none');
                }}
            }});
        </script>
    </body>
    </html>
    """

    return html_base
