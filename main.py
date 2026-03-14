import streamlit as st
import pytz
from datetime import datetime
from modules import amarelos
from styles import apply_styles

# 1. Configuração de Estilo e Fuso
apply_styles()
fuso_br = pytz.timezone('America/Sao_Paulo')
agora = datetime.now(fuso_br)

# 2. GATILHO AUTOMÁTICO (23:45)
# Verificamos a hora e os minutos
if agora.hour == 23 and agora.minute == 45:
    # Trava de segurança para não repetir no mesmo minuto
    if "dia_disparo" not in st.session_state or st.session_state["dia_disparo"] != agora.day:
        with st.status("🤖 Iniciando Relatório Automático das 23:45..."):
            sucesso = amarelos.realizar_coleta_e_envio_automatizado()
            if sucesso:
                st.session_state["dia_disparo"] = agora.day
                st.success("✅ Relatório diário processado!")
            else:
                st.error("❌ Erro na execução automática.")

# 3. NAVEGAÇÃO / TABS
tab1, tab2, tab3 = st.tabs(["Provisionamento", "Outra Aba", "Config"])

with tab1:
    amarelos.render()
