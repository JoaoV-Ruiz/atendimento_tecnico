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
        return None
    except: return None

def formatar_segundos(segundos):
    if segundos is None or segundos <= 0: return "00:00:00"
    return str(timedelta(seconds=int(segundos)))

@st.cache_data(ttl=600)
def load_technical_data():
    url = st.secrets.get("SPREADSHEET_URL")
    creds_json = st.secrets.get("GOOGLE_JSON_CREDENTIALS_2") or st.secrets.get("GOOGLE_JSON_CREDENTIALS")
    if not url or not creds_json: return None
    try:
        from google.oauth2.service_account import Credentials
        creds = Credentials.from_service_account_info(json.loads(creds_json), scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
        return gspread.authorize(creds).open_by_url(url).worksheet("AtendimentoTécnico").get("A8:AJ20")
    except: return None

# --- 3. EXPORTAÇÃO APENAS MÉDIAS ---
def preparar_csv_medias(dados_planilha):
    """Gera um CSV com Colaborador e sua Média de TME do mês"""
    try:
        lista_medias = []
        for linha in dados_planilha:
            if len(linha) > 0 and linha[0] in MAPEAMENTO_TECNICOS:
                nome = linha[0]
                tempos_raw = linha[3:]
                
                # Converte tempos válidos para segundos para calcular média
                segundos_validos = [converter_para_segundos(t) for t in tempos_raw]
                segundos_validos = [s for s in segundos_validos if s is not None]
                
                media_seg = sum(segundos_validos) / len(segundos_validos) if segundos_validos else 0
                lista_medias.append({
                    "Colaborador": nome,
                    "Média TME (Mensal)": formatar_segundos(media_seg)
                })
        
        df_medias = pd.DataFrame(lista_medias)
        return df_medias.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
    except:
        return None

# --- 4. MOTOR DE AUTOMAÇÃO ---
def executar_robo_erp(mes, ano):
    BASE_DIR = Path(__file__).parent.parent
    DOWNLOAD_FOLDER = BASE_DIR / st.secrets["DOWNLOAD_PATH"].strip("/")
    DESTINO_FOLDER = BASE_DIR / st.secrets["DESTINO_PATH"].strip("/")
    DOWNLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    DESTINO_FOLDER.mkdir(parents=True, exist_ok=True)

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
        
        inputs = driver.find_elements(By.ID, ":r0:")
        if inputs:
            inputs[0].send_keys(st.secrets["ERP_USER"])
            driver.find_element(By.ID, ":r1:").send_keys(st.secrets["ERP_PASS"])
            driver.find_element(By.XPATH, "//button[contains(., 'Entrar')]").click()
            time.sleep(8)
        
        driver.get(f"{st.secrets['URL_ERP']}#/all_solicitations")
        time.sleep(12)

        script_filtro = "var bt = document.querySelectorAll('button'); for(var b of bt){if(b.innerHTML.includes('fa-filter')){b.click(); return true;}} return false;"
        if driver.execute_script(script_filtro):
            time.sleep(5)
            wait.until(EC.presence_of_element_located((By.ID, "teamId"))).click()
            f_all = wait.until(EC.visibility_of_element_located((By.ID, "filterAll")))
            f_all.send_keys("COP Encerramentos")
            f_all.send_keys(Keys.ENTER)
            time.sleep(3)
            item = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@id='datagrid_row' and contains(text(), 'COP Encerramentos')]")))
            driver.execute_script("arguments[0].click();", item)
            driver.find_element(By.XPATH, "//button[contains(., 'Confirmar')]").click()

            hj = datetime.now()
            data_ini = f"01/{mes:02d}/{ano}"
            data_fim = hj.strftime("%d/%m/%Y") if (mes == hj.month and ano == hj.year) else f"{calendar.monthrange(ano, mes)[1]:02d}/{mes:02d}/{ano}"

            script_react = "var el = document.getElementById(arguments[0]); el.value = arguments[1]; el.dispatchEvent(new Event('input', {bubbles:true}));"
            driver.execute_script(script_react, "beginReportClosingDate", data_ini)
            driver.execute_script(script_react, "finalReportClosingDate", data_fim)
            time.sleep(2)
            driver.find_element(By.XPATH, "//button[contains(., 'aplicar')]").click()
            time.sleep(12)

            btn_exp = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@tooltip='Imprimir/Exportar']")))
            driver.execute_script("arguments[0].click();", btn_exp)
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '.CSV')]"))).click()
            
            for _ in range(40):
                arquivos = glob.glob(os.path.join(abs_path, "*.csv"))
                if arquivos and not any(f.endswith('.crdownload') for f in arquivos):
                    recente = max(arquivos, key=os.path.getmtime)
                    dest = DESTINO_FOLDER / f"perf_{mes}_{ano}.csv"
                    shutil.move(recente, str(dest))
                    return pd.read_csv(str(dest), sep=None, engine='python', encoding='latin-1')
                time.sleep(2)
        return None
    except: return None
    finally: driver.quit()

@st.cache_data(ttl=900, show_spinner="🤖 Sincronizando Período Completo...")
def sincronizar_periodo_completo():
    fuso = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(fuso)
    dt_p = agora.replace(day=1) - timedelta(days=1)
    banco = {}
    banco['passado'] = executar_robo_erp(dt_p.month, dt_p.year)
    banco['atual'] = executar_robo_erp(agora.month, agora.year)
    return banco

# --- 5. INTERFACE ---
def desenhar_aba(dados_tme_raw, df_bruto, tecnico_sel, mes, ano, dia_limite):
    df_tec = pd.DataFrame(columns=['DATA_REF', 'Tec_Formatado'])
    if df_bruto is not None and not df_bruto.empty:
        df = df_bruto.copy()
        col_data = [c for c in df.columns if "Encerramento" in c][0]
        df['DATA_REF'] = pd.to_datetime(df[col_data], dayfirst=True, errors='coerce')
        possiveis_cols = ["Atendente", "Usuário Encerramento", "Responsável", "Nome"]
        col_atendente = next((c for c in possiveis_cols if c in df.columns), df.columns[3])
        df['Tec_Formatado'] = df[col_atendente].apply(lambda x: next((p_nome for p_nome, erp_nome in MAPEAMENTO_TECNICOS.items() if super_limpeza(erp_nome) in super_limpeza(str(x))), None))
        df_tec = df[df['Tec_Formatado'] == tecnico_sel].dropna(subset=['DATA_REF'])

    mapa_tme = {l[0]: l[3:] for l in dados_tme_raw if len(l) > 0}
    tempos_raw = mapa_tme.get(tecnico_sel, [])
    while len(tempos_raw) < 31: tempos_raw.append("") 

    total_enc = len(df_tec)
    tempos_seg = [converter_para_segundos(t) for t in tempos_raw[:dia_limite]]
    validos = [t for t in tempos_seg if t is not None]
    media_seg = sum(validos) / len(validos) if validos else 0
    
    c1, c2, c3 = st.columns([2,1,1])
    with c1: st.subheader(f"👤 {tecnico_sel}")
    with c2: st.metric("Total Encerramentos", f"{total_enc} un")
    with c3: st.metric("TME Médio (Mês)", formatar_segundos(media_seg))
    
    st.progress(min(total_enc/550, 1.0), text=f"Meta Normal (550): {total_enc}")
    st.progress(min(total_enc/681, 1.0), text=f"Super Meta (681): {total_enc}")
    
    st.divider()
    grid = st.columns(7)
    counts = df_tec['DATA_REF'].dt.day.value_counts().to_dict() if not df_tec.empty else {}

    for i in range(dia_limite):
        dia = i + 1
        with grid[i % 7]:
            qtd = counts.get(dia, 0)
            tme_dia = str(tempos_raw[i]).strip() if i < len(tempos_raw) else ""
            cor = "#FFFFFF"
            if tme_dia in ["", "FORA"]: cor = "#FFD700"; tme_dia = "FORA"
            elif converter_para_segundos(tme_dia) and converter_para_segundos(tme_dia) > 900: cor = "#FF4B4B"

            st.markdown(f"""
                <div style="background:#1d2129; padding:8px; border-radius:8px; border:1px solid #30363d; margin-bottom:8px; text-align:center;">
                    <small style="color:#8b949e;">{dia:02d}/{mes:02d}</small><br>
                    <b style="color:#4da3ff; font-size:1.1rem;">E: {qtd}</b><br>
                    <small style="color:{cor};">⏱️ {tme_dia or '---'}</small>
                </div>
            """, unsafe_allow_html=True)

def render():
    apply_styles()
    st_autorefresh(interval=15 * 60 * 1000, key="refresh_perf")
    fuso = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(fuso)
    
    dados_planilha = load_technical_data()
    if not dados_planilha: return
    
    nomes = sorted([l[0] for l in dados_planilha if len(l) > 0 and l[0] in MAPEAMENTO_TECNICOS])
    
    # --- CABEÇALHO COM BOTÃO DE MÉDIAS ---
    st.markdown("### 📈 Painel de Performance")
    
    col_sel, col_exp = st.columns([3, 1])
    
    with col_sel:
        selecionado = st.selectbox("Selecione o Técnico:", nomes, label_visibility="collapsed")
    
    with col_exp:
        csv_data = preparar_csv_medias(dados_planilha)
        if csv_data:
            st.download_button(
                label="📥 Baixar Médias TME (.csv)",
                data=csv_data,
                file_name=f"medias_tme_equipe_{agora.strftime('%m_%Y')}.csv",
                mime="text/csv",
                use_container_width=True
            )

    banco = sincronizar_periodo_completo()
    tab1, tab2 = st.tabs([f"📅 Mês Atual", f"⏪ Mês Anterior"])

    with tab1:
        desenhar_aba(dados_planilha, banco['atual'], selecionado, agora.month, agora.year, agora.day)
    
    with tab2:
        dt_p = agora.replace(day=1) - timedelta(days=1)
        desenhar_aba(dados_planilha, banco['passado'], selecionado, dt_p.month, dt_p.year, calendar.monthrange(dt_p.year, dt_p.month)[1])
