import streamlit as st
from styles import apply_styles
from dotenv import load_dotenv
import os
import pytz
from datetime import datetime
# Configuração do Fuso
fuso_br = pytz.timezone('America/Sao_Paulo')
agora = datetime.now(fuso_br)

# Defina o horário do gatilho
HORA_ALVO = 16
MINUTO_ALVO = 15
ARQUIVO_TRAVA = "trava_diaria.txt"

# LÓGICA DO GATILHO SILENCIOSO
if agora.hour == HORA_ALVO and agora.minute == MINUTO_ALVO:
    # Verifica se já rodou hoje usando um arquivo físico no servidor
    ja_rodou = False
    if os.path.exists(ARQUIVO_TRAVA):
        with open(ARQUIVO_TRAVA, "r") as f:
            data_gravada = f.read().strip()
            if data_gravada == agora.strftime("%Y-%m-%d"):
                ja_rodou = True

    if not ja_rodou:
        # Registra a trava ANTES para não duplicar se o Streamlit atualizar
        with open(ARQUIVO_TRAVA, "w") as f:
            f.write(agora.strftime("%Y-%m-%d"))
            
        # CHAMA O ROBÔ DO MÓDULO AMARELOS
        with st.status("🤖 Iniciando Relatório Automático das 23:45..."):
            sucesso = amarelos.realizar_coleta_e_envio_automatizado()
            if sucesso:
                st.success("Relatório enviado para o Cauê!")
            else:
                # Se falhou, remove a trava para tentar de novo no próximo minuto
                os.remove(ARQUIVO_TRAVA)
                
# 1. Carregar configurações
load_dotenv()
st.set_page_config(page_title="Indicadores Atend. Ao Técnico", layout="wide", page_icon="🚀")
apply_styles()

# 2. INICIALIZAÇÃO DO CACHE PERMANENTE
# Criamos as chaves originais aqui para que elas persistam entre as abas
if 'batida_version' not in st.session_state:
    st.session_state.batida_version = 0
if 'batida_proto' not in st.session_state:
    for campo in ['batida_proto', 'batida_tec', 'batida_cx', 'anot_batida']:
        st.session_state[campo] = ""
    
    st.session_state.portas = []
    
    for i in range(16):
        for prefixo in ['e_b_', 's_b_', 'id_b_']:
            st.session_state[f"{prefixo}{i}"] = ""
        # Checkbox permanente (booleano)
        st.session_state[f"c_batida_{i}"] = False

# 3. Importação dos módulos
from modules import batida_caixa, encerramentos, amarelos, portabilidade

# --- MENU LATERAL ---
with st.sidebar:
    st.title("🛠️ Operações")
    opcao = st.radio(
        "Selecione a Ferramenta:",
        ["Resumo Encerramentos", "Resumo Amarelos", "Mascara Portabilidade", "Batida de Caixa"]
    )
    st.divider()

# --- NAVEGAÇÃO ---
if opcao == "Batida de Caixa":
    batida_caixa.render()
elif opcao == "Resumo Encerramentos":
    encerramentos.render()
elif opcao == "Resumo Amarelos":
    amarelos.render()
elif opcao == "Mascara Portabilidade":
    portabilidade.render()
