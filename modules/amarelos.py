import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from streamlit_autorefresh import st_autorefresh
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import time
import json
import pytz
from styles import apply_styles, render_timer_box

# --- CONFIGURAÇÕES FIXAS ---
TABELA_NOMES = {
    "396": "DIOGO TABORDA", "728": "VINICIUS COPPA", "734": "NATHALI VALLIER",
    "956": "ERICA MARLOW", "1153": "MARIA EDUARDA", "1163": "JULIA DUARTE",
    "1177": "KAUÃ GOCKS", "1318": "FILIPE VAZ", "1267": "ALISSON GUERREIRO",
    "931": "JOÃO VITOR RUIZ", "960": "RICHER ARAUJO", "667": "CRISTIANO MARQUES", 
    "441": "CAIO ALVES DOS REIS", "968": "SINDEW CRIZEL", "322" : "IGOR SALDANHA"
}

URL_COLETA = "https://atendimento.osir.net.br/inviabilidade/huawei/filaProvisionamento.php"

# --- FUNÇÕES DE APOIO ---
def conectar_google_sheets():
    try:
        creds_info = json.loads(st.secrets["GOOGLE_JSON_CREDENTIALS"])
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)
        planilha = client.open_by_url(st.secrets["SPREADSHEET_URL"])
        return planilha
    except Exception as e:
        st.error(f"Erro na conexão com Google Sheets: {e}")
        return None

def salvar_fechamento_google_sheets(df_atual, total_tela, total_checados):
    planilha = conectar_google_sheets()
    if not planilha: return
    try:
        try:
            aba = planilha.worksheet("Historico_Amarelos")
        except:
            aba = planilha.add_worksheet(title="Historico_Amarelos", rows="1000", cols="10")
            aba.append_row(["Data/Hora", "Colaborador", "Qtd", "Total Tela", "Total Checados"])

        fuso_br = pytz.timezone('America/Sao_Paulo')
        agora_br = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M:%S")

        novas_linhas = []
        for _, row in df_atual.iterrows():
            novas_linhas.append([agora_br, row["Colaborador"], row["Qtd"], total_tela, total_checados])
        
        aba.append_rows(novas_linhas)
        st.toast("✅ Fechamento registrado no Google Sheets!", icon="💾")
    except Exception as e:
        st.error(f"Erro ao registrar no Sheets: {e}")

@st.cache_data(ttl=60, show_spinner=False)
def disparar_automacao():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 30)
        driver.get(URL_COLETA)

        # Login usando Secrets
        wait.until(EC.element_to_be_clickable((By.ID, "login"))).send_keys(st.secrets["EMAIL_CORP"])
        driver.find_element(By.ID, "password").send_keys(st.secrets["SENHA_SISTEMA"])
        driver.find_element(By.NAME, "entrar").click()

        wait.until(EC.presence_of_element_located((By.XPATH, "//a[@data-checado]")))
        time.sleep(2) 

        links = driver.find_elements(By.XPATH, "//a[@data-checado]")
        total_tela = len(links)
        contagem = {nome: 0 for nome in TABELA_NOMES.values()}
        total_checados = 0
        
        for link in links:
            valor = link.get_attribute("data-checado")
            if valor in TABELA_NOMES:
                nome_colaborador = TABELA_NOMES[valor]
                contagem[nome_colaborador] += 1
                total_checados += 1

        df_res = pd.DataFrame(list(contagem.items()), columns=["Colaborador", "Qtd"])
        df_interface = df_res[df_res["Qtd"] > 0].sort_values(by="Qtd", ascending=False)
        
        return df_interface, total_checados, total_tela
    except Exception as e:
        st.error(f"Erro na coleta automática: {e}")
        return None, 0, 0
    finally:
        if driver: driver.quit()

def render():
    # Aplica CSS e Footer
    apply_styles()
    
    # Auto-refresh a cada 30 segundos
    st_autorefresh(interval=30000, key="auto_refresh_amarelos")
    
    # 1. Configuração de Fuso Horário (AWARE)
    fuso_br = pytz.timezone('America/Sao_Paulo')
    agora_atual = datetime.now(fuso_br)
    
    st.title("📊 Monitor de Provisionamento")

    # 2. Inicialização segura do Session State
    if 'dados_cache' not in st.session_state:
        st.session_state['dados_cache'] = None
    
    if 'ultima_coleta' not in st.session_state or st.session_state['ultima_coleta'] is None:
        st.session_state['ultima_coleta'] = agora_atual - timedelta(days=1)

    # 3. Proteção contra erro de fuso horário (TypeError)
    try:
        tempo_passado = agora_atual - st.session_state['ultima_coleta']
    except TypeError:
        st.session_state['ultima_coleta'] = agora_atual - timedelta(days=1)
        tempo_passado = agora_atual - st.session_state['ultima_coleta']

    # 4. Lógica de Disparo do Robô (TTL de 1 minuto)
    if st.session_state['dados_cache'] is None or tempo_passado >= timedelta(minutes=1):
        with st.spinner("Sincronizando com o sistema..."):
            df, checados, tela = disparar_automacao()
            if df is not None:
                st.session_state['dados_cache'] = (df, checados, tela)
                st.session_state['ultima_coleta'] = agora_atual

    # --- INTERFACE ---
    if st.session_state['dados_cache']:
        df_dados, total_checados, total_tela = st.session_state['dados_cache']
        
        # Chama o box de horários do styles.py
        render_timer_box( 
            st.session_state['ultima_coleta'].strftime('%H:%M:%S')
        )

        m1, m2, m3 = st.columns(3)
        m1.metric("Fila Total", total_tela)
        m2.metric("Checados", total_checados)
        m3.metric("Pendente", total_tela - total_checados)

        st.divider()
        c1, c2 = st.columns([1, 1.5])
        with c1:
            st.markdown("### 🏆 Produtividade")
            st.dataframe(df_dados, use_container_width=True, hide_index=True)
        with c2:
            st.markdown("### 📈 Gráfico")
            st.bar_chart(df_dados.set_index("Colaborador"))
            
        # Botão para salvar no Google Sheets manualmente
        if st.button("💾 REGISTRAR FECHAMENTO NO GOOGLE SHEETS", use_container_width=True, type="primary"):
            salvar_fechamento_google_sheets(df_dados, total_tela, total_checados)
    else:
        st.info("Aguardando primeira coleta de dados...")
