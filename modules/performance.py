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

# --- 2. FUNÇÕES DE APOIO ---
def super_limpeza(texto):
    if not isinstance(texto, str): return ""
    texto = texto.upper()
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

def analisar_dados_csv(caminho_csv, mes, ano):
    if not caminho_csv or not os.path.exists(caminho_csv): return None
    try:
        df = pd.read_csv(caminho_csv, sep=None, engine='python', encoding='latin-1', on_bad_lines='skip')
        col_data = [c for c in df.columns if "Encerramento" in c][0]
        df['DATA_REF'] = pd.to_datetime(df[col_data], dayfirst=True, errors='coerce')
        
        possiveis_cols = ["Atendente", "Usuário Encerramento", "Responsável"]
        col_tec = next((c for c in possiveis_cols if c in df.columns), df.columns[3])
        
        # Mapeamento reverso para bater com os nomes da planilha
        df['Atendente_Planilha'] = df[col_tec].apply(lambda x: next((k for k, v in MAPEAMENTO_TECNICOS.items() if super_limpeza(v) in super_limpeza(str(x))), None))
        
        return df[(df['DATA_REF'].dt.month == mes) & (df['DATA_REF'].dt.year == ano)].dropna(subset=['Atendente_Planilha'])
    except: return None

# --- 3. AUTOMAÇÃO ERP ---
@st.cache_data(ttl=900, show_spinner="Sincronizando com ERP...")
def disparar_automacao_erp(mes, ano):
    BASE_DIR = Path(__file__).parent.parent
    DOWNLOAD_FOLDER = BASE_DIR / "temp_downloads"
    DESTINO_FOLDER = BASE_DIR / "data_storage"
    DOWNLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    DESTINO_FOLDER.mkdir(parents=True, exist_ok=True)

    # Limpeza prévia para evitar pegar arquivo errado
    for f in glob.glob(str(DOWNLOAD_FOLDER / "*")):
        try: os.remove(f)
        except: pass

    chrome_options = Options()
    chrome_options.add_argument("--headless=new") # Modo headless atualizado
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    prefs = {
        "download.default_directory": str(DOWNLOAD_FOLDER.absolute()),
        "download.prompt_for_download": False,
        "directory_upgrade": True
    }
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(DOWNLOAD_FOLDER.absolute())})
    
    try:
        wait = WebDriverWait(driver, 30)
        
        # 1. ACESSO E LOGIN
        driver.get("https://erp.osirnet.com.br/all_solicitations#/")
        time.sleep(5)
        
        # Verifica se caiu na tela de login
        inputs_login = driver.find_elements(By.ID, ":r0:")
        if inputs_login:
            inputs_login[0].send_keys(st.secrets["ERP_USER"])
            driver.find_element(By.ID, ":r1:").send_keys(st.secrets["ERP_PASS"])
            driver.find_element(By.XPATH, "//button[contains(., 'Entrar')]").click()
            time.sleep(7)

        # 2. SELEÇÃO DA TELA ANTIGA (Se necessário)
        try:
            btn_ant = driver.find_elements(By.XPATH, "//button[@aria-label='Tela antiga']")
            if btn_ant:
                driver.execute_script("arguments[0].click();", btn_ant[0])
                time.sleep(5)
        except: pass

        # 3. FILTROS DIRETOS
        # Forçamos a ida para a URL de solicitações para limpar estados anteriores
        driver.get("https://erp.osirnet.com.br/all_solicitations#/")
        time.sleep(5)
        
        filtro_avancado = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@tooltip='Filtro avançado']")))
        driver.execute_script("arguments[0].click();", filtro_avancado)
        time.sleep(3)

        # Seleção de Equipe (COP Encerramentos)
        campo_equipe = wait.until(EC.element_to_be_clickable((By.ID, "teamId")))
        campo_equipe.click()
        time.sleep(2)
        
        filtro_txt = wait.until(EC.visibility_of_element_located((By.ID, "filterAll")))
        filtro_txt.send_keys("COP Encerramentos")
        time.sleep(2)
        filtro_txt.send_keys(Keys.ENTER)
        time.sleep(3)
        
        item_equipe = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@id='datagrid_row' and contains(text(), 'COP Encerramentos')]")))
        driver.execute_script("arguments[0].click();", item_equipe)
        time.sleep(1)
        driver.find_element(By.XPATH, "//button[contains(., 'Confirmar')]").click()
        time.sleep(2)

        # DATAS
        hj = datetime.now()
        data_ini = f"01/{mes:02d}/{ano}"
        data_fim = hj.strftime("%d/%m/%Y") if (mes == hj.month and ano == hj.year) else f"{calendar.monthrange(ano, mes)[1]:02d}/{mes:02d}/{ano}"

        def set_react_val(field_id, value):
            script = "var el = document.getElementById(arguments[0]); el.value = arguments[1]; el.dispatchEvent(new Event('input', {bubbles:true})); el.dispatchEvent(new Event('change', {bubbles:true}));"
            driver.execute_script(script, field_id, value)

        set_react_val("beginReportClosingDate", data_ini)
        set_react_val("finalReportClosingDate", data_fim)
        time.sleep(2)
        
        driver.find_element(By.XPATH, "//button[contains(., 'aplicar')]").click()
        
        # 4. EXPORTAÇÃO (O ponto onde mais ocorre erro)
        status_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@tooltip='Imprimir/Exportar']")))
        time.sleep(10) # Aguarda o grid carregar os dados antes de exportar
        driver.execute_script("arguments[0].click();", status_btn)
        
        btn_csv = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '.CSV')]")))
        driver.execute_script("arguments[0].click();", btn_csv)

        # 5. MONITORAMENTO DO DOWNLOAD
        caminho_final = None
        for _ in range(45): # Até 45 segundos de espera
            arquivos = glob.glob(str(DOWNLOAD_FOLDER / "*.csv"))
            if arquivos:
                recente = max(arquivos, key=os.path.getmtime)
                # Verifica se não é um arquivo temporário (.crdownload)
                if not recente.endswith('.crdownload'):
                    nome_arq = os.path.basename(recente)
                    caminho_destino = DESTINO_FOLDER / nome_arq
                    shutil.move(recente, str(caminho_destino))
                    caminho_final = str(caminho_destino)
                    break
            time.sleep(2)

        if caminho_final:
            return analisar_dados_csv(caminho_final, mes, ano)
        return None

    except Exception as e:
        # Imprime o erro real no console para debug
        print(f"DEBUG: Erro no Selenium: {str(e)}")
        raise e # Repassa o erro para o Streamlit mostrar na tela
    finally:
        driver.quit()

# --- 4. RENDERIZAÇÃO DA INTERFACE ---
def desenhar_conteudo(dados_tme, df_erp, tecnico, mes, ano, dia_limite):
    df_tec = df_erp[df_erp['Atendente_Planilha'] == tecnico] if df_erp is not None else pd.DataFrame()
    total = len(df_tec)
    
    # Métricas
    c1, c2, c3 = st.columns([2,1,1])
    with c1: st.markdown(f"#### {tecnico}")
    with col2: st.metric("Total Encerramentos", f"{total} un")
    
    st.progress(min(total/550, 1.0), text=f"Meta Normal: {total}/550")
    st.progress(min(total/681, 1.0), text=f"Super Meta: {total}/681")
    
    st.divider()
    
    # Grid de Histórico
    grid = st.columns(7)
    counts = df_tec['DATA_REF'].dt.day.value_counts().to_dict() if not df_tec.empty else {}
    mapa_tme = {l[0]: l[3:] for l in dados_tme if len(l) > 0}
    tempos_tecnico = mapa_tme.get(tecnico, [""] * 31)

    for i in range(dia_limite):
        dia = i + 1
        with grid[i % 7]:
            qtd = counts.get(dia, 0)
            val_tme = str(tempos_tecnico[i]).strip() if i < len(tempos_tecnico) else ""
            
            # Cor do TME
            cor = "#FFFFFF"
            if val_tme in ["", "FORA"]: cor = "#FFD700"
            elif converter_para_segundos(val_tme) and converter_para_segundos(val_tme) > 15: cor = "#FF4B4B"

            st.markdown(f"""
                <div style="background:#1d2129; padding:8px; border-radius:8px; border:1px solid #30363d; margin-bottom:8px; text-align:center;">
                    <small>{dia:02d}/{mes:02d}</small><br>
                    <b style="color:#4da3ff;">E: {qtd}</b><br>
                    <small style="color:{cor};">⏱️ {val_tme or '---'}</small>
                </div>
            """, unsafe_allow_html=True)

def render():
    apply_styles()
    st_autorefresh(interval=10 * 60 * 1000, key="auto_refresh_perf_v2")
    
    fuso = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(fuso)
    m_atual, a_atual = agora.month, agora.year
    
    # Data Mês Anterior
    dt_passado = agora.replace(day=1) - timedelta(days=1)
    m_pass, a_pass = dt_passado.month, dt_passado.year

    # 1. Carrega Planilha (TME)
    dados_planilha = load_technical_data()
    if not dados_planilha: return
    
    tecnicos = sorted([l[0] for l in dados_planilha if len(l) > 0 and l[0] in MAPEAMENTO_TECNICOS])
    selecionado = st.selectbox("Selecione o Técnico:", tecnicos)
    
    # 2. Abas
    tab1, tab2 = st.tabs([f"📅 {m_atual:02d}/{a_atual}", f"⏪ {m_pass:02d}/{a_pass}"])
    
    with tab1:
        df_atual = disparar_automacao_erp(m_atual, a_atual)
        desenhar_conteudo(dados_planilha, df_atual, selecionado, m_atual, a_atual, agora.day - 1)

    with tab2:
        df_passado = disparar_automacao_erp(m_pass, a_pass)
        ultimo_dia = calendar.monthrange(a_pass, m_pass)[1]
        desenhar_conteudo(dados_planilha, df_passado, selecionado, m_pass, a_pass, ultimo_dia)
