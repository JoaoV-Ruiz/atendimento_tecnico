import streamlit as st
import pytz
from datetime import datetime
from modules import amarelos, batida_caixa, encerramentos, portabilidade
from styles import apply_styles

# 1. Configuração de Página
st.set_page_config(page_title="Sistema Atendimento Técnico", layout="wide", page_icon="📊")

# 2. INICIALIZAÇÃO OBRIGATÓRIA (Bootstrap)
def boot_session_state():
    if 'batida_version' not in st.session_state: st.session_state.batida_version = 0
    if 'batida_proto' not in st.session_state: st.session_state.batida_proto = ""
    if 'batida_tec' not in st.session_state: st.session_state.batida_tec = ""
    if 'batida_cx' not in st.session_state: st.session_state.batida_cx = ""
    if 'anot_batida' not in st.session_state: st.session_state.anot_batida = ""
    if 'portas' not in st.session_state: st.session_state.portas = []
    
    # Inicializa as 16 portas para evitar o erro de chave
    for i in range(16):
        if f'e_b_{i}' not in st.session_state: st.session_state[f'e_b_{i}'] = ""
        if f's_b_{i}' not in st.session_state: st.session_state[f's_b_{i}'] = ""
        if f'id_b_{i}' not in st.session_state: st.session_state[f'id_b_{i}'] = ""
        if f'c_batida_{i}' not in st.session_state: st.session_state[f'c_batida_{i}'] = False
    
    if 'dia_disparo' not in st.session_state: st.session_state.dia_disparo = 0

boot_session_state()
apply_styles()

fuso_br = pytz.timezone('America/Sao_Paulo')
agora = datetime.now(fuso_br)

# 3. GATILHO 23:45
if agora.hour == 19 and agora.minute == 33:
    if st.session_state.dia_disparo != agora.day:
        st.session_state.dia_disparo = agora.day
        with st.status("🤖 Processando Fechamento..."):
            sucesso = amarelos.realizar_coleta_e_envio_automatizado()
            if sucesso: st.toast("Relatório enviado!", icon="🚀")
            else: st.error("Erro no envio para o Chat.")

# 4. MENU LATERAL
st.sidebar.title("🚀 Menu Principal")
escolha = st.sidebar.radio("Selecione:", ["📑 Resumo Encerramento", "🟡 Resumo Amarelos", "📲 Portabilidade", "💰 Batida de Caixa"])

if escolha == "📑 Resumo Encerramento": encerramentos.render()
elif escolha == "🟡 Resumo Amarelos": amarelos.render()
elif escolha == "📲 Portabilidade": portabilidade.render()
elif escolha == "💰 Batida de Caixa": batida_caixa.render()
