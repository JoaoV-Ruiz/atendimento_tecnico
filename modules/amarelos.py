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

# ... (TABELA_NOMES e URLs permanecem iguais) ...
URL_COLETA = "https://atendimento.osir.net.br/inviabilidade/huawei/filaProvisionamento.php"
URL_CHAT = "https://chat.osirnet.com.br/accounts/login/"

def enviar_relatorio_chat(total_sucesso, total_falha):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(URL_CHAT)
        wait = WebDriverWait(driver, 45)
        
        # Login
        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(st.secrets["EMAIL_CORP"])
        driver.find_element(By.NAME, "password").send_keys(st.secrets["SENHA_ZULIP"])
        driver.find_element(By.NAME, "button").click()
        
        # Busca do Cauê (Tenta o seu XPath que funcionava)
        time.sleep(7)
        try:
            # XPath Original que você usava
            xpath = "//span[contains(@class, 'conversation-partners-list') and contains(text(), 'Cauê Arócha')]"
            contato = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        except:
            # XPath Genérico caso o outro mude
            xpath = "//*[contains(text(), 'Cauê Arócha')]"
            contato = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            
        driver.execute_script("arguments[0].click();", contato)
        time.sleep(3)

        agora = datetime.now(pytz.timezone('America/Sao_Paulo'))
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
        
        btn_enviar = driver.find_element(By.ID, "compose-send-button")
        driver.execute_script("arguments[0].click();", btn_enviar)
        return True
    except Exception as e:
        print(f"ERRO NO CHAT: {e}")
        return False
    finally:
        driver.quit()

# As outras funções (salvar_fechamento_google_sheets, disparar_automacao, realizar_coleta_e_envio_automatizado, render)
# permanecem com a mesma lógica do bloco anterior, apenas certifique-se de que os nomes batem.
