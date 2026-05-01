import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import pytz
import random

# --- TABELA DE NOMES MANTIDA ---
TABELA_NOMES = {
    "396": "DIOGO TABORDA", "728": "VINICIUS COPPA", "734": "NATHALI VALLIER",
    "956": "ERICA MARLOW", "1153": "MARIA EDUARDA", "1163": "JULIA DUARTE",
    "1177": "KAUÃ GOCKS", "1318": "FILIPE VAZ", "1267": "ALISSON GUERREIRO",
    "931": "JOÃO VITOR RUIZ", "960": "RICHER ARAUJO", "667": "CRISTIANO MARQUES", 
    "441": "CAIO ALVES DOS REIS", "968": "SINDEW CRIZEL", "322" : "IGOR SALDANHA"
}

# --- FUNÇÕES MOCKADAS (SIMULAÇÃO) ---
def salvar_fechamento_google_sheets(df_atual, total_sucesso, total_falha):
    # Simula o tempo de latência de rede salvando na planilha
    time.sleep(1)
    return True

@st.cache_data(ttl=60, show_spinner=False)
def disparar_automacao_demo():
    # Simula o tempo de raspagem de dados do sistema original
    time.sleep(2)
    
    # Gera dados fictícios distribuídos entre a equipe
    contagem = {nome: random.randint(0, 45) for nome in TABELA_NOMES.values()}
    
    # Alguns terão zero para simular a realidade
    for _ in range(5):
        chave_aleatoria = random.choice(list(contagem.keys()))
        contagem[chave_aleatoria] = 0

    df = pd.DataFrame(list(contagem.items()), columns=["Colaborador", "Qtd"])
    df_final = df[df["Qtd"] > 0].sort_values(by="Qtd", ascending=False)
    
    total_sucesso = df_final["Qtd"].sum()
    total_falha = random.randint(0, int(total_sucesso * 0.1)) # Falhas em torno de 10%
    total_checados = total_sucesso
    
    return df_final, total_checados, total_sucesso, total_falha

def enviar_relatorio_chat(total_sucesso, total_falha):
    # Simula a abertura do Chat (Zulip) e injeção da mensagem via Selenium
    time.sleep(2) 
    return True

def realizar_coleta_e_envio_automatizado():
    """ Função central """
    df, checados, sucesso, falha = disparar_automacao_demo()
    if df is not None:
        salvar_fechamento_google_sheets(df, sucesso, falha)
        return enviar_relatorio_chat(sucesso, falha)
    return False

def render():
    fuso_br = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(fuso_br)
    
    st.title("📊 Monitor de Provisionamento (Modo Demo)")
    st.info("💡 **Aviso de Portfólio:** A raspagem de dados e os envios automáticos pro Chat (Zulip) estão simulados para demonstrar a interface e a lógica em tempo real.")
    
    # --- INICIALIZAÇÃO DE VARIÁVEIS DE SESSÃO ---
    if "dados_cache" not in st.session_state:
        st.session_state.dados_cache = None
    if "ultima_coleta" not in st.session_state:
        st.session_state.ultima_coleta = agora - timedelta(minutes=10)
    
    # Gerenciamento de Cache
    if st.session_state.dados_cache is None or (agora - st.session_state.ultima_coleta >= timedelta(minutes=5)):
        df, checados, sucesso, falha = disparar_automacao_demo()
        st.session_state.dados_cache = (df, checados, sucesso, falha)
        st.session_state.ultima_coleta = agora

    # Exibição na Tela
    if st.session_state.dados_cache:
        df_d, t_c, t_s, t_f = st.session_state.dados_cache
        st.caption(f"📥 Última atualização do monitor: {st.session_state.ultima_coleta.strftime('%H:%M:%S')}")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Sucesso", t_s)
        m2.metric("Total Checado", t_c)
        m3.metric("Faltam Checar", abs(t_s - t_c) + random.randint(5, 20)) # Apenas para dar um visual dinâmico na demo
                    
        st.divider()
        
        if df_d is not None and not df_d.empty:
            c1, c2 = st.columns([1, 1.5])
            with c1:
                st.dataframe(df_d, use_container_width=True, hide_index=True)
            with c2:
                st.bar_chart(df_d.set_index("Colaborador"))
        else:
            st.info("Nenhum dado de produtividade detectado na fila no momento.")
