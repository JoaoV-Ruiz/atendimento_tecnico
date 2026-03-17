import streamlit as st
import pandas as pd
import gspread
import json
import os
import re
import time
import glob
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
from pathlib import Path
from styles import apply_styles
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CONFIGURAÇÃO DE SEGREDOS COM TRATAMENTO DE ERRO ---
# Usamos .get() para evitar KeyError. Se não existir, o valor será None.
ERP_USER = st.secrets.get("ERP_USER")
ERP_PASS = st.secrets.get("ERP_PASS")
URL_PLANILHA = st.secrets.get("URL_PLANILHA")
# Verifique se nos seus Secrets o nome é GOOGLE_JSON_CREDENTIALS ou o final _2
GOOGLE_JSON = st.secrets.get("GOOGLE_JSON_CREDENTIALS_2") or st.secrets.get("GOOGLE_JSON_CREDENTIALS")

# Definição de Caminhos
BASE_DIR = Path(__file__).parent.parent
NOME_DOWNLOAD = (st.secrets.get("DOWNLOAD_PATH") or "downloads").strip("/")
DOWNLOAD_FOLDER = Path("/tmp") / NOME_DOWNLOAD
DOWNLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

URL_ERP = "https://erp.osirnet.com.br/all_solicitations#/"

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

# --- FUNÇÕES DE LOG E SUPORTE ---

def log_processo(mensagem):
    agora = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%H:%M:%S')
    print(f"[LOG PERFORMANCE {agora}] {mensagem}")

def limpar_pasta_downloads():
    arquivos = glob.glob(os.path.join(str(DOWNLOAD_FOLDER), "*"))
    for f in arquivos:
        try: os.remove(f)
        except: pass
    log_processo("🧹 Pasta temporária limpa.")

def mover_arquivo_recente():
    time.sleep(5) # Espera o buffer do sistema
    arquivos = list(DOWNLOAD_FOLDER.glob("*.csv"))
    if not arquivos: return None
    return str(max(arquivos, key=os.path.getmtime))

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

# --- PROCESSAMENTO DE DADOS ---

@st.cache_data(ttl=600)
def load_technical_data():
    if not GOOGLE_JSON or not URL_PLANILHA:
        log_processo("❌ Erro: Credenciais Google ou URL não encontradas nos Secrets.")
        return None
    try:
        creds_info = json.loads(GOOGLE_JSON)
        scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_url(URL_PLANILHA)
        sheet = spreadsheet.worksheet("AtendimentoTécnico")
        return sheet.get("A8:AF20")
    except Exception as e:
        log_processo(f"🚨 Erro Planilha: {e}")
        return None

def analisar_dados_encerramentos(caminho_csv, mes, ano):
    if not caminho_csv or not os.path.exists(caminho_csv): return None
    try:
        df = pd.read_csv(caminho_csv, sep=None, engine='python', encoding='latin-1', on_bad_lines='skip')
        col_data = [c for c in df.columns if "Encerramento" in c][0]
        df['DATA_REF'] = pd.to_datetime(df[col_data], dayfirst=True, errors='coerce')
        
        possiveis_cols = ["Atendente", "Usuário Encerramento", "Responsável", "Nome"]
        col_tec = next((c for c in possiveis_cols if c in df.columns), df.columns[3])
        
        df['Atendente_Planilha'] = df[col_tec].apply(lambda x: next((p for p, t in MAPEAMENTO_TECNICOS.items() if super_limpeza(t) in super_limpeza(str(x))), None))
        df = df.dropna(subset=['Atendente_Planilha', 'DATA_REF'])
        return df[(df['DATA_REF'].dt.month == mes) & (df['DATA_REF'].dt.year == ano)]
    except Exception as e:
        log_processo(f"🚨 Erro CSV: {e}")
        return None

@st.cache_data(ttl=1800, show_spinner="🤖 Sincronizando ERP...")
def disparar_automacao_erp(mes, ano):
    if not ERP_USER or not ERP_PASS:
        log_processo("❌ Erro: Usuário/Senha do ERP não definidos.")
        return None

    limpar_pasta_downloads()
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("prefs", {"download.default_directory": str(DOWNLOAD_FOLDER.absolute())})

    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(DOWNLOAD_FOLDER.absolute())})
        wait = WebDriverWait(driver, 60)

        # 1. Login
        log_processo("🔑 Acessando ERP...")
        driver.get(URL_ERP)
        time.sleep(5)
        
        u_f = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='text']")))
        p_f = driver.find_element(By.XPATH, "//input[@type='password']")
        driver.execute_script("arguments[0].value = arguments[1];", u_f, ERP_USER)
        driver.execute_script("arguments[0].value = arguments[1];", p_f, ERP_PASS)
        driver.execute_script("arguments[0].click();", driver.find_element(By.XPATH, "//button[contains(., 'Entrar')]"))
        
        time.sleep(12)
        driver.get(URL_ERP) # Refresh limpo
        time.sleep(6)

        # 2. Filtros e Exportação (Reduzido para estabilidade)
        log_processo("📥 Tentando Exportar CSV...")
        btn_exp = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(@tooltip, 'Exportar')]")))
        driver.execute_script("arguments[0].click();", btn_exp)
        time.sleep(2)
        driver.execute_script("arguments[0].click();", driver.find_element(By.XPATH, "//button[contains(., '.CSV')]"))
        
        # 3. Espera o Download
        caminho = None
        for _ in range(20):
            caminho = mover_arquivo_recente()
            if caminho: 
                log_processo(f"✅ Arquivo baixado: {os.path.basename(caminho)}")
                break
            time.sleep(3)
        
        return analisar_dados_encerramentos(caminho, mes, ano) if caminho else None

    except Exception as e:
        log_processo(f"🚨 Falha Selenium: {e}")
        return None
    finally:
        if driver: driver.quit()

# --- INTERFACE ---
def render():
    apply_styles()
    fuso_br = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(fuso_br)
    
    st.title("📈 Performance Unificada")

    df_erp = disparar_automacao_erp(agora.month, agora.year)
    dados_tme = load_technical_data()

    if not dados_tme:
        st.error("Não foi possível carregar os dados. Verifique os logs e os Secrets.")
        return

    lista_tecnicos = sorted([l[0] for l in dados_tme if len(l) > 0 and l[0] in MAPEAMENTO_TECNICOS])
    selecionado = st.selectbox("👤 Atendente:", options=lista_tecnicos)

    # Processamento e Exibição (Mesma lógica funcional anterior)
    mapa = {l[0]: l for l in dados_tme if len(l) > 0}
    linha = mapa[selecionado][3:]
    dia_ontem = agora.day - 1
    
    dados_grafico = [linha[i] if i < len(linha) else "" for i in range(dia_ontem)]
    tempos = [converter_para_segundos(t) for t in dados_grafico]
    validos = [s for s in tempos if s is not None]
    tme_total = formatar_segundos(sum(validos)/len(validos)) if validos else "00:00:00"

    df_tec = df_erp[df_erp['Atendente_Planilha'] == selecionado] if df_erp is not None else pd.DataFrame()

    st.divider()
    c1, c2, c3 = st.columns([2, 1, 1])
    c1.subheader(selecionado)
    c2.metric("TME Médio", tme_total)
    c3.metric("Encerramentos", f"{len(df_tec)} un")

    st.subheader("📅 Histórico")
    counts = df_tec['DATA_REF'].dt.day.value_counts().to_dict() if not df_tec.empty else {}
    
    grid = st.columns(7)
    for i in range(dia_ontem):
        dia = i + 1
        with grid[i % 7]:
            val_tme = str(dados_grafico[i]).strip()
            qtd = counts.get(dia, 0)
            cor = "#FFD700" if val_tme == "FORA" else ("#FF4B4B" if (tempos[i] or 0) > 15 else "#FFFFFF")
            st.markdown(f'<div style="background:#1d2129; padding:8px; border-radius:8px; border:1px solid #30363d; text-align:center;"><div style="color:#8b949e; font-size:0.7rem;">{dia:02d}</div><div style="font-weight:bold; color:{cor};">{val_tme or "---"}</div><div style="font-size:0.8rem; color:#4da3ff;">E:{qtd}</div></div>', unsafe_allow_html=True)
