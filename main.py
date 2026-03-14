import streamlit as st
import pytz
from datetime import datetime
from modules import amarelos, batida_caixa, encerramentos, portabilidade
from styles import apply_styles

# 1. Configuração da Página
st.set_page_config(page_title="Sistema Atendimento Técnico", layout="wide", page_icon="📊")

# 2. Aplicar Estilos Globais
apply_styles()

# 3. Gerenciamento de Fuso Horário
fuso_br = pytz.timezone('America/Sao_Paulo')
agora = datetime.now(fuso_br)

# 4. GATILHO AUTOMÁTICO (23:45)
if agora.hour == 18 and agora.minute == 28:
    if "dia_ultimo_disparo" not in st.session_state or st.session_state["dia_ultimo_disparo"] != agora.day:
        with st.status("🤖 Iniciando Relatório Automático das 23:45..."):
            sucesso = amarelos.realizar_coleta_e_envio_automatizado()
            if sucesso:
                st.session_state["dia_ultimo_disparo"] = agora.day
                st.success("✅ Relatório diário processado com sucesso!")
            else:
                st.error("❌ Erro na execução automática da coleta.")

# 5. ESTRUTURA DE NAVEGAÇÃO (TABS) - ORDEM SOLICITADA
tab_encerra, tab_amarelos, tab_porta, tab_caixa = st.tabs([
    "📑 Resumo Encerramento", 
    "🟡 Resumo Amarelos", 
    "📲 Portabilidade",
    "💰 Batida de Caixa"
])

with tab_encerra:
    encerramentos.render()

with tab_amarelos:
    amarelos.render()

with tab_porta:
    portabilidade.render()

with tab_caixa:
    batida_caixa.render()
