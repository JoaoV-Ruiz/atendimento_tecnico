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

# --- CONFIGURAÇÕES DE CAMINHOS (Adaptado para Nuvem/Local) ---
# No Streamlit Cloud, o caminho de download padrão costuma ser /tmp
DOWNLOAD_FOLDER = Path("/tmp/downloads")
DOWNLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

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

@st.cache_data(ttl=900, show_spinner="Sincronizando Performance ERP...")
def disparar_automacao_erp(mes, ano):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    prefs = {"download.default_directory": str(DOWNLOAD_FOLDER.absolute())}
    options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(options=options)
    try:
        driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(DOWNLOAD_FOLDER.absolute())})
        wait = WebDriverWait(driver, 45)
        
        # Login (Usando Secrets)
        driver.get("https://erp.osirnet.com.br/all_solicitations#/")
        try:
            user_field = wait.until(EC.element_to_be_clickable((By.ID, ":r0:")))
            user_field.send_keys(st.secrets["ERP_USER"])
            driver.find_element(By.ID, ":r1:").send_keys(st.secrets["ERP_PASS"])
            driver.find_element(By.XPATH, "//button[contains(., 'Entrar')]").click()
            time.sleep(5)
        except: pass

        # Navegação e Filtros (Resumido para o módulo)
        driver.get("https://erp.osirnet.com.br/all_solicitations#/")
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@tooltip='Filtro avançado']"))).click()
        time.sleep(2)

        # Seleção de Equipe
        driver.find_element(By.ID, "teamId").click()
        f_all = wait.until(EC.element_to_be_clickable((By.ID, "filterAll")))
        f_all.send_keys("COP Encerramentos")
        f_all.send_keys(Keys.ENTER)
        time.sleep(2)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@id='datagrid_row' and contains(text(), 'COP Encerramentos')]"))).click()
        driver.find_element(By.XPATH, "//button[contains(., 'Confirmar')]").click()

        # Exportação CSV
        btn_exp = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@tooltip='Imprimir/Exportar']")))
        driver.execute_script("arguments[0].click();", btn_exp)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '.CSV')]"))).click()
        
        time.sleep(25) # Tempo de download
        
        arquivos = glob.glob(os.path.join(str(DOWNLOAD_FOLDER), "*"))
        if not arquivos: return None
        recente = max(arquivos, key=os.path.getmtime)
        
        return analisar_dados_encerramentos(recente, mes, ano)
        
    except Exception as e:
        st.error(f"Erro na automação ERP: {str(e)}")
        return None
    finally:
        driver.quit()

# --- INTERFACE PRINCIPAL ---
def render():
    apply_styles()
    
    fuso_br = pytz.timezone('America/Sao_Paulo')
    hoje = datetime.now(fuso_br)
    dia_ontem = hoje.day - 1
    mes_atual = hoje.month
    ano_atual = hoje.year

    st.title("📈 Performance Unificada (TME & ERP)")
    
    # Carregamento de dados
    dados_tme = load_technical_data()
    df_erp = disparar_automacao_erp(mes_atual, ano_atual)

    if not dados_tme:
        st.warning("Aguardando dados da planilha...")
        return

    # Seleção do Técnico
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
    
    # --- MÉTRICAS ---
    st.divider()
    m1, m2, m3 = st.columns([2, 1, 1])
    with m1:
        st.subheader(selecionado)
        st.caption(f"Competência {mes_atual:02d}/{ano_atual}")
    with m2:
        st.metric("TME Médio (Mês)", tme_acumulado)
    with m3:
        st.metric("Total Encerramentos", f"{len(df_tec_erp)} un")

    # --- GRID DIÁRIO ---
    st.subheader("📅 Histórico Diário")
    counts_enc = df_tec_erp['DATA_REF'].dt.day.value_counts() if not df_tec_erp.empty else {}
    
    grid = st.columns(7)
    for i in range(dia_ontem):
        dia = i + 1
        with grid[i % 7]:
            val_tme = str(dados_ate_ontem[i]).strip()
            seg = tempos_seg[i]
            qtd = counts_enc.get(dia, 0)
            
            # Cor condicional
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
