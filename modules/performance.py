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
from datetime import timedelta, datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from streamlit_autorefresh import st_autorefresh
from pathlib import Path
from styles import apply_styles

# --- 1. MAPEAMENTO DE NOMES ---
MAPEAMENTO_TECNICOS = {
    "Alisson Do Couto Guerreiro": "ALISSON DO COUTO GUERREIRO",
    "Caio Alves dos Reis": "CAIO REIS",
    "Cristiano Weber Marques": "CRISTIANO WEBER MARQUES",
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

# --- 2. FUNÇÕES DE SUPORTE ---
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
    url = st.secrets.get("URL_PLANILHA")
    creds_json_str = st.secrets.get("GOOGLE_JSON_CREDENTIALS_2") or st.secrets.get("GOOGLE_JSON_CREDENTIALS")
    
    if not url or not creds_json_str:
        st.error("Credenciais não encontradas nos Secrets.")
        return None
    try:
        from google.oauth2.service_account import Credentials
        scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds_dict = json.loads(creds_json_str)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_url(url)
        sheet = spreadsheet.worksheet("AtendimentoTécnico")
        return sheet.get("A8:AF20")
    except Exception as e:
        st.error(f"Erro Planilha: {e}")
        return None

def analisar_dados_encerramentos(caminho_csv, mes, ano):
    if not caminho_csv or not os.path.exists(caminho_csv): return None
    try:
        df = pd.read_csv(caminho_csv, sep=None, engine='python', encoding='latin-1', on_bad_lines='skip')
        col_data = [c for c in df.columns if "Encerramento" in c][0]
        df['DATA_REF'] = pd.to_datetime(df[col_data], dayfirst=True, errors='coerce')
        
        possiveis_cols = ["Atendente", "Usuário Encerramento", "Responsável", "Nome"]
        col_tec = next((c for c in possiveis_cols if c in df.columns), df.columns[3])
        
        df['Atendente_Planilha'] = df[col_tec].apply(lambda x: next((k for k, v in MAPEAMENTO_TECNICOS.items() if super_limpeza(v) in super_limpeza(str(x))), None))
        df = df.dropna(subset=['Atendente_Planilha', 'DATA_REF'])
        return df[(df['DATA_REF'].dt.month == mes) & (df['DATA_REF'].dt.year == ano)]
    except Exception as e:
        st.error(f"Erro CSV: {e}")
        return None

@st.cache_data(ttl=900, show_spinner="Sincronizando com ERP...")
def disparar_automacao_erp(download_path_obj, mes, ano):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    def forcar_input_react(driver, elemento, valor):
        script = """
        var element = arguments[0]; var value = arguments[1]; var lastValue = element.value;
        element.value = value; var event = new Event('input', { bubbles: true });
        var tracker = element._valueTracker; if (tracker) { tracker.setValue(lastValue); }
        element.dispatchEvent(event); element.dispatchEvent(new Event('change', { bubbles: true }));
        """
        driver.execute_script(script, elemento, valor)

    # Limpeza da pasta
    for f in glob.glob(os.path.join(str(download_path_obj), "*")):
        try: os.remove(f)
        except: pass

    prefs = {"download.default_directory": str(download_path_obj.absolute())}
    chrome_options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(download_path_obj.absolute())})
        wait = WebDriverWait(driver, 40) 

        # 1. Login
        driver.get("https://erp.osirnet.com.br/all_solicitations#/")
        try:
            user_field = wait.until(EC.element_to_be_clickable((By.ID, ":r0:")))
            user_field.send_keys(st.secrets["ERP_USER"])
            driver.find_element(By.ID, ":r1:").send_keys(st.secrets["ERP_PASS"])
            driver.find_element(By.XPATH, "//button[contains(., 'Entrar')]").click()
            time.sleep(5)
        except: pass
        
        try:
            btn_ant = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Tela antiga']")))
            driver.execute_script("arguments[0].click();", btn_ant)
            time.sleep(3)
        except: pass
        
        # 3. Filtros
        driver.get("https://erp.osirnet.com.br/all_solicitations#/")
        time.sleep(3)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@tooltip='Filtro avançado']"))).click()
        time.sleep(3)

        driver.find_element(By.ID, "teamId").click()
        time.sleep(1)
        f_all = wait.until(EC.element_to_be_clickable((By.ID, "filterAll")))
        f_all.send_keys("COP Encerramentos")
        f_all.send_keys(Keys.ENTER)
        time.sleep(3)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@id='datagrid_row' and contains(text(), 'COP Encerramentos')]"))).click()
        time.sleep(1)
        driver.find_element(By.XPATH, "//button[contains(., 'Confirmar')]").click()

        driver.execute_script("""
            ['beginInitialDate', 'endInitialDate'].forEach(id => {
                var el = document.getElementById(id);
                if(el) { el.focus(); el.value = ''; el.dispatchEvent(new Event('input', {bubbles:true})); el.blur(); }
            });
        """)

        hj = datetime.now()
        fim = hj.replace(day=calendar.monthrange(hj.year, hj.month)[1]).strftime("%d/%m/%Y")
        forcar_input_react(driver, driver.find_element(By.ID, "finalReportClosingDate"), fim)
        time.sleep(2)
        driver.find_element(By.XPATH, "//button[contains(., 'aplicar')]").click()
        time.sleep(8)
        
        # 4. Exportar
        btn_exp = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@tooltip='Imprimir/Exportar']")))
        driver.execute_script("arguments[0].click();", btn_exp)
        
        btn_csv = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '.CSV')]")))
        btn_csv.click()
        
        # Aguarda download
        caminho_final = None
        for _ in range(30):
            arquivos = glob.glob(os.path.join(str(download_path_obj), "*.csv"))
            if arquivos:
                caminho_final = max(arquivos, key=os.path.getmtime)
                break
            time.sleep(2)
            
        return analisar_dados_encerramentos(caminho_final, mes, ano)
        
    except Exception as e:
        st.error(f"Erro na automação: {str(e)}")
        return None
    finally:
        if driver: driver.quit()

# --- 3. INTERFACE PRINCIPAL ---
def render():
    apply_styles()
    st_autorefresh(interval=10 * 60 * 1000, key="refresh_perf_unificada")
    
    # Configurações de tempo dentro do render
    fuso_br = pytz.timezone('America/Sao_Paulo')
    hoje = datetime.now(fuso_br)
    dia_ontem = hoje.day - 1
    mes_atual = hoje.month
    ano_atual = hoje.year

    # Pastas dentro do render
    base_dir = Path(__file__).parent.parent
    download_folder = base_dir / "temp_downloads"
    download_folder.mkdir(parents=True, exist_ok=True)

    dados_tme_brutos = load_technical_data()
    if not dados_tme_brutos:
        st.warning("Aguardando base de dados da Planilha...")
        return

    lista_nomes_planilha = sorted([l[0] for l in dados_tme_brutos if len(l) > 0 and l[0] in MAPEAMENTO_TECNICOS])
    
    st.markdown("### 👤 Selecione o Atendente")
    selecionado = st.selectbox("Escolha um nome:", options=lista_nomes_planilha, label_visibility="collapsed")
    
    # Automação
    df_erp = disparar_automacao_erp(download_folder, mes_atual, ano_atual)

    # Tratamento TME
    mapa = {l[0]: l for l in dados_tme_brutos if len(l) > 0}
    linha_tecnico = mapa[selecionado]
    dados_tecnico_raw = linha_tecnico[3:]
    
    dados_ate_ontem = [dados_tecnico_raw[i] if i < len(dados_tecnico_raw) else "" for i in range(dia_ontem)]
    tempos_seg = [converter_para_segundos(t) for t in dados_ate_ontem]
    tempos_validos = [s for s in tempos_seg if s is not None]
    
    tme_acumulado = formatar_segundos(sum(tempos_validos)/len(tempos_validos)) if tempos_validos else "00:00:00"

    # Tratamento ERP
    df_tec_erp = df_erp[df_erp['Atendente_Planilha'] == selecionado] if df_erp is not None else pd.DataFrame()
    
    # --- MÉTRICAS ---
    st.divider()
    col_n, col_m1, col_m2 = st.columns([2, 1, 1])
    with col_n:
        st.markdown(f"<h2 style='margin:0;'>{selecionado}</h2>", unsafe_allow_html=True)
        st.caption(f"Performance referente ao mês {mes_atual:02d}/{ano_atual}")
    with col_m1:
        st.metric("TME Acumulado", tme_acumulado)
    with col_m2:
        st.metric("Total Encerramentos", f"{len(df_tec_erp)} un")

    # --- HISTÓRICO DIÁRIO ---
    st.subheader("📅 Histórico Diário")
    grid = st.columns(7)
    counts_enc = df_tec_erp['DATA_REF'].dt.day.value_counts().to_dict() if not df_tec_erp.empty else {}

    for i in range(dia_ontem):
        dia = i + 1
        with grid[i % 7]:
            val_tme = str(dados_ate_ontem[i]).strip()
            seg = tempos_seg[i]
            qtd = counts_enc.get(dia, 0)
            
            # REGRA CORES
            cor_tme = "#FFFFFF"
            display_tme = val_tme
            if val_tme in ["", "FORA"]:
                cor_tme = "#FFD700"
                display_tme = "FORA"
            elif seg is not None and seg > 15:
                cor_tme = "#FF4B4B"

            st.markdown(f"""
                <div style="background:#1d2129; padding:12px; border-radius:10px; border:1px solid #30363d; margin-bottom:12px; text-align:center;">
                    <div style="color:#8b949e; font-size:0.8rem; margin-bottom:5px;">{dia:02d}/{mes_atual:02d}</div>
                    <div style="font-size:1.1rem; font-weight:bold; color:{cor_tme};">⏱️ {display_tme}</div>
                    <div style="font-size:1.1rem; font-weight:bold; color:#4da3ff; margin-top:5px; border-top: 1px solid #30363d; padding-top:5px;">ENC: {qtd}</div>
                </div>
            """, unsafe_allow_html=True)
