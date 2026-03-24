import streamlit as st
import pytz
from datetime import datetime, timedelta
from styles import apply_styles

try:
    from modules import amarelos
except Exception as e:
    st.error(f"Erro ao carregar módulo Amarelos: {e}")

try:
    from modules import batida_caixa
except Exception as e:
    st.error(f"Erro ao carregar módulo Batida de Caixa: {e}")

try:
    from modules import encerramentos
except Exception as e:
    st.error(f"Erro ao carregar módulo Encerramentos: {e}")

try:
    from modules import portabilidade
except Exception as e:
    st.error(f"Erro ao carregar módulo Portabilidade: {e}")

try:
    from modules import performance
except Exception as e:
    st.error(f"Erro ao carregar módulo Performance: {e}")

try:
    from modules import demandas
except Exception as e:
    st.error(f"Erro ao carregar módulo Demandas: {e}")

try:
    from modules import escrita
except Exception as e:
    st.error(f"Erro ao carregar módulo Escrita: {e}")

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
HORA_ALVO = 23
MIN_ALVO = 45 # Ajuste para o horário que desejar

if agora.hour == HORA_ALVO and agora.minute == MIN_ALVO:
    # Só entra se o dia de hoje for diferente do último disparo registrado nesta sessão
    if st.session_state.dia_disparo != agora.day:
        
        # MARCA COMO FEITO IMEDIATAMENTE (antes de rodar a função pesada)
        st.session_state.dia_disparo = agora.day
        
        print(f"🚀 Disparo único iniciado: {agora.strftime('%H:%M:%S')}")
        
        with st.status("🤖 Enviando relatório diário...") as status:
            sucesso = amarelos.realizar_coleta_e_envio_automatizado()
            
            if sucesso:
                status.update(label="✅ Enviado com sucesso!", state="complete")
            else:
                # Se der erro real no Selenium, resetamos a trava para tentar no próximo refresh
                st.session_state.dia_disparo = 0
                status.update(label="❌ Erro no envio. Tentando novamente...", state="error")
                
# --- 4. INTERFACE ---
st.sidebar.title("🚀 Menu Principal")
escolha = st.sidebar.radio(
    "Selecione a ferramenta:", 
    ["📑 Resumo Encerramento", "🟡 Resumo Amarelos", "📲 Portabilidade", "💰 Batida de Caixa", "📈 Performance TME", "🚧 Demanda Infra", "🎙️ BOT para escrita"]
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
elif escolha == "🚧 Demanda Infra":
    demandas.render()
elif escolha == "🎙️ BOT para escrita":
    escrita.render()
