import streamlit as st
import pandas as pd
import gspread
import json
import os
import re
import time
import glob
import unicodedata
import pytz
import calendar
import traceback
from datetime import timedelta, datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from streamlit_autorefresh import st_autorefresh
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. MAPEAMENTO DE NOMES ---
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
    url = st.secrets.get("SPREADSHEET_URL") or st.secrets.get("URL_PLANILHA")
    creds_json_str = st.secrets.get("GOOGLE_JSON_CREDENTIALS_2") or st.secrets.get("GOOGLE_JSON_CREDENTIALS")
    
    if not url or not creds_json_str:
        st.error("❌ Credenciais não encontradas nos Secrets.")
        return None

    try:
        creds_dict = json.loads(creds_json_str)
        
        if "private_key" in creds_dict:
            # 1. Pega a chave bruta
            pk = creds_dict["private_key"]
            
            # 2. LIMPEZA AGRESSIVA:
            # Remove escapes de barra, espaços e garante que as quebras de linha sejam \n reais
            pk = pk.replace("\\n", "\n")
            
            # 3. Reconstrói a chave garantindo que não haja espaços entre o conteúdo Base64
            # Isso resolve o erro de 'Incorrect padding'
            lines = pk.split('\n')
            clean_lines = []
            for line in lines:
                clean_line = line.strip()
                if clean_line:
                    clean_lines.append(clean_line)
            
            creds_dict["private_key"] = "\n".join(clean_lines)
            
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        spreadsheet = client.open_by_url(url.strip())
        sheet = spreadsheet.worksheet("AtendimentoTécnico")
        return sheet.get("A8:AF20")
        
    except Exception as e:
        st.error(f"❌ Erro Crítico na Planilha: {e}")
        # Se falhar, vamos ver como a chave está chegando (sem mostrar a chave toda por segurança)
        if "private_key" in locals():
            st.info(f"Tamanho da chave processada: {len(creds_dict['private_key'])} caracteres.")
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
        st.error(f"❌ Erro CSV: {e}")
        return None

@st.cache_data(ttl=900, show_spinner="🤖 Sincronizando com ERP...")
def disparar_automacao_erp(download_path_obj, mes, ano):
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") # Headless mais moderno
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu") # Importante para servidores Linux
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Impede que o Chrome use muita memória RAM (evita o crash da Stacktrace)
    chrome_options.add_argument("--js-flags='--max-old-space-size=512'") 

    def forcar_input_react(driver, elemento, valor):
        script = "var element = arguments[0]; var value = arguments[1]; var lastValue = element.value; element.value = value; var event = new Event('input', { bubbles: true }); var tracker = element._valueTracker; if (tracker) { tracker.setValue(lastValue); } element.dispatchEvent(event); element.dispatchEvent(new Event('change', { bubbles: true }));"
        driver.execute_script(script, elemento, valor)

    # Limpeza da pasta de downloads
    for f in glob.glob(os.path.join(str(download_path_obj), "*")):
        try: os.remove(f)
        except: pass

    prefs = {
        "download.default_directory": str(download_path_obj.absolute()),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(download_path_obj.absolute())})
        wait = WebDriverWait(driver, 35) # Aumentado para dar fôlego ao servidor

        # 1. Login com verificação
        driver.get("https://erp.osirnet.com.br/all_solicitations#/")
        
        try:
            # Verifica se caiu na tela de login
            user_field = wait.until(EC.presence_of_element_located((By.ID, ":r0:")))
            user_field.send_keys(st.secrets["ERP_USER"])
            driver.find_element(By.ID, ":r1:").send_keys(st.secrets["ERP_PASS"])
            driver.find_element(By.XPATH, "//button[contains(., 'Entrar')]").click()
            time.sleep(5) # Espera o redirecionamento
        except Exception:
            # Se não achou o campo de login, talvez já esteja logado ou a página mudou
            pass
        
        # 2. Navegação para a URL de solicitações
        driver.get("https://erp.osirnet.com.br/all_solicitations#/")
        
        # 3. Filtros (Aqui é onde o erro costuma acontecer)
        # Tenta clicar no filtro avançado com JS caso o Selenium se perca
        btn_filtro = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@tooltip='Filtro avançado']")))
        driver.execute_script("arguments[0].click();", btn_filtro)
        time.sleep(3)

        # Seleção da Equipe
        wait.until(EC.element_to_be_clickable((By.ID, "teamId"))).click()
        time.sleep(1)
        f_all = wait.until(EC.presence_of_element_located((By.ID, "filterAll")))
        f_all.send_keys("COP Encerramentos")
        f_all.send_keys(Keys.ENTER)
        
        # Clica na equipe na lista
        equipe_item = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@id='datagrid_row' and contains(text(), 'COP Encerramentos')]")))
        driver.execute_script("arguments[0].click();", equipe_item)
        time.sleep(1)
        
        driver.find_element(By.XPATH, "//button[contains(., 'Confirmar')]").click()

        # 4. Data
        hj = datetime.now()
        # Pega o último dia do mês atual
        ultimo_dia = calendar.monthrange(hj.year, hj.month)[1]
        data_fim = f"{ultimo_dia:02d}/{hj.month:02d}/{hj.year}"
        
        campo_data = wait.until(EC.presence_of_element_located((By.ID, "finalReportClosingDate")))
        forcar_input_react(driver, campo_data, data_fim)
        time.sleep(2)
        
        driver.find_element(By.XPATH, "//button[contains(., 'aplicar')]").click()
        time.sleep(10) # Tempo para processar a lista pesada
        
        # 5. Exportação
        btn_exp = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@tooltip='Imprimir/Exportar']")))
        driver.execute_script("arguments[0].click();", btn_exp)
        
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '.CSV')]"))).click()
        
        # Aguarda o download de forma inteligente
        caminho_final = None
        for _ in range(20):
            arquivos = glob.glob(os.path.join(str(download_path_obj), "*.csv"))
            if arquivos:
                caminho_final = max(arquivos, key=os.path.getmtime)
                break
            time.sleep(2)
            
        if caminho_final:
            return analisar_dados_encerramentos(caminho_final, mes, ano)
        return None

    except Exception as e:
        # Aqui capturamos o erro real antes da Stacktrace
        st.error(f"❌ Erro detalhado na automação: {str(e)}")
        return None
    finally:
        driver.quit()

# --- 3. INTERFACE PRINCIPAL ---
def render():
    from styles import apply_styles
    apply_styles()
    st_autorefresh(interval=15 * 60 * 1000, key="refresh_perf")
    
    fuso_br = pytz.timezone('America/Sao_Paulo')
    hoje = datetime.now(fuso_br)
    dia_ontem = hoje.day - 1
    mes_atual = hoje.month
    ano_atual = hoje.year

    base_dir = Path(__file__).parent.parent
    download_folder = base_dir / "temp_downloads"
    download_folder.mkdir(parents=True, exist_ok=True)

    dados_tme_brutos = load_technical_data()
    if not dados_tme_brutos:
        st.warning("⚠️ Aguardando sincronização com Google Sheets...")
        return

    lista_nomes_planilha = sorted([l[0] for l in dados_tme_brutos if len(l) > 0 and l[0] in MAPEAMENTO_TECNICOS])
    
    st.markdown("### 👤 Seletor de Performance")
    col_sel, col_sync = st.columns([3, 1])
    
    with col_sel:
        selecionado = st.selectbox("Atendente:", options=lista_nomes_planilha, label_visibility="collapsed")
    
    with col_sync:
        if st.button("🔄 Atualizar ERP", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    df_erp = disparar_automacao_erp(download_folder, mes_atual, ano_atual)

    # Lógica de Cálculo
    mapa = {l[0]: l for l in dados_tme_brutos if len(l) > 0}
    linha_tecnico = mapa[selecionado]
    dados_tecnico_raw = linha_tecnico[3:]
    dados_ate_ontem = [dados_tecnico_raw[i] if i < len(dados_tecnico_raw) else "" for i in range(dia_ontem)]
    tempos_seg = [converter_para_segundos(t) for t in dados_ate_ontem]
    tempos_validos = [s for s in tempos_seg if s is not None]
    
    tme_acumulado = formatar_segundos(sum(tempos_validos)/len(tempos_validos)) if tempos_validos else "00:00:00"
    df_tec_erp = df_erp[df_erp['Atendente_Planilha'] == selecionado] if df_erp is not None else pd.DataFrame()
    total_atual = len(df_tec_erp)

    # --- MÉTRICAS ---
    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("👤 Técnico", selecionado)
    m2.metric("⏱️ TME Acumulado", tme_acumulado)
    m3.metric("📑 Total Encerramentos", f"{total_atual} un")

    # --- PROGRESSO METAS ---
    meta_normal, super_meta = 550, 681
    c_meta1, c_meta2 = st.columns(2)
    with c_meta1:
        st.write(f"**🎯 Meta Normal ({meta_normal} un)**")
        st.progress(min(total_atual/meta_normal, 1.0))
        if total_atual >= meta_normal: st.success("✅ Meta Alcançada!")
    with c_meta2:
        st.write(f"**🚀 Super Meta ({super_meta} un)**")
        st.progress(min(total_atual/super_meta, 1.0))
        if total_atual >= super_meta: st.balloons(); st.success("🏆 Super Meta Batida!")

    # --- GRID DIÁRIO ---
    st.subheader("📅 Histórico Mensal")
    grid = st.columns(7)
    counts_enc = df_tec_erp['DATA_REF'].dt.day.value_counts().to_dict() if not df_tec_erp.empty else {}

    for i in range(dia_ontem):
        dia = i + 1
        with grid[i % 7]:
            val_tme = str(dados_ate_ontem[i]).strip()
            seg = tempos_seg[i]
            qtd = counts_enc.get(dia, 0)
            cor_tme = "#FFD700" if val_tme in ["", "FORA"] else ("#FF4B4B" if seg and seg > 15 else "#FFFFFF")
            
            st.markdown(f"""
                <div style="background:#1d2129; padding:10px; border-radius:8px; border:1px solid #30363d; margin-bottom:10px; text-align:center;">
                    <div style="color:#8b949e; font-size:0.75rem;">{dia:02d}/{mes_atual:02d}</div>
                    <div style="font-weight:bold; color:{cor_tme};">⏱️ {val_tme if val_tme else '---'}</div>
                    <div style="color:#4da3ff; font-size:0.9rem; border-top:1px solid #333; margin-top:5px;">ENC: {qtd}</div>
                </div>
            """, unsafe_allow_html=True)
