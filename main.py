import streamlit as st
import pytz
from datetime import datetime
from modules import amarelos, batida_caixa, encerramentos, portabilidade
from styles import apply_styles

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Sistema Atendimento Técnico", layout="wide", page_icon="📊")

# 2. INICIALIZAÇÃO DE VARIÁVEIS (BOOTSTRAP)
# Isso impede o AttributeError no Batida de Caixa e outros módulos
def inicializar_estado():
    # Variáveis do Batida de Caixa
    if 'batida_version' not in st.session_state:
        st.session_state.batida_version = 0
    if 'batida_proto' not in st.session_state:
        st.session_state.batida_proto = ""
    if 'batida_tec' not in st.session_state:
        st.session_state.batida_tec = ""
    if 'batida_cx' not in st.session_state:
        st.session_state.batida_cx = ""
    if 'anot_batida' not in st.session_state:
        st.session_state.anot_batida = ""
    if 'portas' not in st.session_state:
        st.session_state.portas = []
    
    # Inicializa as 16 linhas da tabela do Batida de Caixa
    for i in range(16):
        if f'e_b_{i}' not in st.session_state: st.session_state[f'e_b_{i}'] = ""
        if f's_b_{i}' not in st.session_state: st.session_state[f's_b_{i}'] = ""
        if f'id_b_{i}' not in st.session_state: st.session_state[f'id_b_{i}'] = ""
        if f'c_batida_{i}' not in st.session_state: st.session_state[f'c_batida_{i}'] = False

    # Variáveis de Controle do Robô (Amarelos)
    if 'dia_ultimo_disparo' not in st.session_state:
        st.session_state.dia_ultimo_disparo = 0

# Executa a inicialização
inicializar_estado()

# 3. ESTILOS E FUSO
apply_styles()
fuso_br = pytz.timezone('America/Sao_Paulo')
agora = datetime.now(fuso_br)

# 4. GATILHO AUTOMÁTICO (23:45)
if agora.hour == 19 and agora.minute == 12: # Use o seu horário de teste
    if "dia_ultimo_disparo" not in st.session_state or st.session_state["dia_ultimo_disparo"] != agora.day:
        # Marcamos como disparado ANTES para evitar que o autorefresh de 30s pegue o mesmo minuto
        st.session_state["dia_ultimo_disparo"] = agora.day 
        
        with st.status("🤖 Processando envio único..."):
            sucesso = amarelos.realizar_coleta_e_envio_automatizado()
            if sucesso:
                st.success("Relatório enviado!")
            else:
                # Se falhou, resetamos a trava para tentar no próximo refresh (opcional)
                st.session_state["dia_ultimo_disparo"] = 0 
                st.error("Falha no envio. Verifique os logs.")

# 5. MENU LATERAL
st.sidebar.title("🚀 Menu Principal")
paginas = [
    "📑 Resumo Encerramento", 
    "🟡 Resumo Amarelos", 
    "📲 Portabilidade", 
    "💰 Batida de Caixa"
]
escolha = st.sidebar.radio("Selecione a ferramenta:", paginas)

st.sidebar.divider()

# 6. NAVEGAÇÃO
if escolha == "📑 Resumo Encerramento":
    encerramentos.render()

elif escolha == "🟡 Resumo Amarelos":
    amarelos.render()

elif escolha == "📲 Portabilidade":
    portabilidade.render()

elif escolha == "💰 Batida de Caixa":
    batida_caixa.render()
