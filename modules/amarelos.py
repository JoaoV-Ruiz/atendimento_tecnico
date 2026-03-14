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
from styles import apply_styles

# --- CONFIGURAÇÕES ---
URL_COLETA = "https://atendimento.osir.net.br/inviabilidade/huawei/filaProvisionamento.php"
URL_CHAT = "https://chat.osirnet.com.br/accounts/login/"

TABELA_NOMES = {
    "396": "DIOGO TABORDA", "728": "VINICIUS COPPA", "734": "NATHALI VALLIER",
    "956": "ERICA MARLOW", "1153": "MARIA EDUARDA", "1163": "JULIA DUARTE",
    "1177": "KAUÃ GOCKS", "1318": "FILIPE VAZ", "1267": "ALISSON GUERREIRO",
    "931": "JOÃO VITOR RUIZ", "960": "RICHER ARAUJO", "667": "CRISTIANO MARQUES", 
    "441": "CAIO ALVES DOS REIS", "968": "SINDEW CRIZEL", "322" : "IGOR SALDANHA"
}

def conectar_google_sheets():
    try:
        creds_info = json.loads(st.secrets["GOOGLE_JSON_CREDENTIALS"])
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)
        return client.open_by_url(st.secrets["SPREADSHEET_URL"])
    except: return None

def salvar_fechamento_google_sheets(df_atual, total_sucesso, total_falha):
    planilha = conectar_google_sheets()
    if not planilha: return
    try:
        nome_aba = f"FECHAMENTO_{datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%d-%m-%Y')}"
        try: aba = planilha.worksheet(nome_aba)
        except:
            aba = planilha.add_worksheet(title=nome_aba, rows="100", cols="10")
            aba.append_row(["Colaborador", "Qtd", "Data", "Sucesso", "Falha"])
        
        data_str = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%d/%m/%Y %H:%M")
        linhas = [[r["Colaborador"], r["Qtd"], data_str, total_sucesso, total_falha] for _, r in df_atual.iterrows()]
        aba.append_rows(linhas)
    except: pass

@st.cache_data(ttl=60, show_spinner=False)
def disparar_automacao():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(URL_COLETA)
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.ID, "login"))).send_keys(st.secrets["EMAIL_CORP"])
        driver.find_element(By.ID, "password").send_keys(st.secrets["SENHA_SISTEMA"])
        driver.find_element(By.NAME, "entrar").click()
        
        wait.until(EC.presence_of_element_located((By.XPATH, "//a[@data-checado]")))
        time.sleep(5) 
        
        # 1. Sucessos
        links_sucesso = driver.find_elements(By.XPATH, "//a[@data-checado]")
        total_sucesso = len(links_sucesso)
        
        # 2. Falhas
        linhas_falha = driver.find_elements(By.CSS_SELECTOR, "tbody.busca-falha tr")
        total_falha = len(linhas_falha)
        
        # 3. Contagem por colaborador (Baseado nos sucessos)
        contagem = {nome: 0 for nome in TABELA_NOMES.values()}
        total_checados = 0
        for link in links_sucesso:
            val = link.get_attribute("data-checado")
            if val in TABELA_NOMES:
                contagem[TABELA_NOMES[val]] += 1
                total_checados += 1
        
        df = pd.DataFrame(list(contagem.items()), columns=["Colaborador", "Qtd"])
        df_final = df[df["Qtd"] > 0].sort_values(by="Qtd", ascending=False)
        
        return df_final, total_checados, total_sucesso, total_falha
    except Exception as e:
        print(f"Erro coleta: {e}")
        return None, 0, 0, 0
    finally:
        driver.quit()

def enviar_relatorio_chat(total_sucesso, total_falha):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(URL_CHAT)
        wait = WebDriverWait(driver, 40)
        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(st.secrets["EMAIL_CORP"])
        driver.find_element(By.NAME, "password").send_keys(st.secrets["SENHA_ZULIP"])
        driver.find_element(By.NAME, "button").click()
        
        xpath_caue = "//*[contains(text(), 'Cauê Arócha')]"
        contato = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_caue)))
        driver.execute_script("arguments[0].click();", contato)
        time.sleep(3)

        agora = datetime.now(pytz.timezone('America/Sao_Paulo'))
        
        # MENSAGEM CONFORME SOLICITADO: Sucesso, Falha e Total
        mensagem = (
            f"📊 *Relatório Automático de Provisionamento*\n"
            f"🕒 Horário: {agora.strftime('%H:%M:%S')}\n"
            f"----------------------------------\n"
            f"✅ *Total Sucesso:* {total_sucesso}\n"
            f"❌ *Total Falha:* {total_falha}\n"
            f"📈 *Total Geral:* {total_sucesso + total_falha}\n"
            f"----------------------------------"
        )

        textarea = wait.until(EC.presence_of_element_located((By.ID, "compose-textarea")))
        driver.execute_script("arguments[0].value = arguments[1];", textarea, mensagem)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", textarea)
        time.sleep(2)
        
        btn_enviar = wait.until(EC.element_to_be_clickable((By.ID, "compose-send-button")))
        driver.execute_script("arguments[0].click();", btn_enviar)
        return True
    except: return False
    finally: driver.quit()

def realizar_coleta_e_envio_automatizado():
    df, checados, sucesso, falha = disparar_automacao()
    if df is not None:
        salvar_fechamento_google_sheets(df, sucesso, falha)
        # Envia apenas os totais para o relatório
        return enviar_relatorio_chat(sucesso, falha)
    return False

def render():
    apply_styles()
    st_autorefresh(interval=30000, key="refresh_amarelos")
    fuso = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(fuso)
    st.title("📊 Monitor de Provisionamento")
    
    if 'dados_cache' not in st.session_state: st.session_state['dados_cache'] = None
    if 'ultima_coleta' not in st.session_state: st.session_state['ultima_coleta'] = agora - timedelta(days=1)

    if st.session_state['dados_cache'] is None or (agora - st.session_state['ultima_coleta'] >= timedelta(minutes=5)):
        df, checados, sucesso, falha = disparar_automacao()
        st.session_state['dados_cache'] = (df, checados, sucesso, falha)
        st.session_state['ultima_coleta'] = agora

    if st.session_state['dados_cache']:
        df_d, t_c, t_s, t_f = st.session_state['dados_cache']
        st.caption(f"📥 Última atualização: {st.session_state['ultima_coleta'].strftime('%H:%M:%S')}")
        
        # MONITOR (Site): Mostra os pendentes de checagem
        m1, m2, m3 = st.columns(3)
        m1.metric("Fila Sucesso", t_s)
        m2.metric("Checados", t_c)
        m3.metric("Não Checados", t_s - t_c)
        
        st.divider()
        c1, c2 = st.columns([1, 1.5])
        c1.dataframe(df_d, use_container_width=True, hide_index=True)
        c2.bar_chart(df_d.set_index("Colaborador"))
