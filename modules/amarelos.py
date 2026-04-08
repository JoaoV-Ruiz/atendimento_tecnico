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

# --- CONFIGURAÇÕES LENDO DO CLOUD SECRETS ---
URL_COLETA = st.secrets["URL_COLETA"]
URL_CHAT = st.secrets["URL_CHAT"]
EMAIL_CORP = st.secrets["EMAIL_CORP"]
SENHA_SISTEMA = st.secrets["SENHA_SISTEMA"]
SENHA_ZULIP = st.secrets["SENHA_ZULIP"]
SPREADSHEET_URL = st.secrets["SPREADSHEET_URL"]

TABELA_NOMES = {
    "396": "DIOGO TABORDA", "728": "VINICIUS COPPA", "734": "NATHALI VALLIER",
    "956": "ERICA MARLOW", "1153": "MARIA EDUARDA", "1163": "JULIA DUARTE",
    "1177": "KAUÃ GOCKS", "1318": "FILIPE VAZ", "1267": "ALISSON GUERREIRO",
    "931": "JOÃO VITOR RUIZ", "960": "RICHER ARAUJO", "667": "CRISTIANO MARQUES", 
    "441": "CAIO ALVES DOS REIS", "968": "SINDEW CRIZEL", "322" : "IGOR SALDANHA"
}

# --- FUNÇÕES DE APOIO ---
def conectar_google_sheets():
    try:
        # Lê o JSON do st.secrets
        creds_json = json.loads(st.secrets["GOOGLE_JSON_CREDENTIALS"])
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
        client = gspread.authorize(creds)
        return client.open_by_url(SPREADSHEET_URL)
    except Exception as e:
        st.error(f"Erro na conexão com Google Sheets: {e}")
        return None

def salvar_fechamento_google_sheets(df_atual, total_sucesso, total_falha):
    planilha = conectar_google_sheets()
    if not planilha: return False
    try:
        fuso_br = pytz.timezone('America/Sao_Paulo')
        agora_br = datetime.now(fuso_br)
        nome_aba = f"FECHAMENTO_{agora_br.strftime('%d-%m-%Y')}"
        
        try: 
            aba = planilha.worksheet(nome_aba)
        except:
            aba = planilha.add_worksheet(title=nome_aba, rows="100", cols="10")
            aba.append_row(["Colaborador", "Qtd", "Data Registro", "Sucesso Geral", "Falha Geral"])
        
        data_str = agora_br.strftime("%d/%m/%Y %H:%M")
        linhas = [[r["Colaborador"], r["Qtd"], data_str, total_sucesso, total_falha] for _, r in df_atual.iterrows()]
        aba.append_rows(linhas)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar no Sheets: {e}")
        return False

@st.cache_data(ttl=60, show_spinner=False)
def disparar_automacao():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Forçar resolução e disfarçar o robô (Vital para rodar em nuvem)
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(URL_COLETA)
        wait = WebDriverWait(driver, 30)
        
        # Login no sistema de coleta
        wait.until(EC.presence_of_element_located((By.ID, "login"))).send_keys(EMAIL_CORP)
        time.sleep(0.5) 
        driver.find_element(By.ID, "password").send_keys(SENHA_SISTEMA)
        driver.find_element(By.NAME, "entrar").click()
        
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "lista-sucesso")))
        
        links_sucesso = driver.find_elements(By.XPATH, "//a[@data-checado]")
        total_sucesso = len(links_sucesso)
        
        linhas_falha = driver.find_elements(By.CSS_SELECTOR, "tbody.busca-falha tr")
        total_falha = len(linhas_falha)
        
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
        # Tira uma foto da tela e salva no servidor
        driver.save_screenshot("erro_nuvem.png")
        
        st.error(f"Erro na coleta Selenium. Veja o print abaixo:")
        # Exibe a foto no seu aplicativo
        st.image("erro_nuvem.png", caption="Visão do Robô no momento do erro")
        st.code(str(e))
        
        return None, 0, 0, 0

def enviar_relatorio_chat(total_sucesso, total_falha):
    """ Envia o relatório para o Cauê via Zulip/Chat """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get(URL_CHAT)
        wait = WebDriverWait(driver, 50)
        
        # 1. Login no Chat
        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(EMAIL_CORP)
        driver.find_element(By.NAME, "password").send_keys(SENHA_ZULIP)
        driver.find_element(By.NAME, "button").click()
        
        # 2. Aguarda o carregamento inicial do sistema
        time.sleep(15) 
        
        # 3. Localiza e Clica no Cauê Arócha
        xpath_caue = "//span[contains(text(), 'Cauê Arócha')]"
        contato = wait.until(EC.presence_of_element_located((By.XPATH, xpath_caue)))
        driver.execute_script("arguments[0].scrollIntoView();", contato)
        time.sleep(2)
        driver.execute_script("arguments[0].click();", contato)
        
        # 4. Aguarda a abertura da janela de digitação
        time.sleep(5)

        fuso_br = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(fuso_br)
        
        mensagem = (
            f"📊 *Relatório Automático de Provisionamento*\n"
            f"🕒 Horário: {agora.strftime('%H:%M:%S')}\n"
            f"----------------------------------\n"
            f"✅ *Total Sucesso:* {total_sucesso}\n"
            f"❌ *Total Falha:* {total_falha}\n"
            f"📈 *Total Acumulado:* {total_sucesso + total_falha}\n"
            f"----------------------------------"
        )

        # 5. Injeta a mensagem e dispara eventos para o sistema reconhecer o texto
        textarea = wait.until(EC.element_to_be_clickable((By.ID, "compose-textarea")))
        textarea.click() # Foca no campo
        driver.execute_script("arguments[0].value = arguments[1];", textarea, mensagem)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", textarea)
        time.sleep(1)
        
        # 6. Envio Final
        btn_enviar = driver.find_element(By.ID, "compose-send-button")
        driver.execute_script("arguments[0].click();", btn_enviar)
        
        time.sleep(3) # Aguarda o processamento do envio
        return True
    except Exception as e:
        print(f"Erro detalhado no envio para o Chat: {e}")
        return False
    finally:
        driver.quit()

def realizar_coleta_e_envio_automatizado():
    """ Função central """
    df, checados, sucesso, falha = disparar_automacao()
    if df is not None:
        salvar_fechamento_google_sheets(df, sucesso, falha)
        return enviar_relatorio_chat(sucesso, falha)
    return False

def render():
    st_autorefresh(interval=30000, key="refresh_amarelos")
    
    fuso_br = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(fuso_br)
    
    st.title("📊 Monitor de Provisionamento")
    
    # --- INICIALIZAÇÃO DE VARIÁVEIS DE SESSÃO ---
    if "dados_cache" not in st.session_state:
        st.session_state.dados_cache = None
    if "ultima_coleta" not in st.session_state:
        st.session_state.ultima_coleta = agora - timedelta(minutes=10)
    
    # Gerenciamento de Cache
    if st.session_state.dados_cache is None or (agora - st.session_state.ultima_coleta >= timedelta(minutes=5)):
        df, checados, sucesso, falha = disparar_automacao()
        st.session_state.dados_cache = (df, checados, sucesso, falha)
        st.session_state.ultima_coleta = agora

    # Exibição na Tela
    if st.session_state.dados_cache:
        df_d, t_c, t_s, t_f = st.session_state.dados_cache
        st.caption(f"📥 Última atualização do monitor: {st.session_state.ultima_coleta.strftime('%H:%M:%S')}")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Sucesso", t_s)
        m2.metric("Total Checado", t_c)
        m3.metric("Faltam Checar", t_s - t_c)
                    
        st.divider()
        
        if df_d is not None and not df_d.empty:
            c1, c2 = st.columns([1, 1.5])
            with c1:
                st.dataframe(df_d, use_container_width=True, hide_index=True)
            with c2:
                st.bar_chart(df_d.set_index("Colaborador"))
        else:
            st.info("Nenhum dado de produtividade detectado na fila no momento.")

if __name__ == "__main__":
    render()
