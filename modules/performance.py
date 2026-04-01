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
        # Suporta H:M:S ou M:S
        if len(partes) == 3:
            h, m, s = map(int, partes)
            return h * 3600 + m * 60 + s
        elif len(partes) == 2:
            m, s = map(int, partes)
            return m * 60 + s
        return None
    except: return None

def formatar_segundos(segundos):
    if segundos is None or segundos < 0: return "00:00:00"
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

def executar_robo_erp(mes, ano):
    BASE_DIR = Path(__file__).parent.parent
    DOWNLOAD_FOLDER = BASE_DIR / st.secrets["DOWNLOAD_PATH"].strip("/")
    DESTINO_FOLDER = BASE_DIR / st.secrets["DESTINO_PATH"].strip("/")
    DOWNLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    DESTINO_FOLDER.mkdir(parents=True, exist_ok=True)

    # Limpeza
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
        wait = WebDriverWait(driver, 45)
        driver.get(st.secrets["URL_ERP"])
        
        # 1. LOGIN
        inputs = driver.find_elements(By.ID, ":r0:")
        if inputs:
            inputs[0].send_keys(st.secrets["ERP_USER"])
            driver.find_element(By.ID, ":r1:").send_keys(st.secrets["ERP_PASS"])
            driver.find_element(By.XPATH, "//button[contains(., 'Entrar')]").click()
            time.sleep(8)
        
        # Tela Antiga
        try:
            btn_ant = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Tela antiga']")))
            driver.execute_script("arguments[0].click();", btn_ant)
            time.sleep(6)
        except: pass
            
        # 2. ACESSO DIRETOR E FILTRO
        driver.get(st.secrets['URL_ERP'])
        time.sleep(10)

        script_abrir_filtro = """
        var botoes = document.querySelectorAll('button');
        var clicou = false;
        botoes.forEach(btn => {
            if (btn.innerHTML.includes('fa-filter') || btn.getAttribute('tooltip') === 'Filtro avançado') {
                btn.click();
                clicou = true;
            }
        });
        return clicou;
        """
        
        if driver.execute_script(script_abrir_filtro):
            time.sleep(5)
            # Seleção Equipe
            campo_eq = wait.until(EC.presence_of_element_located((By.ID, "teamId")))
            driver.execute_script("arguments[0].click();", campo_eq)
            time.sleep(2)
            f_all = wait.until(EC.visibility_of_element_located((By.ID, "filterAll")))
            f_all.send_keys("COP Encerramentos")
            f_all.send_keys(Keys.ENTER)
            time.sleep(3)
            item = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@id='datagrid_row' and contains(text(), 'COP Encerramentos')]")))
            driver.execute_script("arguments[0].click();", item)
            driver.find_element(By.XPATH, "//button[contains(., 'Confirmar')]").click()
            time.sleep(2)

            # Datas
            hj = datetime.now()
            data_ini = f"01/{mes:02d}/{ano}"
            data_fim = hj.strftime("%d/%m/%Y") if (mes == hj.month and ano == hj.year) else f"{calendar.monthrange(ano, mes)[1]:02d}/{mes:02d}/{ano}"

            script_react = "var el = document.getElementById(arguments[0]); el.value = arguments[1]; el.dispatchEvent(new Event('input', {bubbles:true}));"
            driver.execute_script(script_react, "beginReportClosingDate", data_ini)
            driver.execute_script(script_react, "finalReportClosingDate", data_fim)
            time.sleep(2)
            driver.execute_script("arguments[0].click();", driver.find_element(By.XPATH, "//button[contains(., 'aplicar')]"))
            time.sleep(12)

            # Exportação
            btn_exp = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@tooltip='Imprimir/Exportar']")))
            driver.execute_script("arguments[0].click();", btn_exp)
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '.CSV')]"))).click()
            
            # Download
            for _ in range(40):
                arquivos = glob.glob(os.path.join(abs_path, "*.csv"))
                if arquivos and not any(f.endswith('.crdownload') for f in arquivos):
                    recente = max(arquivos, key=os.path.getmtime)
                    dest = DESTINO_FOLDER / f"perf_{mes}_{ano}.csv"
                    shutil.move(recente, str(dest))
                    df = pd.read_csv(str(dest), sep=None, engine='python', encoding='latin-1')
                    return df # Retorna o dataframe bruto para processamento
                time.sleep(2)
        return None
    except Exception as e:
        st.error(f"Erro no Robô ({mes}/{ano}): {e}")
        return None
    finally:
        driver.quit()

@st.cache_data(ttl=900, show_spinner="🤖 Sincronizando Período Completo...")
def sincronizar_periodo_completo():
    fuso = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(fuso)
    # Mês Atual
    df_atual = executar_robo_erp(agora.month, agora.year)
    # Mês Anterior
    dt_p = agora.replace(day=1) - timedelta(days=1)
    df_passado = executar_robo_erp(dt_p.month, dt_p.year)
    
    return {'atual': df_atual, 'passado': df_passado}

def desenhar_aba(dados_tme_raw, df_bruto, tecnico, mes, ano, dia_limite):
    # 1. TRATAMENTO DOS DADOS DO ERP
    df_tec = pd.DataFrame()
    if df_bruto is not None and not df_bruto.empty:
        df = df_bruto.copy()
        # Identifica coluna de data
        col_data = [c for c in df.columns if "Encerramento" in c][0]
        df['DATA_REF'] = pd.to_datetime(df[col_data], dayfirst=True, errors='coerce')
        # Identifica coluna de atendente
        possiveis_cols = ["Atendente", "Usuário Encerramento", "Responsável", "Nome"]
        col_atendente = next((c for c in possiveis_cols if c in df.columns), df.columns[3])
        # Mapeia
        df['Tec_Formatado'] = df[col_atendente].apply(lambda x: next((k for k, v in MAPEAMENTO_TECNICOS.items() if super_limpeza(v) in super_limpeza(str(x))), None))
        df_tec = df[df['Tec_Formatado'] == tecnico].dropna(subset=['DATA_REF'])

    # 2. TRATAMENTO TME (PLANILHA)
    mapa_tme = {l[0]: l[3:] for l in dados_tme_raw if len(l) > 0}
    tempos_raw = mapa_tme.get(tecnico, [""] * 31)
    
    # Cálculos de Métricas
    total_enc = len(df_tec)
    
    # Cálculo da Média de TME
    tempos_segundos = [converter_para_segundos(t) for t in tempos_raw[:dia_limite]]
    tempos_validos = [t for t in tempos_segundos if t is not None]
    media_tme_seg = sum(tempos_validos) / len(tempos_validos) if tempos_validos else 0
    tme_formatado = formatar_segundos(media_tme_seg)

    # 3. INTERFACE DE MÉTRICAS
    col1, col2, col3 = st.columns([2,1,1])
    with col1: st.markdown(f"### {tecnico}")
    with col2: st.metric("Total Encerramentos", f"{total_enc} un")
    with col3: st.metric("TME Médio (Mês)", tme_formatado)
    
    st.progress(min(total_enc/550, 1.0), text=f"Meta Normal (550): {total_enc}")
    st.progress(min(total_enc/681, 1.0), text=f"Super Meta (681): {total_enc}")
    
    st.divider()
    
    # 4. GRID DIÁRIO
    grid = st.columns(7)
    counts_diario = df_tec['DATA_REF'].dt.day.value_counts().to_dict()

    for i in range(dia_limite):
        dia = i + 1
        with grid[i % 7]:
            qtd = counts_diario.get(dia, 0)
            tme_dia = str(tempos_raw[i]).strip() if i < len(tempos_raw) else ""
            
            # Lógica de cor do TME diário
            seg_dia = converter_para_segundos(tme_dia)
            cor_tme = "#FFFFFF"
            if tme_dia in ["", "FORA"]: cor_tme = "#FFD700"
            elif seg_dia and seg_dia > 900: # Exemplo: Alerta se maior que 15 min
                cor_tme = "#FF4B4B"

            st.markdown(f"""
                <div style="background:#1d2129; padding:8px; border-radius:8px; border:1px solid #30363d; margin-bottom:8px; text-align:center;">
                    <small style="color:#8b949e;">{dia:02d}/{mes:02d}</small><br>
                    <b style="color:#4da3ff; font-size:1.1rem;">E: {qtd}</b><br>
                    <small style="color:{cor_tme};">⏱️ {tme_dia or '---'}</small>
                </div>
            """, unsafe_allow_html=True)

def render():
    apply_styles()
    st_autorefresh(interval=15 * 60 * 1000, key="refresh_perf")
    
    agora = datetime.now(pytz.timezone('America/Sao_Paulo'))
    dados_planilha = load_technical_data()
    if not dados_planilha:
        st.error("Falha ao carregar dados da Planilha Master.")
        return
    
    nomes = sorted([l[0] for l in dados_planilha if len(l) > 0 and l[0] in MAPEAMENTO_TECNICOS])
    selecionado = st.selectbox("Selecione o Técnico:", nomes)

    # Coleta
    banco = sincronizar_periodo_completo()

    tab1, tab2 = st.tabs([f"📅 Mês Atual", f"⏪ Mês Anterior"])

    with tab1:
        if banco['atual'] is None:
            st.warning("Dados do mês atual não disponíveis ou falha na coleta.")
        desenhar_aba(dados_planilha, banco['atual'], selecionado, agora.month, agora.year, agora.day)
    
    with tab2:
        dt_p = agora.replace(day=1) - timedelta(days=1)
        if banco['passado'] is None:
            st.warning("Dados do mês anterior não disponíveis.")
        desenhar_aba(dados_planilha, banco['passado'], selecionado, dt_p.month, dt_p.year, calendar.monthrange(dt_p.year, dt_p.month)[1])
