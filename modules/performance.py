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

st.set_page_config(layout="wide")

# --- 1. CONFIGURAÇÕES E MAPEAMENTO ---
MAPEAMENTO_TECNICOS = {
    "Alisson Do Couto Guerreiro": "ALISSON DO COUTO GUERREIRO",
    "Caio Alves dos Reis": "CAIO REIS",
    "Cristiano Weber Marques": "CRISTIANO MARQUES",
    "Diogo Taborda de Bitencourt": "DIOGO TABORDA DE BITENCOURT",
    "Filipe Vieira Vaz": "FILIPE VIEIRA VAZ",
    "Igor Saldanha Noguez": "IGOR SALDANHA",
    "João Vitor Ruiz Barboza": "JOÃO VITOR RUIZ BARBOZA",
    "Julia da Silva Duarte": "JULIA DA SILVA DUARTE",
    "Kauã Larri Gocks da Silveira": "KAUÃ LARRI GOCKS DA SILVEIRA",
    "Nathali Elisa Xavier Vallier": "NATHALI VALLIER",
    "Richer Falcão Araujo": "RICHER FALCÃO ARAUJO",
    "Sindew Crizel Nunes": "SINDEW CRIZEL NUNES",
    "Vinicius Maciel Coppa": "VINICIUS COPPA"
}

# --- 2. FUNÇÕES DE APOIO ---
def super_limpeza(texto):
    if not isinstance(texto, str): return ""
    texto = texto.split(" / ")[0].upper()
    texto = unicodedata.normalize('NFKD', texto)
    texto = "".join([c for c in texto if not unicodedata.combining(c)])
    return re.sub(r'[^A-Z]', '', texto)

def converter_para_segundos(tempo_str):
    if not tempo_str or str(tempo_str).strip() in ["", "FORA", "---"]: return None
    try:
        partes = str(tempo_str).split(':')
        if len(partes) == 3:
            h, m, s = map(int, partes)
            return h * 3600 + m * 60 + s
        elif len(partes) == 2:
            m, s = map(int, partes)
            return m * 60 + s
        return None
    except: return None

def formatar_segundos(segundos):
    if segundos is None or segundos <= 0: return "00:00:00"
    return str(timedelta(seconds=int(segundos)))

# --- NOVO MECANISMO DE PLANILHA (VIA SECRETS) ---
@st.cache_data(ttl=600, show_spinner=False)
def carregar_tme_por_mes(mes_numero):
    # Alterado de os.getenv para st.secrets
    url = st.secrets["SPREADSHEET_URL"]
    creds_json = st.secrets.get("GOOGLE_JSON_CREDENTIALS_2", st.secrets.get("GOOGLE_JSON_CREDENTIALS"))
    
    if not url or not creds_json: 
        return None
    try:
        from google.oauth2.service_account import Credentials
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(json.loads(creds_json), scopes=scopes)
        
        cliente = gspread.authorize(creds)
        planilha = cliente.open_by_url(url)
        aba = planilha.worksheet("AtendimentoTécnico")
        
        aba.update_acell('B2', mes_numero)
        time.sleep(4) 
        
        return aba.get("A8:AJ20")
        
    except Exception as e: 
        st.error(f"Erro ao acessar Planilha (Mês {mes_numero}): {e}")
        return None

# --- 3. ROBÔ ERP ---
def executar_robo_erp_periodo(dt_ini, dt_fim):
    # Alterado para lidar com pastas de forma segura no servidor Linux da nuvem
    download_path_raw = st.secrets.get("DOWNLOAD_PATH", "downloads").strip("/")
    destino_path_raw = st.secrets.get("DESTINO_PATH", "destino").strip("/")
    
    DOWNLOAD_FOLDER = Path(download_path_raw).absolute()
    DESTINO_FOLDER = Path(destino_path_raw).absolute()
    DOWNLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    DESTINO_FOLDER.mkdir(parents=True, exist_ok=True)

    for f in glob.glob(str(DOWNLOAD_FOLDER / "*.csv")):
        try: os.remove(f)
        except: pass

    # MODO HEADLESS ATIVADO PARA NUVEM
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") # Crucial para servidor
    chrome_options.add_argument("--no-sandbox") # Crucial para servidor
    chrome_options.add_argument("--disable-dev-shm-usage") # Crucial para servidor
    chrome_options.add_argument("--disable-gpu") # Extra segurança no Linux
    chrome_options.add_argument("--window-size=1920,1080")
    
    abs_path = str(DOWNLOAD_FOLDER.absolute())
    chrome_options.add_experimental_option("prefs", {"download.default_directory": abs_path})
    
    driver = webdriver.Chrome(options=chrome_options)
    # Permite downloads mesmo no modo Headless
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": abs_path})
    
    wait = WebDriverWait(driver, 45)
    
    try: 
        def forcar_input_react(elemento, valor):
            script = """
            var element = arguments[0]; var value = arguments[1]; var lastValue = element.value;
            element.value = value; var event = new Event('input', { bubbles: true });
            var tracker = element._valueTracker; if (tracker) { tracker.setValue(lastValue); }
            element.dispatchEvent(event); element.dispatchEvent(new Event('change', { bubbles: true }));
            """
            driver.execute_script(script, elemento, valor)

        # Login via Secrets
        driver.get(st.secrets["URL_ERP"])
        time.sleep(5)
        try:
            c_user = wait.until(EC.element_to_be_clickable((By.ID, ":r0:")))
            c_pass = driver.find_element(By.ID, ":r1:")
            forcar_input_react(c_user, st.secrets["ERP_USER"])
            forcar_input_react(c_pass, st.secrets["ERP_PASS"]) 
            driver.find_element(By.XPATH, "//button[@data-testid='button' and contains(., 'Entrar')]").click()
            time.sleep(10)
        except: pass

        # Tela Antiga
        try:
            btn_ant = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Tela antiga']")))
            driver.execute_script("arguments[0].click();", btn_ant)
            time.sleep(6)
        except: pass
        
        driver.get(st.secrets["URL_ERP"])
        time.sleep(5)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@tooltip='Filtro avançado']"))).click()
        time.sleep(3)
        
        # Filtros    
        driver.find_element(By.ID, "teamId").click()
        time.sleep(1)
        f_all = wait.until(EC.element_to_be_clickable((By.ID, "filterAll")))
        f_all.send_keys("COP Encerramentos")
        f_all.send_keys(Keys.ENTER)
        time.sleep(3)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@id='datagrid_row' and contains(text(), 'COP Encerramentos')]"))).click()
        time.sleep(1)
        driver.find_element(By.XPATH, "//button[contains(., 'Confirmar')]").click()

        # Datas
        data_ini_str = dt_ini.strftime("%d/%m/%Y")
        data_fim_str = dt_fim.strftime("%d/%m/%Y")
        
        driver.execute_script("""
            ['beginInitialDate', 'endInitialDate'].forEach(id => {
                var el = document.getElementById(id);
                if(el) { el.focus(); el.value = ''; el.dispatchEvent(new Event('input', {bubbles:true})); el.blur(); }
            });
        """)
        
        forcar_input_react(driver.find_element(By.ID, "initialReportClosingDate"), data_ini_str)
        forcar_input_react(driver.find_element(By.ID, "finalReportClosingDate"), data_fim_str)
        
        time.sleep(2)
        driver.find_element(By.XPATH, "//button[contains(., 'aplicar')]").click()
        time.sleep(15)

        # EXPORTAÇÃO
        btn_exp = wait.until(EC.presence_of_element_located((By.XPATH, "//button[@tooltip='Imprimir/Exportar']")))
        driver.execute_script("arguments[0].click();", btn_exp)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '.CSV')]"))).click()
        
        for _ in range(40):
            arquivos = glob.glob(os.path.join(abs_path, "*.csv"))
            if arquivos and not any(f.endswith('.crdownload') for f in arquivos):
                recente = max(arquivos, key=os.path.getmtime)
                dest = DESTINO_FOLDER / f"perf_periodo_completo.csv"
                shutil.move(recente, str(dest))
                return pd.read_csv(str(dest), sep=None, engine='python', encoding='latin-1')
            time.sleep(2)
            
        return None
    except Exception as e:
        st.error(f"Erro ao coletar dados do ERP: {e}")
        return None
    finally:
        time.sleep(8)   
        driver.quit()

# --- 4. INTERFACE ---

def preparar_csv_consolidado(dados_tme_raw, df_bruto, mes, ano):
    try:
        df_mes = pd.DataFrame()
        if df_bruto is not None and not df_bruto.empty:
            df = df_bruto.copy()
            col_data = None
            for c in df.columns:
                c_low = str(c).lower()
                if "data" in c_low and ("encerrament" in c_low or "fechament" in c_low or "resolu" in c_low):
                    col_data = c
                    break
            if not col_data:
                cols_com_data = [c for c in df.columns if "data" in str(c).lower()]
                col_data = cols_com_data[-1] if cols_com_data else df.columns[0]
            
            df['DATA_DT'] = pd.to_datetime(df[col_data], dayfirst=True, errors='coerce')
            
            possiveis_cols = ["Usuário Encerramento", "Atendente", "Responsável", "Nome"]
            col_atendente = next((c for p in possiveis_cols for c in df.columns if p.lower() in str(c).lower()), df.columns[3])
            
            df['Tec_Formatado'] = df[col_atendente].apply(lambda x: next(
                (p_nome for p_nome, erp_nome in MAPEAMENTO_TECNICOS.items() 
                 if super_limpeza(erp_nome) in super_limpeza(str(x))), 
                None
            ))
            df_mes = df[(df['DATA_DT'].dt.month == mes) & (df['DATA_DT'].dt.year == ano)]

        counts_geral = df_mes['Tec_Formatado'].value_counts().to_dict() if not df_mes.empty else {}
        mapa_tme = {str(l[0]).strip(): l[3:] for l in dados_tme_raw if len(l) > 0}

        lista_relatorio = []
        for nome_tecnico in MAPEAMENTO_TECNICOS.keys():
            tempos_raw = mapa_tme.get(nome_tecnico, [])
            segundos_validos = [converter_para_segundos(t) for t in tempos_raw]
            segundos_validos = [s for s in segundos_validos if s is not None]
            media_seg = sum(segundos_validos) / len(segundos_validos) if segundos_validos else 0
            
            total_e = counts_geral.get(nome_tecnico, 0)
            
            lista_relatorio.append({
                "Colaborador": nome_tecnico,
                "Mês/Ano": f"{mes:02d}/{ano}",
                "Total Encerramentos": total_e,
                "Média TME (Mensal)": formatar_segundos(media_seg)
            })
            
        df_final = pd.DataFrame(lista_relatorio)
        return df_final.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
    except Exception as e:
        st.error(f"Erro ao gerar CSV: {e}")
        return None

@st.cache_data(ttl=900, show_spinner="🤖 Coletando base unificada do ERP (Mês Passado e Atual)...")
def sincronizar_periodo_completo():
    fuso = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(fuso)
    
    primeiro_dia_atual = agora.replace(day=1)
    ultimo_dia_passado = primeiro_dia_atual - timedelta(days=1)
    dt_ini = ultimo_dia_passado.replace(day=1)
    
    ultimo_dia_atual_num = calendar.monthrange(agora.year, agora.month)[1]
    dt_fim = agora.replace(day=ultimo_dia_atual_num)
    
    return executar_robo_erp_periodo(dt_ini, dt_fim)

def desenhar_aba(dados_tme_raw, df_bruto, tecnico_sel, mes, ano, dia_limite):
    counts = {}
    total_enc = 0
    
    if df_bruto is not None and not df_bruto.empty:
        df = df_bruto.copy()
        
        col_data = None
        for c in df.columns:
            c_low = str(c).lower()
            if "data" in c_low and ("encerrament" in c_low or "fechament" in c_low or "resolu" in c_low):
                col_data = c
                break
                
        if not col_data:
            for c in df.columns:
                if "encerrament" in str(c).lower() or "fechament" in str(c).lower():
                    col_data = c
                    break
                    
        if not col_data:
            cols_com_data = [c for c in df.columns if "data" in str(c).lower()]
            col_data = cols_com_data[-1] if cols_com_data else df.columns[0]
        
        df['DATA_DT'] = pd.to_datetime(df[col_data], dayfirst=True, errors='coerce')
        
        possiveis_cols = ["Usuário Encerramento", "Usuario Encerramento", "Atendente", "Responsável", "Responsavel", "Nome", "Técnico", "Tecnico"]
        col_atendente = next((c for p in possiveis_cols for c in df.columns if p.lower() in str(c).lower()), None)
        if not col_atendente:
            col_atendente = df.columns[3] if len(df.columns) > 3 else df.columns[0]
        
        df['Tec_Formatado'] = df[col_atendente].apply(lambda x: next(
            (p_nome for p_nome, erp_nome in MAPEAMENTO_TECNICOS.items() 
             if super_limpeza(erp_nome) in super_limpeza(str(x))), 
            None
        ))
        
        df_tec = df[
            (df['Tec_Formatado'] == tecnico_sel) & 
            (df['DATA_DT'].dt.month == mes) & 
            (df['DATA_DT'].dt.year == ano)
        ].dropna(subset=['DATA_DT'])
        
        total_enc = len(df_tec)
        
        if not df_tec.empty:
            counts = df_tec['DATA_DT'].dt.day.astype(int).value_counts().to_dict()

    mapa_tme = {}
    if dados_tme_raw:
        for linha in dados_tme_raw:
            if len(linha) > 0:
                nome_planilha = str(linha[0]).strip()
                mapa_tme[nome_planilha] = linha[3:]
                
    tempos_raw = mapa_tme.get(tecnico_sel.strip(), [])
    while len(tempos_raw) < 31: tempos_raw.append("") 

    tempos_seg = [converter_para_segundos(t) for t in tempos_raw[:dia_limite]]
    validos = [t for t in tempos_seg if t is not None]
    media_seg = sum(validos) / len(validos) if validos else 0
    
    c1, c2, c3 = st.columns([2,1,1])
    with c1: st.subheader(f"👤 {tecnico_sel}")
    with c2: st.metric("Total Encerramentos", f"{total_enc} un")
    with c3: st.metric("TME Médio", formatar_segundos(media_seg))
    
    st.progress(min(total_enc/550, 1.0), text=f"Meta Normal (550): {total_enc}")
    st.progress(min(total_enc/681, 1.0), text=f"Super Meta (681): {total_enc}")
    st.divider()
    
    dias_semana = ["Domingo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"]
    cols_header = st.columns(7)
    for i, col in enumerate(cols_header):
        col.markdown(f"<div style='text-align:center; color:#8b949e; font-weight:bold;'>{dias_semana[i]}</div>", unsafe_allow_html=True)

    primeiro_dia_semana, num_dias = calendar.monthrange(ano, mes)
    offset_dias = (primeiro_dia_semana + 1) % 7 
    
    dia_atual = 1
    placeholder_vazio = "<div style='min-height: 90px; visibility: hidden;'></div>"

    for semana in range(6): 
        cols = st.columns(7)
        for dia_semana in range(7):
            with cols[dia_semana]:
                if (semana == 0 and dia_semana < offset_dias) or (dia_atual > num_dias):
                    st.markdown(placeholder_vazio, unsafe_allow_html=True)
                else:
                    qtd = counts.get(dia_atual, 0)
                    tme_dia = str(tempos_raw[dia_atual - 1]).strip() if (dia_atual - 1) < len(tempos_raw) else ""
                    
                    cor_tme = "#8b949e"
                    seg_dia = converter_para_segundos(tme_dia)
                    if tme_dia in ["FORA", "---", ""]:
                        cor_tme = "#FFD700" 
                        tme_dia = "FORA" if tme_dia == "FORA" else "---"
                    elif seg_dia and seg_dia > 900: 
                        cor_tme = "#FF4B4B" 
                    elif seg_dia:
                        cor_tme = "#00FF7F" 

                    hoje = datetime.now(pytz.timezone('America/Sao_Paulo'))
                    e_hoje = (dia_atual == hoje.day and mes == hoje.month and ano == hoje.year)
                    
                    bg_color = "#2a313d" if e_hoje else "#1d2129"
                    borda_color = "#58a6ff" if e_hoje else "#30363d"
                    label_color = "#ffffff" if qtd > 0 else "#8b949e"

                    st.markdown(f"""
                        <div style="background:{bg_color}; padding:10px; border-radius:8px; border:1px solid {borda_color}; margin-bottom:10px; text-align:center;">
                            <div style="color:#8b949e; font-size:0.8rem; margin-bottom:4px;">{dia_atual:02d}/{mes:02d}</div>
                            <div style="color:{label_color}; font-size:1.2rem; font-weight:bold;">E: {qtd}</div>
                            <div style="color:{cor_tme}; font-size:0.85rem; margin-top:4px;">⏱️ {tme_dia}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    dia_atual += 1

def render():
    st_autorefresh(interval=15 * 60 * 1000, key="refresh_perf")
    fuso = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(fuso)
    
    mes_atual = agora.month
    dt_p = agora.replace(day=1) - timedelta(days=1)
    mes_passado = dt_p.month
    
    st.markdown("### 📈 Painel de Performance Operacional")
    
    with st.spinner("⏳ Sincronizando Planilhas..."):
        dados_planilha_historico = carregar_tme_por_mes(mes_passado)
        dados_planilha_atual = carregar_tme_por_mes(mes_atual)
    
    if not dados_planilha_atual: 
        st.error("Falha ao carregar Planilha Google.")
        return
        
    nomes = sorted([l[0] for l in dados_planilha_atual if len(l) > 0 and l[0] in MAPEAMENTO_TECNICOS])
    
    selecionado = st.selectbox("Selecione o Técnico:", nomes, label_visibility="collapsed")

    df_bruto_unificado = sincronizar_periodo_completo()
    
    tab1, tab2 = st.tabs([f"📅 Mês Atual ({mes_atual:02d}/{agora.year})", f"⏪ Mês Anterior ({mes_passado:02d}/{dt_p.year})"])

    with tab1:
        csv_atual = preparar_csv_consolidado(dados_planilha_atual, df_bruto_unificado, mes_atual, agora.year)
        if csv_atual:
            st.download_button(
                label="📥 Baixar Relatório Consolidado (Mês Atual)",
                data=csv_atual,
                file_name=f"performance_{mes_atual}_{agora.year}.csv",
                mime="text/csv"
            )
        st.divider()
        desenhar_aba(dados_planilha_atual, df_bruto_unificado, selecionado, mes_atual, agora.year, agora.day)
    
    with tab2:
        csv_passado = preparar_csv_consolidado(dados_planilha_historico, df_bruto_unificado, mes_passado, dt_p.year)
        if csv_passado:
            st.download_button(
                label="📥 Baixar Relatório Consolidado (Mês Anterior)",
                data=csv_passado,
                file_name=f"performance_{mes_passado}_{dt_p.year}.csv",
                mime="text/csv"
            )
        st.divider()
        desenhar_aba(dados_planilha_historico, df_bruto_unificado, selecionado, mes_passado, dt_p.year, calendar.monthrange(dt_p.year, mes_passado)[1])

if __name__ == "__main__":
    render()
