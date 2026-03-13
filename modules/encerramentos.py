import os
import re
import time
import glob
import shutil
import calendar
import unicodedata
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from streamlit_autorefresh import st_autorefresh
import json
import traceback
import pytz
from pathlib import Path

def render():
    st_autorefresh(interval=5 * 60 * 1000, key="refresh_encerramentos")
    
    # --- 1. CONFIGURAÇÃO DE SEGREDOS E CAMINHOS (PATHLIB) ---
    ERP_USER = st.secrets["ERP_USER"]
    ERP_PASS = st.secrets["ERP_PASS"]
    
    # Define a raiz do projeto (sobe dois níveis de modules/encerramentos.py)
    BASE_DIR = Path(__file__).parent.parent

    # Pega os nomes das pastas dos Secrets e garante que são objetos Path
    NOME_DOWNLOAD = st.secrets["DOWNLOAD_PATH"].strip("/")
    NOME_DESTINO = st.secrets["DESTINO_PATH"].strip("/")

    DOWNLOAD_FOLDER = BASE_DIR / NOME_DOWNLOAD
    DESTINO_FOLDER = BASE_DIR / NOME_DESTINO

    # Cria as pastas no servidor
    DOWNLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    DESTINO_FOLDER.mkdir(parents=True, exist_ok=True)

    URL_ERP = "https://erp.osirnet.com.br/all_solicitations#/"

    # --- 2. FUNÇÕES DE APOIO ---
    def super_limpeza(texto):
        if not isinstance(texto, str): return ""
        texto = texto.split(" / ")[0].upper()
        texto = unicodedata.normalize('NFKD', texto)
        texto = "".join([c for c in texto if not unicodedata.combining(c)])
        return re.sub(r'[^A-Z]', '', texto)

    def identificar_pela_chave(nome_bruto_csv, termos_busca):
        if pd.isna(nome_bruto_csv) or "Sem Atendente" in str(nome_bruto_csv): return None
        nome_limpo_csv = super_limpeza(str(nome_bruto_csv))
        for chave_limpa, nome_bonito in termos_busca.items():
            if chave_limpa in nome_limpo_csv: return nome_bonito
        return None

    def analisar_dados_encerramentos(caminho_csv):
        if caminho_csv is None or not os.path.exists(caminho_csv):
            return None
        try:
            termos_busca = {
                "ALISSONDOCOUTOGUERREIRO": "ALISSON DO COUTO GUERREIRO", "IGORSALDANHA": "IGOR SALDANHA",
                "JOAOVITORRUIZBARBOZA": "JOÃO VITOR RUIZ BARBOZA", "VINICIUSCOPPA": "VINICIUS COPPA",
                "JULIADASILVADUARTE": "JULIA DA SILVA DUARTE", "KAULARRIGOCKSDASILVEIRA": "KAUÃ LARRI GOCKS DA SILVEIRA",
                "KAUALARRIGOCKSDASILVEIRA": "KAUÃ LARRI GOCKS DA SILVEIRA", "CAIOREIS": "CAIO REIS",
                "DIOGOTABORDADEBITENCOURT": "DIOGO BITENCOURT", "MARIAEDUARDABARBOSAVIANA": "MARIA EDUARDA BARBOSA VIANA",
                "NATHALIVALLIER": "NATHALI VALLIER", "RICHERFALCAOARAUJO": "RICHER FALCÃO ARAUJO",
                "SINDEWCRIZELNUNES": "SINDEW CRIZEL NUNES", "CRISTIANOMARQUES": "CRISTIANO MARQUES",
                "FILIPEVIEIRAVAZ": "FILIPE VIEIRA VAZ"
            }
            df = pd.read_csv(caminho_csv, sep=None, engine='python', encoding='latin-1', on_bad_lines='skip')
            col_encontrada = [c for c in df.columns if "Encerramento" in c]
            if not col_encontrada: return None
            
            df['DATA_REF'] = pd.to_datetime(df[col_encontrada[0]], dayfirst=True, errors='coerce')
            df['MES_ANO'] = df['DATA_REF'].dt.strftime('%m/%Y')
            
            possiveis_cols = ["Atendente", "Usuário Encerramento", "Responsável", "Nome"]
            coluna_tecnico = next((c for c in possiveis_cols if c in df.columns), df.columns[3])
            
            df['Atendente'] = df[coluna_tecnico].apply(lambda x: identificar_pela_chave(x, termos_busca))
            return df.dropna(subset=['Atendente', 'DATA_REF']).copy()
        except Exception as e:
            st.error(f"Erro na análise do CSV: {e}")
            return None

    def mover_arquivo_recente():
        timeout = 60
        path_str = str(DOWNLOAD_FOLDER.absolute())
        for _ in range(timeout):
            if not any(f.endswith(".crdownload") for f in os.listdir(path_str)): break
            time.sleep(1)
        
        arquivos = glob.glob(os.path.join(path_str, "*"))
        if not arquivos: return None
        
        arquivo_recente = max(arquivos, key=os.path.getmtime)
        nome_arq = os.path.basename(arquivo_recente)
        caminho_final = DESTINO_FOLDER / nome_arq
        
        shutil.move(arquivo_recente, str(caminho_final.absolute()))
        return str(caminho_final.absolute())

    # --- 3. AUTOMAÇÃO SELENIUM ---
    @st.cache_data(ttl=300, show_spinner=False)
    def disparar_automacao_cached():
        prog_container = st.empty()
        text_container = st.empty()
        p_bar = prog_container.progress(0)
        status_text = text_container.text("🚀 Robô em ação...")
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")

        abs_download_path = str(DOWNLOAD_FOLDER.absolute())
        prefs = {
            "download.default_directory": abs_download_path,
            "download.prompt_for_download": False,
            "directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)

        driver = None
        try:
            driver = webdriver.Chrome(options=chrome_options)
            
            # Comando CRÍTICO para habilitar downloads no modo Headless do Linux
            driver.execute_cdp_cmd("Page.setDownloadBehavior", {
                "behavior": "allow",
                "downloadPath": abs_download_path
            })

            wait = WebDriverWait(driver, 35)
            
            def forcar_input_react(elemento, valor):
                script = """
                var element = arguments[0]; var value = arguments[1]; var lastValue = element.value;
                element.value = value; var event = new Event('input', { bubbles: true });
                var tracker = element._valueTracker; if (tracker) { tracker.setValue(lastValue); }
                element.dispatchEvent(event); element.dispatchEvent(new Event('change', { bubbles: true }));
                """
                driver.execute_script(script, elemento, valor)

            # 1. Login
            status_text.text("🔐 Efetuando Login...")
            p_bar.progress(20)
            driver.get(URL_ERP)
            time.sleep(5)
            try:
                c_user = wait.until(EC.element_to_be_clickable((By.ID, ":r0:")))
                c_pass = driver.find_element(By.ID, ":r1:")
                forcar_input_react(c_user, ERP_USER)
                forcar_input_react(c_pass, ERP_PASS) 
                driver.find_element(By.XPATH, "//button[@data-testid='button' and contains(., 'Entrar')]").click()
                time.sleep(10)
            except: pass

            # 2. Tela Antiga
            status_text.text("⚙️ Acessando interface...")
            p_bar.progress(40)
            try:
                btn_ant = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Tela antiga']")))
                driver.execute_script("arguments[0].click();", btn_ant)
                time.sleep(6)
            except: pass

            # 3. Filtros
            status_text.text("🔍 Aplicando filtros...")
            p_bar.progress(60)
            try:
                driver.get(URL_ERP)
                time.sleep(5)
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
                time.sleep(12)
            except: pass

            # 4. Exportação
            status_text.text("📥 Baixando CSV...")
            p_bar.progress(85)
            try:
                btn_exp = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@tooltip='Imprimir/Exportar']")))
                driver.execute_script("arguments[0].click();", btn_exp)
                time.sleep(2)
                driver.find_element(By.XPATH, "//button[contains(., '.CSV')]").click()
                
                time.sleep(30) # Tempo maior para o servidor processar
                caminho = mover_arquivo_recente()
                
                if caminho is None:
                    return None

                status_text.text("✅ Sincronizado!")
                p_bar.progress(100)
                time.sleep(1)
                prog_container.empty()
                text_container.empty()
                
                hora_br = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%H:%M:%S")
                return {"dados": analisar_dados_encerramentos(caminho), "horario": hora_br}
            except: return None
                
        finally:
            if driver: driver.quit()

    # --- 4. INTERFACE STREAMLIT ---
    st.title("🚀 É A EQUIPE DO ENCERRAS!!!")
    resultado = disparar_automacao_cached()
    
    if resultado and resultado.get("dados") is not None:
        df_completo = resultado["dados"]
        hora = resultado["horario"]
        
        if not df_completo.empty:
            st.markdown(f"**🕒 Última Sincronização:** `{hora}`")
            hoje = datetime.now(pytz.timezone('America/Sao_Paulo'))
            mes_atual_str = hoje.strftime('%m/%Y')
            
            meses_disponiveis = sorted(df_completo['MES_ANO'].dropna().unique(), 
                                       key=lambda x: datetime.strptime(x, '%m/%Y'), reverse=True)

            tab_geral, tab_ranking, tab_individual = st.tabs(["📊 Visão Geral", "🏆 Ranking Mensal", "👤 Individual"])

            with tab_geral:
                df_mes = df_completo[df_completo['MES_ANO'] == mes_atual_str]
                if not df_mes.empty:
                    stats = df_mes['Atendente'].value_counts().reset_index()
                    stats.columns = ['Atendente', 'Encerras']
                    stats.index = stats.index + 1 
                    c1, c2, c3 = st.columns(3)
                    c1.metric(f"Total em {mes_atual_str}", f"{len(df_mes)} un")
                    c2.metric("Média/Técnico", f"{round(stats['Encerras'].mean(), 1)}")
                    c3.metric("Líder", f"{stats.iloc[0]['Atendente'].split()[0]}", f"{stats.iloc[0]['Encerras']} un")
                    st.dataframe(stats, use_container_width=True)
                else: st.info(f"Sem dados para {mes_atual_str}.")

            with tab_ranking:
                if meses_disponiveis:
                    abas_rank = st.tabs(meses_disponiveis[:3] + ["🏆 Ranking Geral"])
                    for i, mes in enumerate(meses_disponiveis[:3]):
                        with abas_rank[i]:
                            df_r = df_completo[df_completo['MES_ANO'] == mes]['Atendente'].value_counts().reset_index()
                            df_r.columns = ['Atendente', 'Total']; df_r.index = df_r.index + 1
                            st.table(df_r)
                    with abas_rank[-1]:
                        df_geral = df_completo['Atendente'].value_counts().reset_index()
                        df_geral.columns = ['Atendente', 'Total Acumulado']; df_geral.index = df_geral.index + 1
                        st.table(df_geral)

            with tab_individual:
                atendentes = sorted(df_completo['Atendente'].unique())
                if atendentes:
                    tecnico = st.selectbox("Selecione o Atendente:", atendentes, key="sb_individual_tecnico")
                    df_tec = df_completo[df_completo['Atendente'] == tecnico].copy()
                    df_tec['MES_INICIO'] = df_tec['DATA_REF'].dt.to_period('M').dt.to_timestamp()
                    hist = df_tec.groupby('MES_INICIO').size().reset_index(name='Encerras')
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.metric("Total Acumulado", len(df_tec))
                        hist_tabela = hist.copy()
                        hist_tabela['Mês/Ano'] = hist_tabela['MES_INICIO'].dt.strftime('%m/%Y')
                        st.dataframe(hist_tabela.sort_values('MES_INICIO', ascending=False)[['Mês/Ano', 'Encerras']], hide_index=True)
                    with col2: st.line_chart(hist.set_index('MES_INICIO')['Encerras'])
        else: st.warning("⚠️ Nenhum dado encontrado no CSV.")
    else: st.info("⏳ Aguardando sincronização do ERP (isso pode levar 1 minuto)...")
