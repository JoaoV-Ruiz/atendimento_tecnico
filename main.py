import streamlit as st
import pytz
from datetime import datetime, timedelta

# --- 1. CONFIGURAÇÃO DA PÁGINA (DEVE SER A PRIMEIRA COISA) ---
st.set_page_config(page_title="Sistema Atendimento Técnico", layout="wide", page_icon="📊")

# --- 2. IMPORTAÇÃO DE ESTILOS ---
from styles import apply_styles

# --- 3. INICIALIZAÇÃO DE SEGURANÇA (BOOT) ---
def formatador_codigo_rapido():
    """Gera o código especial pegando os últimos 8 dígitos e inserindo o prefixo."""
    with st.popover("🔑 Gerador de ZTE"):
        st.markdown("**Transformador de Serial**")
        texto_input = st.text_input("Insira o Serial original:", placeholder="ex: ZTE3B8TR8J17025", key="in_codigo")
        
        if texto_input:
            # Remove espaços em branco acidentais do início/fim
            texto_limpo = texto_input.strip()
            
            if len(texto_limpo) >= 8:
                ultimos_oito = texto_limpo[-8:].lower()
                resultado = f"051R@{ultimos_oito}"
                
                st.caption("Resultado (clique no ícone para copiar):")
                # O st.code já cria uma caixinha com botão de cópia nativo!
                st.code(resultado, language="text")
            else:
                st.warning("⚠️ O texto inserido tem menos de 8 caracteres.")
                
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

# --- 4. IMPORTAÇÃO DOS MÓDULOS (BLINDADA) ---
# Importamos um a um para que se um der erro, o sistema não morra
try:
    from modules import amarelos, batida_caixa, encerramentos, portabilidade, performance, scripts_rb
except Exception as e:
    st.warning(f"Aviso: Alguns módulos estão sendo carregados... (Erro: {e})")

fuso_br = pytz.timezone('America/Sao_Paulo')
agora = datetime.now(fuso_br)

# --- 5. GATILHO AUTOMÁTICO ---
HORA_ALVO = 22
MIN_ALVO = 15

if agora.hour == HORA_ALVO and agora.minute == MIN_ALVO:
    if st.session_state.dia_disparo != agora.day:
        st.session_state.dia_disparo = agora.day
        with st.status("🤖 Enviando relatório diário...") as status:
            try:
                sucesso = amarelos.realizar_coleta_e_envio_automatizado()
                if sucesso:
                    status.update(label="✅ Enviado com sucesso!", state="complete")
                else:
                    st.session_state.dia_disparo = 0
                    status.update(label="❌ Erro no envio.", state="error")
            except:
                status.update(label="❌ Módulo Amarelos indisponível.", state="error")

# --- 6. INTERFACE ---
st.sidebar.title("🚀 Menu Principal")
escolha = st.sidebar.radio(
    "Selecione a ferramenta:", 
    ["📑 Resumo Encerramento", "🟡 Resumo Amarelos", "📲 Portabilidade", "💰 Batida de Caixa", "📈 Performance TME", "💻Scripts Para RB's"]
)

with st.sidebar:
        st.divider()
        formatador_codigo_rapido() 
        st.divider()

# Renderização segura
try:
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
    elif escolha == "💻Scripts Para RB's":
        scripts_rb.render()
except NameError:
    st.error("O módulo selecionado não foi carregado corretamente. Verifique o arquivo na pasta 'modules'.")
