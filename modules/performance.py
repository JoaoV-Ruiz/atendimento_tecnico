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

# --- 1. CONFIGURAÇÕES TÉCNICAS E GLOBAIS ---
st.set_page_config(page_title="Performance Unificada TME & ERP", layout="wide")
apply_styles()

fuso_br = pytz.timezone('America/Sao_Paulo')
hoje_global = datetime.now(fuso_br)
DIA_ONTEM = hoje_global.day - 1
MES_ATUAL_NUM = hoje_global.month
ANO_ATUAL_NUM = hoje_global.year

# No servidor, usamos pastas temporárias dentro do diretório do projeto
BASE_DIR = Path(__file__).parent
DOWNLOAD_FOLDER = BASE_DIR / "temp_downloads"
DOWNLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

# --- 2. MAPEAMENTO DE NOMES ---
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

# --- 3. FUNÇÕES DE SUPORTE ---
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

# --- 4. CARREGAMENTO E AUTOMAÇÃO ---

@st.cache_data(ttl=600)
def load_technical_data():
    # No Streamlit Cloud, use st.secrets em vez de .env
    url = st.secrets.get("URL_PLANILHA")
    creds_json_str = st.secrets.get("GOOGLE_JSON_CREDENTIALS_2")
    
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

def analisar_dados_encerramentos(caminho_csv):
    if not caminho_csv or not os.path.exists(caminho_csv): return None
    try:
        df = pd.read_csv(caminho_csv, sep=None, engine='python', encoding='latin-1', on_bad_lines='skip')
        col_data = [c for c in df.columns if "Encerramento" in c][0]
        df['DATA_REF'] = pd.to_datetime(df[col_data], dayfirst=True, errors='coerce')
        
        possiveis_cols = ["Atendente", "Usuário Encerramento", "Responsável", "Nome"]
        col_tec = next((c for c in possiveis_cols if c in df.columns), df.columns[3])
        
        df['Atendente_Planilha'] = df[col_tec].apply(lambda x: next((k for k, v in MAPEAMENTO_TECNICOS.items() if super_limpeza(v) in super_limpeza(str(x))), None))
        df = df.dropna(subset=['Atendente_Planilha', 'DATA_REF'])
        return df[(df['DATA_REF'].dt.month == MES_ATUAL_NUM) & (df['DATA_REF'].dt.year == ANO_ATUAL_NUM)]
    except Exception as e:
        st.error(f"Erro CSV: {e}")
        return None

@st.cache_data(ttl=900, show_spinner="Sincronizando com ERP...")
def disparar_automacao_erp():
    chrome_options = Options()
    chrome_options.add_argument("--headless") # Obrigatório no servidor
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    def forcar_input_react(elemento, valor):
                script = """
                var element = arguments[0]; var value = arguments[1]; var lastValue = element.value;
                element.value = value; var event = new Event('input', { bubbles: true });
                var tracker = element._valueTracker; if (tracker) { tracker.setValue(lastValue); }
                element.dispatchEvent(event); element.dispatchEvent(new Event('change', { bubbles: true }));
                """
                driver.execute_script(script, elemento, valor)
    # Limpa a pasta antes de baixar
    for f in glob.glob(os.path.join(str(DOWNLOAD_FOLDER), "*")):
        os.remove(f)

    prefs = {"download.default_directory": str(DOWNLOAD_FOLDER.absolute())}
    chrome_options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(DOWNLOAD_FOLDER.absolute())})
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
        time.sleep(3)
        try:
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

                # Limpeza datas
            driver.execute_script("""
                ['beginInitialDate', 'endInitialDate'].forEach(id => {
                    var el = document.getElementById(id);
                    if(el) { el.focus(); el.value = ''; el.dispatchEvent(new Event('input', {bubbles:true})); el.blur(); }
                });
            """)

            hj = datetime.now()
            fim = hj.replace(day=calendar.monthrange(hj.year, hj.month)[1]).strftime("%d/%m/%Y")
            forcar_input_react(driver.find_element(By.ID, "finalReportClosingDate"), fim)
            time.sleep(2)
            driver.find_element(By.XPATH, "//button[contains(., 'aplicar')]").click()
            time.sleep(6)
        except: pass
        
        # 4. Exportar
        btn_exp = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@tooltip='Imprimir/Exportar']")))
        driver.execute_script("arguments[0].click();", btn_exp)
        
        btn_csv = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '.CSV')]")))
        btn_csv.click()
        
        # Aguarda download (Loop de verificação em vez de sleep fixo)
        caminho_final = None
        for _ in range(30):
            arquivos = glob.glob(os.path.join(str(DOWNLOAD_FOLDER), "*.csv"))
            if arquivos:
                caminho_final = max(arquivos, key=os.path.getmtime)
                break
            time.sleep(2)
            
        return analisar_dados_encerramentos(caminho_final)
        
    except Exception as e:
        st.error(f"Erro na automação: {str(e)}")
        return None
    finally:
        driver.quit()

# --- INTERFACE PRINCIPAL ---
def render():
# --- INTERFACE (Substitua a partir daqui no seu render) ---
    st.title("📈 Performance Unificada")
    
    # Chama as funções de coleta (que já estão com cache)
    df_erp = disparar_automacao_erp()
    dados_tme = load_technical_data()

    if dados_tme:
        # 1. Seletor de Atendente
        lista_nomes = sorted([l[0] for l in dados_tme if len(l) > 0 and l[0] in MAPEAMENTO_TECNICOS])
        selecionado = st.selectbox("👤 Selecionar o Atendente:", options=lista_nomes)

        # 2. Processamento dos dados para a interface
        mapa = {l[0]: l for l in dados_tme if len(l) > 0}
        linha = mapa[selecionado][3:]
        
        # Filtra os dados da planilha até ontem
        grafico_raw = [linha[i] if i < len(linha) else "" for i in range(dia_ontem)]
        tempos_seg = [converter_para_segundos(t) for t in grafico_raw]
        validos = [s for s in tempos_seg if s is not None]
        
        # Cálculo do TME Médio
        tme_media = formatar_segundos(sum(validos)/len(validos)) if validos else "00:00:00"

        # Filtra os encerramentos do ERP para o técnico selecionado
        df_tec = df_erp[df_erp['Atendente_Planilha'] == selecionado] if df_erp is not None else pd.DataFrame()
        counts_enc = df_tec['DATA_REF'].dt.day.value_counts().to_dict() if not df_tec.empty else {}

        # 3. Exibição das Métricas Principais
        st.divider()
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("TME Acumulado (Mês)", tme_media)
        with col_m2:
            st.metric("Total Encerramentos", f"{len(df_tec)} un")

        # 4. GRID DIÁRIO (O Design Bonitinho)
        st.subheader("📅 Histórico Diário")
        
        # Cria as colunas para o grid (7 dias por linha)
        grid = st.columns(7)
        
        for i in range(dia_ontem):
            dia = i + 1
            with grid[i % 7]:
                val_tme = str(grafico_raw[i]).strip()
                seg = tempos_seg[i]
                qtd = counts_enc.get(dia, 0)
                
                # Definição de Cores Condicionais
                cor_tme = "#FFFFFF" # Branco padrão
                if val_tme in ["", "FORA"]: 
                    cor_tme = "#FFD700" # Amarelo para folga/fora
                elif seg is not None and seg > 15: 
                    cor_tme = "#FF4B4B" # Vermelho para alerta (>15s)

                # Container HTML para o Card do Dia
                st.markdown(f"""
                    <div style="
                        background: #1d2129; 
                        padding: 12px; 
                        border-radius: 10px; 
                        border: 1px solid #30363d; 
                        margin-bottom: 12px; 
                        text-align: center;
                        min-height: 100px;
                    ">
                        <div style="color: #8b949e; font-size: 0.85rem; font-weight: 500;">
                            {dia:02d}/{mes_atual:02d}
                        </div>
                        <div style="font-size: 1.15rem; font-weight: bold; color: {cor_tme}; margin-top: 5px;">
                            ⏱️ {val_tme if val_tme else '---'}
                        </div>
                        <div style="font-size: 0.95rem; font-weight: 600; color: #4da3ff; margin-top: 8px; border-top: 1px solid #30363d; padding-top: 5px;">
                            ENC: {qtd}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("💡 Aguardando conexão com a base de dados...")

if __name__ == "__main__":
    main()
