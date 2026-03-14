import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import time
import pytz

# ... (TABELA_NOMES e URLs permanecem iguais)

@st.cache_data(ttl=60, show_spinner=False)
def disparar_automacao():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get("https://atendimento.osir.net.br/inviabilidade/huawei/filaProvisionamento.php")
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.ID, "login"))).send_keys(st.secrets["EMAIL_CORP"])
        driver.find_element(By.ID, "password").send_keys(st.secrets["SENHA_SISTEMA"])
        driver.find_element(By.NAME, "entrar").click()
        
        wait.until(EC.presence_of_element_located((By.XPATH, "//a[@data-checado]")))
        time.sleep(5) 
        
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
    except:
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
        driver.get("https://chat.osirnet.com.br/accounts/login/")
        wait = WebDriverWait(driver, 40)
        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(st.secrets["EMAIL_CORP"])
        driver.find_element(By.NAME, "password").send_keys(st.secrets["SENHA_ZULIP"])
        driver.find_element(By.NAME, "button").click()
        
        time.sleep(7)
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
            f"📈 *Total Acumulado:* {total_sucesso + total_falha}\n"
            f"----------------------------------"
        )

        textarea = wait.until(EC.presence_of_element_located((By.ID, "compose-textarea")))
        driver.execute_script("arguments[0].value = arguments[1];", textarea, mensagem)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", textarea)
        time.sleep(2)
        driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "compose-send-button"))
        return True
    except: return False
    finally: driver.quit()

def realizar_coleta_e_envio_automatizado():
    df, checados, sucesso, falha = disparar_automacao()
    if df is not None:
        return enviar_relatorio_chat(sucesso, falha)
    return False

def render():
    st_autorefresh(interval=30000, key="refresh_amarelos")
    fuso = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(fuso)
    st.title("📊 Monitor de Provisionamento")
    
    if st.session_state.dados_cache is None or (agora - st.session_state.ultima_coleta >= timedelta(minutes=5)):
        df, checados, sucesso, falha = disparar_automacao()
        st.session_state.dados_cache = (df, checados, sucesso, falha)
        st.session_state.ultima_coleta = agora

    if st.session_state.dados_cache:
        df_d, t_c, t_s, t_f = st.session_state.dados_cache
        st.caption(f"📥 Última atualização: {st.session_state.ultima_coleta.strftime('%H:%M:%S')}")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Sucesso", t_s)
        m2.metric("Total Checado", t_c)
        m3.metric("Faltam Checar", t_s - t_c)
        
        st.divider()
        c1, c2 = st.columns([1, 1.5])
        c1.dataframe(df_d, hide_index=True)
        c2.bar_chart(df_d.set_index("Colaborador"))
