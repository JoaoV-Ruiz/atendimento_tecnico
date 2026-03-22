import streamlit as st
import pytz
from datetime import datetime, timedelta
from modules import amarelos, batida_caixa, encerramentos, portabilidade, performance
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

# --- 3. GATILHO AUTOMÁTICO ---
HORA_ALVO = 15
MIN_ALVO = 52

# Verifica se estamos no minuto exato e se ainda não disparou HOJE
if agora.hour == HORA_ALVO and agora.minute == MIN_ALVO:
    # Se o dia salvo no state for diferente do dia atual, precisa disparar
    if st.session_state.get('dia_disparo') != agora.day:
        
        print(f"🚀 Iniciando disparo automático: {agora.strftime('%H:%M:%S')}")
        
        with st.status("🤖 Processando relatório automático...") as status:
            # Importante: Garantir que a trava seja setada ANTES para evitar loops de clique
            st.session_state.dia_disparo = agora.day
            
            sucesso = amarelos.realizar_coleta_e_envio_automatizado()
            
            if sucesso:
                status.update(label="✅ Relatório enviado com sucesso!", state="complete")
                st.toast("Enviado para o Cauê!")
            else:
                # Se falhar, reseta para tentar de novo no próximo refresh do mesmo minuto
                st.session_state.dia_disparo = 0
                status.update(label="❌ Erro no envio. Tentando novamente...", state="error")

# --- 4. INTERFACE ---
st.sidebar.title("🚀 Menu Principal")
escolha = st.sidebar.radio(
    "Selecione a ferramenta:", 
    ["📑 Resumo Encerramento", "🟡 Resumo Amarelos", "📲 Portabilidade", "💰 Batida de Caixa", "📈 Performance TME"]
)

st.sidebar.divider()
st.sidebar.info(f"📅 **Hoje:** {agora.strftime('%d/%m/%Y')}\n\n🕒 **Hora:** {agora.strftime('%H:%M:%S')}")

if escolha == "📑 Resumo Encerramento":
    encerramentos.render()
elif escolha == "🟡 Resumo Amarelos":
    amarelos.render()
elif escolha == "📲 Portabilidade":
    portabilidade.render()
elif escolha == "💰 Batida de Caixa":
    batida_caixa.render()
elif escolha == "📈 Performance TME":
    performance.render()
