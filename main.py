import streamlit as st
import pytz
from datetime import datetime, timedelta

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema Atendimento Técnico", layout="wide", page_icon="📊")

# --- 2. IMPORTAÇÃO DE ESTILOS ---
from styles import apply_styles

# --- 3. FUNÇÃO DE SENHA VIA SECRETS ---
def check_password():
    """Retorna True se a senha nos Secrets coincidir com a entrada."""
    def password_entered():
        # Busca a senha cadastrada nos Secrets do Streamlit
        try:
            senha_correta = st.secrets["SISTEMA_PASSWORD"]
            if st.session_state["password_input"] == senha_correta:
                st.session_state["password_correct"] = True
                del st.session_state["password_input"]
            else:
                st.session_state["password_correct"] = False
        except KeyError:
            st.error("❌ Erro: 'SISTEMA_PASSWORD' não configurado nos Secrets!")

    if "password_correct" not in st.session_state:
        # Centraliza a tela de login
        _, col_login, _ = st.columns([1, 1, 1])
        with col_login:
            st.markdown("### 🔐 Acesso Restrito")
            st.text_input(
                "Insira a senha mestra:", 
                type="password", 
                on_change=password_entered, 
                key="password_input"
            )
            if "password_correct" in st.session_state and not st.session_state["password_correct"]:
                st.error("😕 Senha incorreta.")
        return False
    return True

# --- INÍCIO DA RENDERIZAÇÃO ---
if check_password():
    apply_styles() # Aplica o Dark Mode após o login
    
    # Importação dos módulos (dentro do IF para performance)
    try:
        from modules import amarelos, batida_caixa, encerramentos, portabilidade, performance, scripts_rb
    except Exception as e:
        st.error(f"Erro ao carregar módulos: {e}")

    # Inicialização do estado (Boot)
    # [Mantenha aqui sua função boot_session_state() e a chamada dela]

    fuso_br = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(fuso_br)

    # --- MENU LATERAL E CONTEÚDO ---
    st.sidebar.title("🚀 Menu Principal")
    escolha = st.sidebar.radio(
        "Selecione a ferramenta:", 
        ["📑 Resumo Encerramento", "🟡 Resumo Amarelos", "📲 Portabilidade", "💰 Batida de Caixa", "📈 Performance TME", "🚧 Demanda Infra"]
    )

    # Renderização dos módulos
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

else:
    # Bloqueia o restante do app
    st.stop()
