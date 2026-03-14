import streamlit as st
import pytz
from datetime import datetime
from modules import amarelos, batida_caixa, encerramentos, portabilidade
from styles import apply_styles

# 1. Configuração da Página
st.set_page_config(page_title="Sistema Atendimento Técnico", layout="wide", page_icon="📊")

# 2. Aplicar Estilos
apply_styles()

# 3. Fuso Horário e Gatilho (Independente da aba selecionada)
fuso_br = pytz.timezone('America/Sao_Paulo')
agora = datetime.now(fuso_br)

# Verifica o envio das 23:45
if agora.hour == 23 and agora.minute == 45:
    if "dia_ultimo_disparo" not in st.session_state or st.session_state["dia_ultimo_disparo"] != agora.day:
        # Roda em segundo plano sem travar a UI
        sucesso = amarelos.realizar_coleta_e_envio_automatizado()
        if sucesso:
            st.session_state["dia_ultimo_disparo"] = agora.day

# 4. MENU LATERAL (Sidebar)
st.sidebar.title("🚀 Menu Principal")
paginas = [
    "📑 Resumo Encerramento", 
    "🟡 Resumo Amarelos", 
    "📲 Portabilidade", 
    "💰 Batida de Caixa"
]
escolha = st.sidebar.radio("Selecione a ferramenta:", paginas)

st.sidebar.divider()
st.sidebar.write(f"🕒 **Brasília:** {agora.strftime('%H:%M:%S')}")

# 5. CARREGAMENTO CONDICIONAL (Só carrega o que você clicar)
if escolha == "📑 Resumo Encerramento":
    encerramentos.render()

elif escolha == "🟡 Resumo Amarelos":
    amarelos.render()

elif escolha == "📲 Portabilidade":
    portabilidade.render()

elif escolha == "💰 Batida de Caixa":
    batida_caixa.render()
