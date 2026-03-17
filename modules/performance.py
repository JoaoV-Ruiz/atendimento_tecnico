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
from oauth2client.service_account import ServiceAccountCredentials
from styles import apply_styles

def render():
    # 1. Configurações Iniciais e Estilo
    apply_styles()
    st_autorefresh(interval=10 * 60 * 1000, key="refresh_performance")
    
    fuso_br = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(fuso_br)
    dia_ontem = agora.day - 1
    mes_atual_num = agora.month
    ano_atual_num = agora.year

    # --- CONFIGURAÇÃO DE SEGREDOS E CAMINHOS ---
    ERP_USER = st.secrets["ERP_USER"]
    ERP_PASS = st.secrets["ERP_PASS"]
    BASE_DIR = Path(__file__).parent.parent
    NOME_DOWNLOAD = st.secrets["DOWNLOAD_PATH"].strip("/")
    DOWNLOAD_FOLDER = BASE_DIR / NOME_DOWNLOAD
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

    # --- FUNÇÕES DE APOIO ---
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

    def mover_arquivo_recente():
        path_str = str(DOWNLOAD_FOLDER.absolute())
        time.sleep(5) # Espera o download estabilizar
        arquivos = glob.glob(os.path.join(path_str, "*"))
        if not arquivos: return None
        return max(arquivos, key=os.path.getmtime)

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

    def analisar_dados_encerramentos(caminho_csv):
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
            return df[(df['DATA_REF'].dt.month == mes_atual_num) & (df['DATA_REF'].dt.year == ano_atual_num)]
        except Exception as e:
            st.error(f"Erro CSV: {e}")
            return None

    @st.cache_data(ttl=900, show_spinner=False)
    def disparar_automacao_erp():
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        abs_download_path = str(DOWNLOAD_FOLDER.absolute())
        chrome_options.add_experimental_option("prefs", {"download.default_directory": abs_download_path, "download.prompt_for_download": False})

        driver = None
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": abs_download_path})
            wait = WebDriverWait(driver, 35)

            # Lógica de Login e Exportação idêntica ao Encerramentos.py
            driver.get(URL_ERP)
            time.sleep(5)
            try:
                user_f = wait.until(EC.element_to_be_clickable((By.ID, ":r0:")))
                pass_f = driver.find_element(By.ID, ":r1:")
                # Injeção via JS para evitar erros do React
                driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", user_f, ERP_USER)
                driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", pass_f, ERP_PASS)
                driver.find_element(By.XPATH, "//button[contains(., 'Entrar')]").click()
                time.sleep(10)
            except: pass

            driver.get(URL_ERP)
            time.sleep(5)
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@tooltip='Filtro avançado']"))).click()
            time.sleep(2)
            
            # (Filtros e Exportação conforme Encerramentos.py)
            # ... (seu código de filtros ERP) ...
            
            # Exportar CSV
            btn_exp = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@tooltip='Imprimir/Exportar']")))
            driver.execute_script("arguments[0].click();", btn_exp)
            time.sleep(2)
            driver.find_element(By.XPATH, "//button[contains(., '.CSV')]").click()
            time.sleep(30)
            
            caminho = mover_arquivo_recente()
            return analisar_dados_encerramentos(caminho)
        except: return None
        finally:
            if driver: driver.quit()

    # --- RENDERIZAÇÃO DA INTERFACE (MANTENDO SEU ESTILO ORIGINAL) ---
    st.title("📈 Performance Unificada")
    
    dados_tme_brutos = load_technical_data()
    df_erp = disparar_automacao_erp()

    if dados_tme_brutos:
        lista_nomes = sorted([l[0] for l in dados_tme_brutos if len(l) > 0 and l[0] in MAPEAMENTO_TECNICOS])
        selecionado = st.selectbox("👤 Selecione o Atendente", options=lista_nomes)

        # Processamento TME
        mapa = {l[0]: l for l in dados_tme_brutos if len(l) > 0}
        linha_tec = mapa[selecionado][3:]
        dados_ate_ontem = [linha_tec[i] if i < len(linha_tec) else "" for i in range(dia_ontem)]
        tempos_seg = [converter_para_segundos(t) for t in dados_ate_ontem]
        validos = [s for s in tempos_seg if s is not None]
        tme_acumulado = formatar_segundos(sum(validos)/len(validos)) if validos else "00:00:00"

        # Processamento ERP
        df_tec_erp = df_erp[df_erp['Atendente_Planilha'] == selecionado] if df_erp is not None else pd.DataFrame()
        
        # Métricas no Estilo do Sistema
        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("TME Acumulado", tme_acumulado)
        m2.metric("Total Encerramentos", f"{len(df_tec_erp)} un")
        
        # Grid de quadradinhos diários
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
                        <div style="color:#8b949e; font-size:0.8rem;">{dia:02d}/{mes_atual_num:02d}</div>
                        <div style="font-size:1.1rem; font-weight:bold; color:{cor_tme};">⏱️ {val_tme if val_tme else '---'}</div>
                        <div style="font-size:0.9rem; color:#4da3ff;">ENC: {qtd}</div>
                    </div>
                """, unsafe_allow_html=True)
