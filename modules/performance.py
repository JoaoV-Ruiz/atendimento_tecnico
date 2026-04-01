import os
import re
import time
import glob
import shutil
import calendar
import unicodedata
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from streamlit_autorefresh import st_autorefresh
import json
import pytz
import gspread
from pathlib import Path
from styles import apply_styles

# --- 1. MAPEAMENTO DE NOMES (PLANILHA VS ERP) ---
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
    texto = "".join([c for c in texto if not unicodedata.combining(c)])
    return re.sub(r'[^A-Z]', '', texto)

def converter_para_segundos(tempo_str):
    if not tempo_str or str(tempo_str).strip() in ["", "FORA"]: return None
    try:
        partes = str(tempo_str).split(':')
        if len(partes) == 3:
            h, m, s = map(int, partes)
            return h * 3600 + m * 60 + s
        elif len(partes) == 2:
            m, s = map(int, partes)
            return m * 60 + s
        return float(tempo_str)
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
        scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = Credentials.from_service_account_info(json.loads(creds_json), scopes=scope)
        client = gspread.authorize(creds)
        return client.open_by_url(url).worksheet("AtendimentoTécnico").get("A8:AF20")
    except: return None

# --- 3. AUTOMAÇÃO SELENIUM (PARAMETRIZADA) ---
@st.cache_data(ttl=900, show_spinner=False)
def disparar_automacao_erp(mes, ano):
    BASE_DIR = Path(__file__).parent.parent
    DOWNLOAD_FOLDER = BASE_DIR / st.secrets["DOWNLOAD_PATH"].strip("/")
    DESTINO_FOLDER = BASE_DIR / st.secrets["DESTINO_PATH"].strip("/")
    DOWNLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    DESTINO_FOLDER.mkdir(parents=True, exist_ok=True)

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    abs_download_path = str(DOWNLOAD_FOLDER.absolute())
    prefs = {"download.default_directory": abs_download_path}
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": abs_download_path})
    
    try:
        wait = WebDriverWait(driver, 35)
        driver.get(st.secrets["URL_ERP"])
        
        # Login
        try:
            u_field = wait.until(EC.element_to_be_clickable((By.ID, ":r0:")))
            p_field = driver.find_element(By.ID, ":r1:")
            u_field.send_keys(st.secrets["ERP_USER"])
            p_field.send_keys(st.secrets["ERP_PASS"])
            driver.find_element(By.XPATH, "//button[contains(., 'Entrar')]").click()
            time.sleep(8)
        except: pass

        # Filtros
        driver.get(st.secrets["URL_ERP"])
        time.sleep(5)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@tooltip='Filtro avançado']"))).click()
        time.sleep(3)

        # Equipe
        driver.find_element(By.ID, "teamId").click()
        time.sleep(1)
        f_all = wait.until(EC.element_to_be_clickable((By.ID, "filterAll")))
        f_all.send_keys("COP Encerramentos")
        f_all.send_keys(Keys.ENTER)
        time.sleep(3)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@id='datagrid_row' and contains(text(), 'COP Encerramentos')]"))).click()
        driver.find_element(By.XPATH, "//button[contains(., 'Confirmar')]").click()

        # Datas Dinâmicas
        hj = datetime.now()
        data_ini = f"01/{mes:02d}/{ano}"
        if mes == hj.month and ano == hj.year:
            data_fim = hj.strftime("%d/%m/%Y")
        else:
            data_fim = f"{calendar.monthrange(ano, mes)[1]:02d}/{mes:02d}/{ano}"

        script_data = """
            var el = document.getElementById(arguments[0]);
            el.value = arguments[1];
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
        """
        driver.execute_script(script_data, "beginReportClosingDate", data_ini)
        driver.execute_script(script_data, "finalReportClosingDate", data_fim)
        
        driver.find_element(By.XPATH, "//button[contains(., 'aplicar')]").click()
        time.sleep(12)

        # Exportar
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@tooltip='Imprimir/Exportar']"))).click()
        driver.find_element(By.XPATH, "//button[contains(., '.CSV')]").click()
        
        time.sleep(25)
        arquivos = glob.glob(os.path.join(abs_download_path, "*"))
        if arquivos:
            recente = max(arquivos, key=os.path.getmtime)
            nome_arq = f"perf_{mes}_{ano}.csv"
            caminho_final = DESTINO_FOLDER / nome_arq
            shutil.move(recente, str(caminho_final.absolute()))
            
            # Analisar CSV
            df = pd.read_csv(str(caminho_final.absolute()), sep=None, engine='python', encoding='latin-1')
            col_data = [c for c in df.columns if "Encerramento" in c][0]
            df['DATA_REF'] = pd.to_datetime(df[col_data], dayfirst=True, errors='coerce')
            possiveis_cols = ["Atendente", "Usuário Encerramento", "Responsável"]
            col_tec = next((c for c in possiveis_cols if c in df.columns), df.columns[3])
            
            # Limpeza e Mapeamento
            df['Atendente_Planilha'] = df[col_tec].apply(lambda x: next((k for k, v in MAPEAMENTO_TECNICOS.items() if super_limpeza(v) in super_limpeza(str(x))), None))
            return df.dropna(subset=['Atendente_Planilha', 'DATA_REF'])
            
    except Exception as e:
        st.error(f"Erro Automação ({mes}/{ano}): {e}")
    finally:
        driver.quit()
    return None

# --- 4. RENDERIZAÇÃO DE INTERFACE ---
def render_aba(dados_tme, df_erp, tecnico, mes, ano, dia_limite):
    df_tec = df_erp[df_erp['Atendente_Planilha'] == tecnico] if df_erp is not None else pd.DataFrame()
    total = len(df_tec)
    
    c1, c2, c3 = st.columns([2,1,1])
    with c1: st.markdown(f"#### {tecnico}")
    with c2: st.metric("Total ENC", f"{total} un")
    
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
    st_autorefresh(interval=10 * 60 * 1000, key="auto_perf_v3")
    
    fuso = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(fuso)
    m_atual, a_atual = agora.month, agora.year
    
    # Datas Mês Anterior
    dt_passado = agora.replace(day=1) - timedelta(days=1)
    m_pass, a_pass = dt_passado.month, dt_passado.year

    dados_planilha = load_technical_data()
    if not dados_planilha: return
    
    tecnicos = sorted([l[0] for l in dados_planilha if len(l) > 0 and l[0] in MAPEAMENTO_TECNICOS])
    selecionado = st.selectbox("Selecione o Técnico:", tecnicos)
    
    tab1, tab2 = st.tabs([f"📅 {m_atual:02d}/{a_atual}", f"⏪ {m_pass:02d}/{a_pass}"])
    
    with tab1:
        df_a = disparar_automacao_erp(m_atual, a_atual)
        render_aba(dados_planilha, df_a, selecionado, m_atual, a_atual, agora.day - 1)

    with tab2:
        df_p = disparar_automacao_erp(m_pass, a_pass)
        ultimo_dia = calendar.monthrange(a_pass, m_pass)[1]
        render_aba(dados_planilha, df_p, selecionado, m_pass, a_pass, ultimo_dia)
