import streamlit as st
import pytz
from datetime import datetime
from modules import amarelos, batida_caixa, encerramentos, portabilidade
from styles import apply_styles

st.set_page_config(page_title="Sistema Atendimento Técnico", layout="wide", page_icon="📊")
apply_styles()

fuso_br = pytz.timezone('America/Sao_Paulo')
agora = datetime.now(fuso_br)

# --- GATILHO AUTOMÁTICO (PROTEÇÃO CONTRA DUPLICIDADE) ---
if agora.hour == 19 and agora.minute == 19:
    if "dia_disparo" not in st.session_state or st.session_state["dia_disparo"] != agora.day:
        # Marcamos o dia IMEDIATAMENTE para bloquear outros refreshes
        st.session_state["dia_disparo"] = agora.day
        
        with st.status("🤖 Enviando relatório diário..."):
            sucesso = amarelos.realizar_coleta_e_envio_automatizado()
            if sucesso:
                st.toast("🚀 Relatório enviado com sucesso!", icon="✅")
            else:
                # Se falhou, resetamos a trava para o próximo refresh tentar de novo
                st.session_state["dia_disparo"] = 0
                st.error("Erro no envio do relatório.")

# --- MENU LATERAL E NAVEGAÇÃO ---
st.sidebar.title("🚀 Menu Principal")
escolha = st.sidebar.radio("Selecione:", ["📑 Resumo Encerramento", "🟡 Resumo Amarelos", "📲 Portabilidade", "💰 Batida de Caixa"])

if escolha == "📑 Resumo Encerramento": encerramentos.render()
elif escolha == "🟡 Resumo Amarelos": amarelos.render()
elif escolha == "📲 Portabilidade": portabilidade.render()
elif escolha == "💰 Batida de Caixa": batida_caixa.render()
