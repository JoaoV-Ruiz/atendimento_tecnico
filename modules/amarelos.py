import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import json
import pytz
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURAÇÕES ---
URL_COLETA = "https://atendimento.osir.net.br/inviabilidade/huawei/filaProvisionamento.php"
URL_CHAT = "https://chat.osirnet.com.br/accounts/login/"

def enviar_relatorio_chat(df_dados, total_tela, total_checados):
    """ Faz o login no Chat e envia o relatório para o Cauê """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 35)
        
        # 1. LOGIN NO CHAT
        driver.get(URL_CHAT)
        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(st.secrets["EMAIL_CORP"])
        driver.find_element(By.NAME, "password").send_keys(st.secrets["SENHA_ZULIP"])
        driver.find_element(By.NAME, "button").click()
        time.sleep(5)

        # 2. SELECIONAR O CONTATO (CAUÊ)
        # Ajuste o XPath se o nome na lista for diferente
        xpath_caue = "//span[contains(text(), 'Cauê Arócha')]"
        contato = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_caue)))
        driver.execute_script("arguments[0].click();", contato)
        time.sleep(2)

        # 3. MONTAR MENSAGEM
        agora = datetime.now(pytz.timezone('America/Sao_Paulo'))
        msg = (
            f"📊 *Relatório de Provisionamento*\n"
            f"🕒 Horário: {agora.strftime('%H:%M:%S')}\n"
            f"----------------------------------\n"
            f"✅ *Checados:* {total_checados}\n"
            f"⏳ *Pendentes:* {total_tela - total_checados}\n"
            f"📈 *Total Fila:* {total_tela}\n"
            f"----------------------------------"
        )

        # 4. ENVIAR VIA JS (Evita erros de foco no textarea)
        textarea = wait.until(EC.presence_of_element_located((By.ID, "compose-textarea")))
        driver.execute_script("arguments[0].value = arguments[1];", textarea, msg)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", textarea)
        time.sleep(1)
        
        btn_enviar = driver.find_element(By.ID, "compose-send-button")
        driver.execute_script("arguments[0].click();", btn_enviar)
        return True
    except Exception as e:
        print(f"Erro no envio Chat: {e}")
        return False
    finally:
        if driver: driver.quit()

def realizar_coleta_e_envio_automatizado():
    """ Função mestra chamada pelo gatilho das 23:45 """
    # Reutiliza a função de coleta que você já tem
    from modules.amarelos import disparar_automacao, salvar_fechamento_google_sheets
    
    df, checados, tela = disparar_automacao()
    if df is not None:
        # Salva no Sheets
        salvar_fechamento_google_sheets(df, tela, checados)
        # Envia para o Chat
        sucesso_envio = enviar_relatorio_chat(df, tela, checados)
        return sucesso_envio
    return False
