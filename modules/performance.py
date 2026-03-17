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

# --- 1. CONFIGURAÇÃO DE CAMINHOS ---
# Usamos /tmp para garantir permissão de escrita no Streamlit Cloud
DOWNLOAD_FOLDER = Path("/tmp/performance_downloads")
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

# --- FUNÇÕES DE AUXÍLIO E LOG ---

def log_processo(mensagem):
    """Imprime no console do Streamlit Cloud (Manage App > Logs)"""
    agora = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%H:%M:%S')
    print(f"[ROBÔ ERP {agora}] {mensagem}")

def limpar_pasta_downloads():
    """Remove arquivos antigos para não processar CSV errado"""
    arquivos = glob.glob(os.path.join(str(DOWNLOAD_FOLDER), "*"))
    for f in arquivos:
        try: os.remove(f)
        except: pass
    log_processo("🧹 Pasta temporária limpa.")

def mover_arquivo_recente():
    """Busca o arquivo CSV recém baixado"""
    time.sleep(4)
    arquivos = list(DOWNLOAD_FOLDER.glob("*.csv"))
    if not arquivos: 
        return None
    # Pega o arquivo com a data de modificação mais recente
    arquivo_recente = max(arquivos, key=os.path.getmtime)
    return str(arquivo_recente)

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

# --- COLETA DE DADOS ---

@st.cache_data(ttl=600)
def load_technical_data():
    try:
        creds_info = json.loads(st.secrets["GOOGLE_JSON_CREDENTIALS_2"])
        scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_url(st.secrets["URL_PLANILHA"])
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
        
        def vincular_nome_planilha(nome_erp):
            nome_erp_limpo = super_limpeza(str(nome_erp))
            for nome_planilha, termo_busca in MAPEAMENTO_TECNICOS.items():
                if super_limpeza(termo_busca) in nome_erp_limpo:
                    return nome_planilha
            return None

        df['Atendente_Planilha'] = df[col_tec].apply(vincular_nome_planilha)
        df = df.dropna(subset=['Atendente_Planilha', 'DATA_REF'])
        return df[(df['DATA_REF'].dt.month == mes) & (df['DATA_REF'].dt.year == ano)]
    except Exception as e:
        log_processo(f"🚨 Erro Processamento CSV: {e}")
        return None

@st.cache_data(ttl=1800, show_spinner="🤖 Robô sincronizando ERP... acompanhe nos logs.")
def disparar_automacao_erp(mes, ano):
    limpar_pasta_downloads()
    
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    prefs = {"download.default_directory": str(DOWNLOAD_FOLDER.absolute())}
    options.add_experimental_option("prefs", prefs)

    driver = None
    try:
        log_processo("🌐 Abrindo Chrome Headless...")
        driver = webdriver.Chrome(options=options)
        driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(DOWNLOAD_FOLDER.absolute())})
        wait = WebDriverWait(driver, 60)

        # 1. Login
        log_processo(f"🔗 Acessando {URL_ERP}")
        driver.get(URL_ERP)
        time.sleep(6)
        
        log_processo("🔑 Realizando Login...")
        u_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='text']")))
        p_field = driver.find_element(By.XPATH, "//input[@type='password']")
        
        driver.execute_script("arguments[0].value = arguments[1];", u_field, st.secrets["ERP_USER"])
        driver.execute_script("arguments[0].value = arguments[1];", p_field, st.secrets["ERP_PASS"])
        driver.execute_script("arguments[0].click();", driver.find_element(By.XPATH, "//button[contains(., 'Entrar')]"))
        
        time.sleep(12)
        log_processo("🔓 Login concluído. Acessando filtros...")
        driver.get(URL_ERP)
        time.sleep(6)

        # 2. Filtros
        log_processo("🔍 Aplicando filtros de equipe (COP Encerramentos)...")
        btn_filtro = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@tooltip, 'Filtro')]")))
        driver.execute_script("arguments[0].click();", btn_filtro)
        
        campo_equipe = wait.until(EC.element_to_be_clickable((By.ID, "teamId")))
        driver.execute_script("arguments[0].click();", campo_equipe)
        
        f_txt = wait.until(EC.element_to_be_clickable((By.ID, "filterAll")))
        f_txt.send_keys("COP Encerramentos")
        time.sleep(2)
        f_txt.send_keys(Keys.ENTER)
        
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'COP Encerramentos')]")))
        driver.execute_script("arguments[0].click();", driver.find_element(By.XPATH, "//div[contains(text(), 'COP Encerramentos')]"))
        driver.execute_script("arguments[0].click();", driver.find_element(By.XPATH, "//button[contains(., 'Confirmar')]"))
        time.sleep(3)

        # 3. Exportar
        log_processo("📥 Clicando em Exportar .CSV...")
        btn_exp = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(@tooltip, 'Exportar')]")))
        driver.execute_script("arguments[0].click();", btn_exp)
        time.sleep(2)
        driver.execute_script("arguments[0].click();", driver.find_element(By.XPATH, "//button[contains(., '.CSV')]"))
        
        # 4. Monitoramento
        log_processo("⏳ Aguardando arquivo na pasta /tmp...")
        caminho_csv = None
        for i in range(25): # Tenta por 50 segundos
            caminho_csv = mover_arquivo_recente()
            if caminho_csv:
                log_processo(f"📄 Sucesso! Arquivo encontrado: {os.path.basename(caminho_csv)}")
                break
            time.sleep(2)
        
        if caminho_csv:
            return analisar_dados_encerramentos(caminho_csv, mes, ano)
        
        log_processo("❌ Falha: Arquivo não foi baixado.")
        return None

    except Exception as e:
        log_processo(f"🚨 ERRO NA AUTOMAÇÃO: {e}")
        return None
    finally:
        if driver: driver.quit()

# --- INTERFACE ---
def render():
    apply_styles()
    fuso_br = pytz.timezone('America/Sao_Paulo')
    hoje = datetime.now(fuso_br)
    dia_ontem = hoje.day - 1
    mes_atual = hoje.month
    ano_atual = hoje.year

    st.title("📈 Performance Unificada (TME & ERP)")
    
    # Debug visual opcional (descomente se quiser ver na tela)
    # st.sidebar.write(f"Arquivos em /tmp: {os.listdir(str(DOWNLOAD_FOLDER))}")

    df_erp = disparar_automacao_erp(mes_atual, ano_atual)
    dados_tme = load_technical_data()

    if not dados_tme:
        st.warning("Carregando base de dados TME...")
        return

    lista_tecnicos = sorted([l[0] for l in dados_tme if len(l) > 0 and l[0] in MAPEAMENTO_TECNICOS])
    selecionado = st.selectbox("👤 Selecionar Atendente:", options=lista_tecnicos)

    # Processamento TME
    mapa = {l[0]: l for l in dados_tme if len(l) > 0}
    linha_tecnico = mapa[selecionado][3:]
    dados_ate_ontem = [linha_tecnico[i] if i < len(linha_tecnico) else "" for i in range(dia_ontem)]
    tempos_seg = [converter_para_segundos(t) for t in dados_ate_ontem]
    tempos_validos = [s for s in tempos_seg if s is not None]
    tme_acumulado = formatar_segundos(sum(tempos_validos)/len(tempos_validos)) if tempos_validos else "00:00:00"

    # Processamento ERP
    df_tec_erp = df_erp[df_erp['Atendente_Planilha'] == selecionado] if df_erp is not None else pd.DataFrame()
    
    # Exibição
    st.divider()
    m1, m2, m3 = st.columns([2, 1, 1])
    with m1:
        st.subheader(selecionado)
        st.caption(f"Competência {mes_atual:02d}/{ano_atual}")
    with m2:
        st.metric("TME Médio (Mês)", tme_acumulado)
    with m3:
        st.metric("Total Encerramentos", f"{len(df_tec_erp)} un")

    st.subheader("📅 Histórico Diário")
    counts_enc = df_tec_erp['DATA_REF'].dt.day.value_counts().to_dict() if not df_tec_erp.empty else {}

    grid = st.columns(7)
    for i in range(dia_ontem):
        dia = i + 1
        with grid[i % 7]:
            val_tme = str(dados_ate_ontem[i]).strip()
            seg = tempos_seg[i]
            qtd = counts_enc.get(dia, 0)
            cor_tme = "#FFFFFF"
            if val_tme in ["", "FORA"]: cor_tme = "#FFD700"
            elif seg is not None and seg > 15: cor_tme = "#FF4B4B"

            st.markdown(f"""
                <div style="background:#1d2129; padding:10px; border-radius:10px; border:1px solid #30363d; margin-bottom:10px; text-align:center;">
                    <div style="color:#8b949e; font-size:0.8rem;">{dia:02d}/{mes_atual:02d}</div>
                    <div style="font-size:1.1rem; font-weight:bold; color:{cor_tme};">⏱️ {val_tme if val_tme else '---'}</div>
                    <div style="font-size:0.9rem; color:#4da3ff;">ENC: {qtd}</div>
                </div>
            """, unsafe_allow_html=True)
