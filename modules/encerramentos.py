import os
import re
import time
import glob
import shutil
import calendar
import unicodedata
import pandas as pd
import streamlit as st
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from streamlit_autorefresh import st_autorefresh
import json
import pytz
from pathlib import Path

def render():
    # Aumentei o intervalo para 10 minutos para não sobrecarregar o servidor
    st_autorefresh(interval=10 * 60 * 1000, key="refresh_encerramentos")
    
    ERP_USER = st.secrets["ERP_USER"]
    ERP_PASS = st.secrets["ERP_PASS"]
    BASE_DIR = Path(__file__).parent.parent
    DOWNLOAD_FOLDER = BASE_DIR / st.secrets["DOWNLOAD_PATH"].strip("/")
    DESTINO_FOLDER = BASE_DIR / st.secrets["DESTINO_PATH"].strip("/")

    DOWNLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    DESTINO_FOLDER.mkdir(parents=True, exist_ok=True)
    URL_ERP = st.secrets["URL_ERP"]
    
    # --- FUNÇÕES DE APOIO ---
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
        if caminho_csv is None or not os.path.exists(caminho_csv): return None
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
            # Lendo com tratamento de erro para arquivos vazios
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
        # Limpeza: espera o arquivo terminar de baixar
        time.sleep(5) 
        path_str = str(DOWNLOAD_FOLDER.absolute())
        arquivos = glob.glob(os.path.join(path_str, "*.csv"))
        if not arquivos: return None
        
        arquivo_recente = max(arquivos, key=os.path.getmtime)
        nome_arq = f"relatorio_encerras_{int(time.time())}.csv" # Nome dinâmico para evitar cache de arquivo
        caminho_final = DESTINO_FOLDER / nome_arq
        
        shutil.move(arquivo_recente, str(caminho_final.absolute()))
        return str(caminho_final.absolute())

    # --- AUTOMAÇÃO SELENIUM ---
    @st.cache_data(ttl=900, show_spinner=False)
    def disparar_automacao_cached():
        prog_container = st.empty()
        p_bar = prog_container.progress(0)
        
        chrome_options = Options()
        chrome_options.add_argument("--headless=new") # Mudança para a versão mais estável do headless
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")

        abs_download_path = str(DOWNLOAD_FOLDER.absolute())
        prefs = {
            "download.default_directory": abs_download_path,
            "download.prompt_for_download": False,
            "directory_upgrade": True
        }
        chrome_options.add_experimental_option("prefs", prefs)

        driver = None
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": abs_download_path})
            wait = WebDriverWait(driver, 40)
            
            def forcar_input_react(elemento, valor):
                driver.execute_script("""
                    var element = arguments[0]; var value = arguments[1];
                    element.value = value;
                    element.dispatchEvent(new Event('input', { bubbles: true }));
                    element.dispatchEvent(new Event('change', { bubbles: true }));
                    element.blur();
                """, elemento, valor)

            # 1. Login
            p_bar.progress(10, text="🔐 Efetuando Login...")
            driver.get(URL_ERP)
            time.sleep(5)
            
            # Tenta localizar campos de login com seletores mais flexíveis
            user_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'], input#\\:r0\\:")))
            pass_field = driver.find_element(By.CSS_SELECTOR, "input[type='password'], input#\\:r1\\:")
            
            forcar_input_react(user_field, ERP_USER)
            forcar_input_react(pass_field, ERP_PASS)
            
            btn_login = driver.find_element(By.XPATH, "//button[contains(., 'Entrar')]")
            driver.execute_script("arguments[0].click();", btn_login)
            time.sleep(8)

            # 2. Tela Antiga
            status_text.text("⚙️ Acessando interface...")
            p_bar.progress(30)
            try:
                btn_ant = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Tela antiga']")))
                driver.execute_script("arguments[0].click();", btn_ant)
                time.sleep(6)
            except: pass
            # 2. Navegação e Filtros
            p_bar.progress(40, text="🔍 Aplicando filtros...")
            driver.get(URL_ERP)
            time.sleep(5)
            
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@tooltip='Filtro avançado']"))).click()
            time.sleep(3)

            # Seleção de Equipe
            wait.until(EC.element_to_be_clickable((By.ID, "teamId"))).click()
            time.sleep(1)
            f_all = wait.until(EC.presence_of_element_located((By.ID, "filterAll")))
            f_all.send_keys("COP Encerramentos")
            time.sleep(2)
            f_all.send_keys(Keys.ENTER)
            time.sleep(2)
            
            wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@id='datagrid_row' and contains(., 'COP Encerramentos')]"))).click()
            driver.find_element(By.XPATH, "//button[contains(., 'Confirmar')]").click()

            # Datas
            hj = datetime.now()
            ultimo_dia = calendar.monthrange(hj.year, hj.month)[1]
            data_ini = f"01/{hj.month:02d}/{hj.year}"
            data_fim = f"{ultimo_dia:02d}/{hj.month:02d}/{hj.year}"
            
            # Limpeza via JS para garantir que o campo aceite o novo valor
            driver.execute_script("document.getElementById('beginReportClosingDate').value = '';")
            forcar_input_react(driver.find_element(By.ID, "beginReportClosingDate"), data_ini)
            
            driver.execute_script("document.getElementById('finalReportClosingDate').value = '';")
            forcar_input_react(driver.find_element(By.ID, "finalReportClosingDate"), data_fim)
            
            time.sleep(2)
            driver.find_element(By.XPATH, "//button[contains(., 'aplicar')]").click()
            time.sleep(10)

            # 3. Exportação
            p_bar.progress(80, text="📥 Baixando CSV...")
            btn_exp = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@tooltip='Imprimir/Exportar']")))
            driver.execute_script("arguments[0].click();", btn_exp)
            time.sleep(2)
            
            btn_csv = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '.CSV')]")))
            driver.execute_script("arguments[0].click();", btn_csv)
            
            time.sleep(25) # Espera o download
            caminho = mover_arquivo_recente()
            
            p_bar.progress(100, text="✅ Concluído!")
            time.sleep(2)
            prog_container.empty()
            
            hora_br = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%H:%M:%S")
            return {"dados": analisar_dados_encerramentos(caminho), "horario": hora_br}

        except Exception as e:
            st.error(f"Ocorreu um erro no robô: {str(e)}")
            return None
        finally:
            if driver:
                driver.quit()

    # --- LÓGICA DE EXIBIÇÃO (REVISADA) ---
    st.title("🚀 É A EQUIPE DO ENCERRAS!!!")
    
    # Botão manual para forçar atualização se necessário
    if st.button("🔄 Atualizar Agora"):
        st.cache_data.clear()
        st.rerun()

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
