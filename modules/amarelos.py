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

# --- CONFIGURAÇÕES FIXAS ---
TABELA_NOMES = {
    "396": "DIOGO TABORDA", "728": "VINICIUS COPPA", "734": "NATHALI VALLIER",
    "956": "ERICA MARLOW", "1153": "MARIA EDUARDA", "1163": "JULIA DUARTE",
    "1177": "KAUÃ GOCKS", "1318": "FILIPE VAZ", "1267": "ALISSON GUERREIRO",
    "931": "JOÃO VITOR RUIZ", "960": "RICHER ARAUJO", "667": "CRISTIANO MARQUES", 
    "441": "CAIO ALVES DOS REIS", "968": "SINDEW CRIZEL", "322" : "IGOR SALDANHA"
}

URL_COLETA = "https://atendimento.osir.net.br/inviabilidade/huawei/filaProvisionamento.php"
URL_CHAT = "https://chat.osirnet.com.br/accounts/login/"

# --- FUNÇÕES DE APOIO ---
def conectar_google_sheets():
    try:
        creds_info = json.loads(st.secrets["GOOGLE_JSON_CREDENTIALS"])
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)
        return client.open_by_url(st.secrets["SPREADSHEET_URL"])
    except Exception as e:
        print(f"Erro conexão Sheets: {e}")
        return None

def salvar_fechamento_google_sheets(df_atual, total_tela, total_checados):
    planilha = conectar_google_sheets()
    if not planilha: return
    try:
        fuso_br = pytz.timezone('America/Sao_Paulo')
        agora_br = datetime.now(fuso_br)
        nome_aba = f"FECHAMENTO_{agora_br.strftime('%d-%m-%Y')}"
        
        try:
            aba = planilha.worksheet(nome_aba)
        except:
            aba = planilha.add_worksheet(title=nome_aba, rows="100", cols="10")
            aba.append_row(["Colaborador", "Qtd", "Data/Hora", "Total Tela", "Total Checados"])
        
        data_str = agora_br.strftime("%d/%m/%Y %H:%M:%S")
        novas_linhas = [[r["Colaborador"], r["Qtd"], data_str, total_tela, total_checados] for _, r in df_atual.iterrows()]
        
        aba.append_rows(novas_linhas)
        print(f"✅ Dados salvos na aba {nome_aba}")
    except Exception as e:
        print(f"Erro ao salvar no Sheets: {e}")

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
        time.sleep(3)
        links = driver.find_elements(By.XPATH, "//a[@data-checado]")
        
        total_tela = len(links)
        contagem = {nome: 0 for nome in TABELA_NOMES.values()}
        total_checados = 0
        
        for link in links:
            val = link.get_attribute("data-checado")
            if val in TABELA_NOMES:
                contagem[TABELA_NOMES[val]] += 1
                total_checados += 1
                
        df = pd.DataFrame(list(contagem.items()), columns=["Colaborador", "Qtd"])
        df_final = df[df["Qtd"] > 0].sort_values(by="Qtd", ascending=False)
        return df_final, total_checados, total_tela
    except Exception as e:
        print(f"Erro na coleta: {e}")
        return None, 0, 0
    finally:
        driver.quit()

def enviar_relatorio_chat(df_dados, total_tela, total_checados):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(URL_CHAT)
        wait = WebDriverWait(driver, 40)
        
        # Login no Chat
        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(st.secrets["EMAIL_CORP"])
        driver.find_element(By.NAME, "password").send_keys(st.secrets["SENHA_ZULIP"])
        driver.find_element(By.NAME, "button").click()
        
        # Localizar Cauê (Busca por texto para ser mais resiliente)
        xpath_caue = "//*[contains(text(), 'Cauê Arócha')]"
        contato = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_caue)))
        driver.execute_script("arguments[0].click();", contato)
        time.sleep(3)

        # Montagem da Mensagem
        agora_br = datetime.now(pytz.timezone('America/Sao_Paulo'))
        mensagem = (
            f"📊 *Relatório Automático de Provisionamento*\n"
            f"🕒 Horário: {agora_br.strftime('%H:%M:%S')}\n"
            f"----------------------------------\n"
            f"✅ *Checados:* {total_checados}\n"
            f"⏳ *Pendentes:* {total_tela - total_checados}\n"
            f"📈 *Total Fila:* {total_tela}\n"
            f"----------------------------------"
        )

        # Inserção da Mensagem via JS
        textarea = wait.until(EC.presence_of_element_located((By.ID, "compose-textarea")))
        driver.execute_script("arguments[0].value = arguments[1];", textarea, mensagem)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", textarea)
        time.sleep(2)
        
        # Clique no Enviar via JS
        btn_enviar = wait.until(EC.element_to_be_clickable((By.ID, "compose-send-button")))
        driver.execute_script("arguments[0].click();", btn_enviar)
        
        print("🚀 Relatório enviado com sucesso para o Chat!")
        return True
    except Exception as e:
        print(f"❌ Erro no envio do Chat: {e}")
        return False
    finally:
        driver.quit()

def realizar_coleta_e_envio_automatizado():
    """ Função Mestra chamada pela Main """
    df, checados, tela = disparar_automacao()
    if df is not None:
        # 1. Salva no Sheets
        salvar_fechamento_google_sheets(df, tela, checados)
        # 2. Envia para o Chat
        return enviar_relatorio_chat(df, tela, checados)
    return False

def render():
    apply_styles()
    st_autorefresh(interval=30000, key="refresh_amarelos")
    fuso = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(fuso)
    
    st.title("📊 Monitor de Provisionamento")
    
    if 'dados_cache' not in st.session_state: st.session_state['dados_cache'] = None
    if 'ultima_coleta' not in st.session_state: st.session_state['ultima_coleta'] = agora - timedelta(days=1)

    # Lógica de atualização a cada 5 minutos no monitor visual
    if st.session_state['dados_cache'] is None or (agora - st.session_state['ultima_coleta'] >= timedelta(minutes=5)):
        df, checados, tela = disparar_automacao()
        st.session_state['dados_cache'] = (df, checados, tela)
        st.session_state['ultima_coleta'] = agora

    if st.session_state['dados_cache']:
        df_d, t_c, t_t = st.session_state['dados_cache']
        st.caption(f"📥 Última atualização: {st.session_state['ultima_coleta'].strftime('%H:%M:%S')}")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Fila Total", t_t)
        m2.metric("Checados", t_c)
        m3.metric("Pendente", t_t - t_c)
        
        st.divider()
        c1, c2 = st.columns([1, 1.5])
        c1.dataframe(df_d, use_container_width=True, hide_index=True)
        c2.bar_chart(df_d.set_index("Colaborador"))
