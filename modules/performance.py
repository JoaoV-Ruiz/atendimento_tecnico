import streamlit as st
import pandas as pd
import gspread
import json
import os
import re
import time
import glob
import shutil
import calendar
import unicodedata
import pytz
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from streamlit_autorefresh import st_autorefresh
from pathlib import Path
from styles import apply_styles

# --- 1. CONFIGURAÇÕES E MAPEAMENTO ---
MAPEAMENTO_TECNICOS = {
    "Alisson Do Couto Guerreiro": "ALISSON DO COUTO GUERREIRO",
    "Caio Alves dos Reis": "CAIO REIS",
    "Cristiano Weber Marques": "CRISTIANO MARQUES",
    "Diogo Taborda de Bitencourt": "DIOGO BITENCOURT",
    "Filipe Vieira Vaz": "FILIPE VIEIRA VAZ",
    "Igor Saldanha Noguez": "IGOR SALDANHA",
    "João Vitor Ruiz Barboza": "JOÃO VITOR RUIZ BARBOZA",
    "Julia da Silva Duarte": "JULIA DA SILVA DUARTE",
    "Kauã Larri Gocks da Silveira": "KAUÃ LARRI GOCKS DA SILVEIRA",
    "Nathali Elisa Xavier Vallier": "NATHALI VALLIER",
    "Richer Falcão Araujo": "RICHER FALCÃO ARAUJO",
    "Sindew Crizel Nunes": "SINDEW CRIZEL NUNES",
    "Vinicius Maciel Coppa": "VINICIUS COPPA"
}

# --- 2. FUNÇÕES DE APOIO ---
def super_limpeza(texto):
    if not isinstance(texto, str): return ""
    texto = texto.split(" / ")[0].upper()
    texto = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in texto if not unicodedata.combining(c)])

def converter_para_segundos(tempo_str):
    if not tempo_str or str(tempo_str).strip() in ["", "FORA"]: return None
    try:
        partes = str(tempo_str).split(':')
        h, m, s = (map(int, partes) if len(partes) == 3 else [0] + list(map(int, partes)))
        return h * 3600 + m * 60 + s
    except: return None

def formatar_segundos(segundos):
    return str(timedelta(seconds=int(segundos)))

@st.cache_data(ttl=600)
def load_technical_data():
    url = st.secrets.get("SPREADSHEET_URL")
    creds_json = st.secrets.get("GOOGLE_JSON_CREDENTIALS_2") or st.secrets.get("GOOGLE_JSON_CREDENTIALS")
    if not url or not creds_json: return None
    try:
        from google.oauth2.service_account import Credentials
        creds = Credentials.from_service_account_info(json.loads(creds_json), scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
        return gspread.authorize(creds).open_by_url(url).worksheet("AtendimentoTécnico").get("A8:AF20")
    except: return None

# --- 3. MOTOR DE AUTOMAÇÃO (SEM CACHE INTERNO PARA EVITAR CONFLITO) ---
def executar_robo_erp(mes, ano):
    BASE_DIR = Path(__file__).parent.parent
    DOWNLOAD_FOLDER = BASE_DIR / st.secrets["DOWNLOAD_PATH"].strip("/")
    DESTINO_FOLDER = BASE_DIR / st.secrets["DESTINO_PATH"].strip("/")
    DOWNLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    DESTINO_FOLDER.mkdir(parents=True, exist_ok=True)

    # Limpa downloads antigos
    for f in glob.glob(str(DOWNLOAD_FOLDER / "*")):
        try: os.remove(f)
        except: pass

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    abs_path = str(DOWNLOAD_FOLDER.absolute())
    chrome_options.add_experimental_option("prefs", {"download.default_directory": abs_path})
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": abs_path})
    
    try:
        wait = WebDriverWait(driver, 40)
        driver.get(st.secrets["URL_ERP"])
        
        # Login
        inputs = driver.find_elements(By.ID, ":r0:")
        if inputs:
            inputs[0].send_keys(st.secrets["ERP_USER"])
            driver.find_element(By.ID, ":r1:").send_keys(st.secrets["ERP_PASS"])
            driver.find_element(By.XPATH, "//button[contains(., 'Entrar')]").click()
            time.sleep(7)

        # Filtros
        driver.get(f"{st.secrets['URL_ERP']}#/all_solicitations")
        time.sleep(6)
        
        btn_filtro = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@tooltip='Filtro avançado']")))
        driver.execute_script("arguments[0].click();", btn_filtro)
        time.sleep(3)

        # Equipe
        wait.until(EC.element_to_be_clickable((By.ID, "teamId"))).click()
        f_all = wait.until(EC.visibility_of_element_located((By.ID, "filterAll")))
        f_all.send_keys("COP Encerramentos")
        f_all.send_keys(Keys.ENTER)
        time.sleep(3)
        item = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@id='datagrid_row' and contains(text(), 'COP Encerramentos')]")))
        driver.execute_script("arguments[0].click();", item)
        driver.find_element(By.XPATH, "//button[contains(., 'Confirmar')]").click()

        # Datas
        hj = datetime.now()
        data_ini = f"01/{mes:02d}/{ano}"
        data_fim = hj.strftime("%d/%m/%Y") if (mes == hj.month and ano == hj.year) else f"{calendar.monthrange(ano, mes)[1]:02d}/{mes:02d}/{ano}"

        script_react = "var el = document.getElementById(arguments[0]); el.value = arguments[1]; el.dispatchEvent(new Event('input', {bubbles:true}));"
        driver.execute_script(script_react, "beginReportClosingDate", data_ini)
        driver.execute_script(script_react, "finalReportClosingDate", data_fim)
        time.sleep(2)
        driver.find_element(By.XPATH, "//button[contains(., 'aplicar')]").click()
        time.sleep(10)

        # Exportar
        driver.execute_script("arguments[0].click();", wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@tooltip='Imprimir/Exportar']"))))
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '.CSV')]"))).click()
        
        # Monitorar Download
        for _ in range(30):
            arquivos = glob.glob(os.path.join(abs_path, "*.csv"))
            if arquivos and not any(f.endswith('.crdownload') for f in arquivos):
                recente = max(arquivos, key=os.path.getmtime)
                dest = DESTINO_FOLDER / f"perf_{mes}_{ano}.csv"
                shutil.move(recente, str(dest))
                # Processar CSV
                df = pd.read_csv(str(dest), sep=None, engine='python', encoding='latin-1')
                col_data = [c for c in df.columns if "Encerramento" in c][0]
                df['DATA_REF'] = pd.to_datetime(df[col_data], dayfirst=True, errors='coerce')
                possiveis_cols = ["Atendente", "Usuário Encerramento", "Responsável"]
                col_tec = next((c for c in possiveis_cols if c in df.columns), df.columns[3])
                df['Atendente_Planilha'] = df[col_tec].apply(lambda x: next((k for k, v in MAPEAMENTO_TECNICOS.items() if super_limpeza(v) in super_limpeza(str(x))), None))
                return df.dropna(subset=['Atendente_Planilha', 'DATA_REF'])
            time.sleep(2)
    finally:
        driver.quit()
    return None

# --- 4. COLETA UNIFICADA (A SOLUÇÃO PARA O STACKTRACE) ---
@st.cache_data(ttl=900, show_spinner="🤖 Sincronizando meses Atual e Anterior...")
def sincronizar_periodo_completo():
    fuso = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(fuso)
    m_at, a_at = agora.month, agora.year
    dt_p = agora.replace(day=1) - timedelta(days=1)
    m_pa, a_pa = dt_p.month, dt_p.year

    banco = {}
    banco['passado'] = executar_robo_erp(m_pa, a_pa)
    banco['atual'] = executar_robo_erp(m_at, a_at)
    return banco

# --- 5. INTERFACE ---
def desenhar_aba(dados_tme, df_erp, tecnico, mes, ano, dia_limite):
    df_tec = df_erp[df_erp['Atendente_Planilha'] == tecnico] if df_erp is not None else pd.DataFrame()
    total = len(df_tec)
    
    col1, col2, col3 = st.columns([2,1,1])
    with col1: st.markdown(f"#### {tecnico}")
    with col2: st.metric("Total Encerramentos", f"{total} un")
    
    st.progress(min(total/550, 1.0), text=f"Meta Normal (550): {total}")
    st.progress(min(total/681, 1.0), text=f"Super Meta (681): {total}")
    
    st.divider()
    grid = st.columns(7)
    counts = df_tec['DATA_REF'].dt.day.value_counts().to_dict() if not df_tec.empty else {}
    mapa_tme = {l[0]: l[3:] for l in dados_tme if len(l) > 0}
    tempos = mapa_tme.get(tecnico, [""] * 31)

    for i in range(dia_limite):
        dia = i + 1
        with grid[i % 7]:
            qtd = counts.get(dia, 0)
            tme = str(tempos[i]).strip() if i < len(tempos) else ""
            cor = "#FF4B4B" if converter_para_segundos(tme) and converter_para_segundos(tme) > 15 else "#FFFFFF"
            if tme in ["", "FORA"]: cor = "#FFD700"

            st.markdown(f"""
                <div style="background:#1d2129; padding:8px; border-radius:8px; border:1px solid #30363d; margin-bottom:8px; text-align:center;">
                    <small>{dia:02d}/{mes:02d}</small><br>
                    <b style="color:#4da3ff;">E: {qtd}</b><br>
                    <small style="color:{cor};">⏱️ {tme or '---'}</small>
                </div>
            """, unsafe_allow_html=True)

def render():
    apply_styles()
    st_autorefresh(interval=15 * 60 * 1000, key="refresh_perf")
    
    agora = datetime.now(pytz.timezone('America/Sao_Paulo'))
    dados_planilha = load_technical_data()
    if not dados_planilha: return
    
    nomes = sorted([l[0] for l in dados_planilha if len(l) > 0 and l[0] in MAPEAMENTO_TECNICOS])
    selecionado = st.selectbox("Técnico:", nomes)

    # Coleta em massa (Mês anterior + Mês atual)
    banco = sincronizar_periodo_completo()

    tab1, tab2 = st.tabs([f"📅 Mês Atual", f"⏪ Mês Anterior"])

    with tab1:
        desenhar_aba(dados_planilha, banco['atual'], selecionado, agora.month, agora.year, agora.day - 1)
    
    with tab2:
        dt_p = agora.replace(day=1) - timedelta(days=1)
        desenhar_aba(dados_planilha, banco['passado'], selecionado, dt_p.month, dt_p.year, calendar.monthrange(dt_p.year, dt_p.month)[1])
