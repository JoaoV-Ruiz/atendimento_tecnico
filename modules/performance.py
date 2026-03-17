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
# Usar /tmp é a única garantia de escrita no Streamlit Cloud
DOWNLOAD_FOLDER = Path("/tmp/downloads")
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

# --- FUNÇÕES DE AUXÍLIO ---

def mover_arquivo_recente():
    time.sleep(3)
    arquivos = list(DOWNLOAD_FOLDER.glob("*.csv"))
    if not arquivos: return None
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

@st.cache_data(ttl=3600) # Aumentado para 1 hora para evitar disparos excessivos
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
        st.error(f"Erro ao processar CSV do ERP: {e}")
        return None

@st.cache_data(ttl=1800, show_spinner="🤖 Robô acessando ERP... aguarde.")
def disparar_automacao_erp(mes, ano):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    abs_download_path = str(DOWNLOAD_FOLDER.absolute())
    prefs = {"download.default_directory": abs_download_path}
    chrome_options.add_experimental_option("prefs", prefs)

    driver = None
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Iniciando Selenium...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": abs_download_path})
        wait = WebDriverWait(driver, 60)

        # 1. LOGIN
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔑 Acessando página de login...")
        driver.get(URL_ERP)
        time.sleep(5)
        
        u_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='text']")))
        p_field = driver.find_element(By.XPATH, "//input[@type='password']")
        
        driver.execute_script("arguments[0].value = arguments[1];", u_field, st.secrets["ERP_USER"])
        driver.execute_script("arguments[0].value = arguments[1];", p_field, st.secrets["ERP_PASS"])
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📑 Inserindo credenciais...")
        btn_login = driver.find_element(By.XPATH, "//button[contains(., 'Entrar')]")
        driver.execute_script("arguments[0].click();", btn_login)
        
        time.sleep(12)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Login realizado. Redirecionando...")
        driver.get(URL_ERP)
        time.sleep(5)

        # 3. FILTROS
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 Aplicando filtros de equipe...")
        btn_filtro = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@tooltip, 'Filtro')]")))
        driver.execute_script("arguments[0].click();", btn_filtro)
        
        campo_equipe = wait.until(EC.element_to_be_clickable((By.ID, "teamId")))
        driver.execute_script("arguments[0].click();", campo_equipe)
        
        filtro_txt = wait.until(EC.element_to_be_clickable((By.ID, "filterAll")))
        filtro_txt.send_keys("COP Encerramentos")
        time.sleep(2)
        filtro_txt.send_keys(Keys.ENTER)
        
        item_lista = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'COP Encerramentos')]")))
        driver.execute_script("arguments[0].click();", item_lista)
        driver.execute_script("arguments[0].click();", driver.find_element(By.XPATH, "//button[contains(., 'Confirmar')]"))
        
        # 4. EXPORTAR
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📥 Solicitando exportação CSV...")
        btn_exp = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(@tooltip, 'Exportar')]")))
        driver.execute_script("arguments[0].click();", btn_exp)
        time.sleep(2)
        
        btn_csv = driver.find_element(By.XPATH, "//button[contains(., '.CSV')]")
        driver.execute_script("arguments[0].click();", btn_csv)
        
        # 5. MONITOR DE DOWNLOAD
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏳ Aguardando download na pasta /tmp...")
        start_time = time.time()
        caminho_final = None
        while time.time() - start_time < 50:
            caminho_final = mover_arquivo_recente()
            if caminho_final: 
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✨ Arquivo detectado: {os.path.basename(caminho_final)}")
                break
            time.sleep(3)
        
        if caminho_final:
            df = analisar_dados_encerramentos(caminho_final, mes, ano)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 📊 CSV processado com {len(df) if df is not None else 0} linhas.")
            return df
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Erro: Download não concluído.")
        return None

    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚨 ERRO CRÍTICO: {str(e)}")
        return None
    finally:
        if driver: 
            driver.quit()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🏁 Navegador encerrado.")

# --- INTERFACE PRINCIPAL ---
def render():
    apply_styles()
    fuso_br = pytz.timezone('America/Sao_Paulo')
    hoje = datetime.now(fuso_br)
    dia_ontem = hoje.day - 1
    mes_atual = hoje.month
    ano_atual = hoje.year

    st.title("📈 Performance Unificada (TME & ERP)")
    
    # Executa a automação apenas se necessário (Cache cuida disso)
    df_erp = disparar_automacao_erp(mes_atual, ano_atual)
    dados_tme = load_technical_data()

    if not dados_tme:
        st.warning("Aguardando dados da planilha TME...")
        return

    lista_tecnicos = sorted([l[0] for l in dados_tme if len(l) > 0 and l[0] in MAPEAMENTO_TECNICOS])
    selecionado = st.selectbox("👤 Selecionar Atendente:", options=lista_tecnicos)

    # Lógica de exibição
    mapa = {l[0]: l for l in dados_tme if len(l) > 0}
    linha_tecnico = mapa[selecionado][3:]
    
    dados_ate_ontem = [linha_tecnico[i] if i < len(linha_tecnico) else "" for i in range(dia_ontem)]
    tempos_seg = [converter_para_segundos(t) for t in dados_ate_ontem]
    tempos_validos = [s for s in tempos_seg if s is not None]
    
    tme_acumulado = formatar_segundos(sum(tempos_validos)/len(tempos_validos)) if tempos_validos else "00:00:00"

    # Segurança para o DataFrame
    if df_erp is not None:
        df_tec_erp = df_erp[df_erp['Atendente_Planilha'] == selecionado]
    else:
        df_tec_erp = pd.DataFrame()
    
    # Métricas
    st.divider()
    m1, m2, m3 = st.columns([2, 1, 1])
    with m1:
        st.subheader(selecionado)
        st.caption(f"Competência {mes_atual:02d}/{ano_atual}")
    with m2:
        st.metric("TME Médio (Mês)", tme_acumulado)
    with m3:
        st.metric("Total Encerramentos", f"{len(df_tec_erp)} un")

    # Grid Diário
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
