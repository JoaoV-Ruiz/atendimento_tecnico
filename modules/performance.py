import streamlit as st
import pandas as pd
import gspread
import json
import os
import re
import time
import glob
import unicodedata
import pytz
import calendar
from datetime import timedelta, datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from streamlit_autorefresh import st_autorefresh
from pathlib import Path
from styles import apply_styles

# --- CONFIGURAÇÕES E MAPEAMENTO ---
MAPEAMENTO_TECNICOS = {
    "Alisson Do Couto Guerreiro": "ALISSON DO COUTO GUERREIRO",
    "Caio Alves dos Reis": "CAIO REIS",
    "Cristiano Weber Marques": "CRISTIANO MARQUES",
    "Diogo Taborda de Bitencourt": "DIOGO TABORDA DE BITENCOURT",
    "Filipe Vieira Vaz": "FILIPE VIEIRA VAZ",
    "Igor Saldanha Noguez": "IGOR SALDANHA",
    "João Vitor Ruiz Barboza": "JOÃO VITOR RUIZ BARBOZA",
    "Julia da Silva Duarte": "JULIA DA SILVA DUARTE",
    "Kauã Larri Gocks da Silveira": "KAUA LARRI GOCKS DA SILVEIRA",
    "Nathali Elisa Xavier Vallier": "NATHALI VALLIER",
    "Richer Falcão Araujo": "RICHER FALCAO ARAUJO",
    "Sindew Crizel Nunes": "SINDEW CRIZEL NUNES",
    "Vinicius Maciel Coppa": "VINICIUS COPPA"
}

def super_limpeza(texto):
    if not isinstance(texto, str): return ""
    texto = texto.upper()
    texto = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in texto if not unicodedata.combining(c)])

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

def analisar_dados(caminho_csv, mes, ano):
    if not caminho_csv or not os.path.exists(caminho_csv): return None
    try:
        df = pd.read_csv(caminho_csv, sep=None, engine='python', encoding='latin-1', on_bad_lines='skip')
        col_data = [c for c in df.columns if "Encerramento" in c][0]
        df['DATA_REF'] = pd.to_datetime(df[col_data], dayfirst=True, errors='coerce')
        possiveis_cols = ["Atendente", "Usuário Encerramento", "Responsável"]
        col_tec = next((c for c in possiveis_cols if c in df.columns), df.columns[3])
        df['Atendente_Planilha'] = df[col_tec].apply(lambda x: next((k for k, v in MAPEAMENTO_TECNICOS.items() if super_limpeza(v) in super_limpeza(str(x))), None))
        return df[(df['DATA_REF'].dt.month == mes) & (df['DATA_REF'].dt.year == ano)].dropna(subset=['Atendente_Planilha'])
    except: return None

@st.cache_data(ttl=900)
def disparar_automacao_erp(download_path, mes, ano):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    prefs = {"download.default_directory": str(download_path.absolute())}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        wait = WebDriverWait(driver, 30)
        driver.get("https://erp.osirnet.com.br/all_solicitations#/")
        
        # Login
        try:
            wait.until(EC.presence_of_element_located((By.ID, ":r0:"))).send_keys(st.secrets["ERP_USER"])
            driver.find_element(By.ID, ":r1:").send_keys(st.secrets["ERP_PASS"])
            driver.find_element(By.XPATH, "//button[contains(., 'Entrar')]").click()
            time.sleep(5)
        except: pass

        # Filtros de Data
        hj = datetime.now()
        data_ini = f"01/{mes:02d}/{ano}"
        data_fim = hj.strftime("%d/%m/%Y") if (mes == hj.month and ano == hj.year) else f"{calendar.monthrange(ano, mes)[1]:02d}/{mes:02d}/{ano}"

        driver.get("https://erp.osirnet.com.br/all_solicitations#/")
        time.sleep(3)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@tooltip='Filtro avançado']"))).click()
        
        # (Aqui entra sua lógica de selecionar Equipe COP Encerramentos...)
        # Simulando preenchimento de data:
        for id_campo, val in [("beginReportClosingDate", data_ini), ("finalReportClosingDate", data_fim)]:
            el = driver.find_element(By.ID, id_campo)
            driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles:true}));", el, val)
        
        driver.find_element(By.XPATH, "//button[contains(., 'aplicar')]").click()
        time.sleep(10)
        
        # Exportar CSV
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@tooltip='Imprimir/Exportar']"))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '.CSV')]"))).click()
        
        time.sleep(5)
        arquivos = glob.glob(os.path.join(str(download_path), "*.csv"))
        if arquivos:
            return analisar_dados(max(arquivos, key=os.path.getmtime), mes, ano)
    except Exception as e:
        st.error(f"Erro Automação: {e}")
    finally:
        driver.quit()
    return None

def desenhar_aba(dados_tme, df_erp, tecnico, mes, ano, dia_limite):
    df_tec = df_erp[df_erp['Atendente_Planilha'] == tecnico] if df_erp is not None else pd.DataFrame()
    
    col1, col2, col3 = st.columns([2,1,1])
    with col1: st.markdown(f"#### {tecnico}")
    with col2: st.metric("Total ENC", f"{len(df_tec)} un")
    
    total = len(df_tec)
    st.progress(min(total/550, 1.0), text=f"Meta Normal (550): {total}")
    st.progress(min(total/681, 1.0), text=f"Super Meta (681): {total}")
    
    st.divider()
    grid = st.columns(7)
    counts = df_tec['DATA_REF'].dt.day.value_counts().to_dict() if not df_tec.empty else {}
    
    # TME
    mapa = {l[0]: l[3:] for l in dados_tme if len(l) > 0}
    tempos = mapa.get(tecnico, [""] * 31)

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
    st_autorefresh(interval=10 * 60 * 1000, key="auto_refresh_perf")
    
    agora = datetime.now(pytz.timezone('America/Sao_Paulo'))
    m_atual, a_atual = agora.month, agora.year
    dt_p = agora.replace(day=1) - timedelta(days=1)
    m_pass, a_pass = dt_p.month, dt_p.year

    download_path = Path(__file__).parent.parent / "temp_downloads"
    download_path.mkdir(exist_ok=True)

    dados_planilha = load_technical_data()
    if not dados_planilha: return
    
    nomes = sorted([l[0] for l in dados_planilha if len(l) > 0 and l[0] in MAPEAMENTO_TECNICOS])
    selecionado = st.selectbox("Técnico:", nomes)

    tab1, tab2 = st.tabs([f"📅 Mês Atual", f"⏪ Mês Anterior"])

    with tab1:
        df_a = disparar_automacao_erp(download_path, m_atual, a_atual)
        desenhar_aba(dados_planilha, df_a, selecionado, m_atual, a_atual, agora.day - 1)
    
    with tab2:
        df_p = disparar_automacao_erp(download_path, m_pass, a_pass)
        desenhar_aba(dados_planilha, df_p, selecionado, m_pass, a_pass, calendar.monthrange(a_pass, m_pass)[1])
