import streamlit as st
import pytz
from datetime import datetime, timedelta
from modules import amarelos, batida_caixa, encerramentos, portabilidade
from styles import apply_styles

# 1. Configuração da Página
st.set_page_config(page_title="Sistema Atendimento Técnico", layout="wide", page_icon="📊")

# 2. Inicialização de Segurança (Boot)
def boot_session_state():
    if 'batida_version' not in st.session_state: st.session_state.batida_version = 0
    if 'batida_proto' not in st.session_state: st.session_state.batida_proto = ""
    if 'batida_tec' not in st.session_state: st.session_state.batida_tec = ""
    if 'batida_cx' not in st.session_state: st.session_state.batida_cx = ""
    if 'anot_batida' not in st.session_state: st.session_state.anot_batida = ""
    if 'portas' not in st.session_state: st.session_state.portas = []
    
    for i in range(16):
        for pref in ['e_b_', 's_b_', 'id_b_']:
            if f'{pref}{i}' not in st.session_state: st.session_state[f'{pref}{i}'] = ""
        if f'c_batida_{i}' not in st.session_state: st.session_state[f'c_batida_{i}'] = False
    
    if 'dados_cache' not in st.session_state: st.session_state.dados_cache = None
    if 'ultima_coleta' not in st.session_state: 
        st.session_state.ultima_coleta = datetime.now() - timedelta(days=1)
    if 'dia_disparo' not in st.session_state: st.session_state.dia_disparo = 0

boot_session_state()
apply_styles()

fuso_br = pytz.timezone('America/Sao_Paulo')
agora = datetime.now(fuso_br)

# 3. Gatilho Automático (23:45)
if agora.hour == 13 and agora.minute == 4:
    if st.session_state.dia_disparo != agora.day:
        st.session_state.dia_disparo = agora.day
        with st.status("🤖 Iniciando Processo de Fechamento...") as status:
            st.write("📡 Coletando dados do sistema...")
            sucesso = amarelos.realizar_coleta_e_envio_automatizado()
            if sucesso:
                status.update(label="✅ Relatório enviado!", state="complete")
                st.toast("Enviado com sucesso!")
            else:
                st.session_state.dia_disparo = 0
                status.update(label="❌ Falha no envio", state="error")

# 4. Menu Lateral
st.sidebar.title("🚀 Menu Principal")
escolha = st.sidebar.radio("Selecione:", ["📑 Resumo Encerramento", "🟡 Resumo Amarelos", "📲 Portabilidade", "💰 Batida de Caixa"])

if escolha == "📑 Resumo Encerramento": encerramentos.render()
elif escolha == "🟡 Resumo Amarelos": amarelos.render()
elif escolha == "📲 Portabilidade": portabilidade.render()
elif escolha == "💰 Batida de Caixa": batida_caixa.render()
