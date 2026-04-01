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

# [MAPEAMENTO_TECNICOS e funções de limpeza permanecem as mesmas]

@st.cache_data(ttl=900, show_spinner="Buscando encerramentos no ERP...")
def disparar_automacao_erp(download_path_obj, mes, ano):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # [Configurações de Prefs e Driver...]
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        wait = WebDriverWait(driver, 40)
        # 1. Login (Sua lógica de login aqui)
        # ...
        
        # 2. Navegação para filtros
        driver.get("https://erp.osirnet.com.br/all_solicitations#/")
        time.sleep(3)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@tooltip='Filtro avançado']"))).click()
        
        # [Lógica de selecionar equipe 'COP Encerramentos'...]

        # 3. FILTRO DE DATA DINÂMICO
        hj = datetime.now()
        ultimo_dia = calendar.monthrange(ano, mes)[1]
        
        data_ini = f"01/{mes:02d}/{ano}"
        # Se for o mês atual, limita até hoje para não dar erro no ERP
        data_fim = hj.strftime("%d/%m/%Y") if (mes == hj.month and ano == hj.year) else f"{ultimo_dia:02d}/{mes:02d}/{ano}"

        # Função React Input
        def forcar_input(dr, el, val):
            dr.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles:true}));", el, val)

        forcar_input(driver, driver.find_element(By.ID, "beginReportClosingDate"), data_ini)
        forcar_input(driver, driver.find_element(By.ID, "finalReportClosingDate"), data_fim)
        
        driver.find_element(By.XPATH, "//button[contains(., 'aplicar')]").click()
        time.sleep(10)

        # 4. Exportar e Analisar (Sua lógica de CSV aqui)
        # ... 
        # return analisar_dados_encerramentos(caminho_final, mes, ano)
        pass 

    except Exception as e:
        st.error(f"Erro Automação ({mes}/{ano}): {e}")
        return None
    finally:
        driver.quit()

def desenhar_conteudo_performance(dados_tme, df_erp, tecnico, mes, ano, dia_max):
    # Filtra os dados do técnico
    df_tec = df_erp[df_erp['Atendente_Planilha'] == tecnico] if df_erp is not None else pd.DataFrame()
    
    # Métricas
    col1, col2, col3 = st.columns([2,1,1])
    col2.metric("Total Encerramentos", f"{len(df_tec)} un")
    
    # Progress Bars (Metas)
    total = len(df_tec)
    st.progress(min(total/550, 1.0), text=f"Meta Normal: {total}/550")
    st.progress(min(total/681, 1.0), text=f"Super Meta: {total}/681")
    
    st.divider()
    
    # Grid de Histórico
    grid = st.columns(7)
    counts = df_tec['DATA_REF'].dt.day.value_counts().to_dict() if not df_tec.empty else {}
    
    # Mapeia TME da planilha
    mapa = {l[0]: l[3:] for l in dados_tme if len(l) > 0}
    dados_dias = mapa.get(tecnico, [""] * 31)

    for i in range(dia_max):
        dia = i + 1
        with grid[i % 7]:
            qtd = counts.get(dia, 0)
            tme_val = str(dados_dias[i]).strip() if i < len(dados_dias) else ""
            
            st.markdown(f"""
                <div style="background:#1d2129; padding:8px; border-radius:8px; border:1px solid #30363d; margin-bottom:8px; text-align:center;">
                    <small>{dia:02d}/{mes:02d}</small><br>
                    <b style="color:#4da3ff;">E: {qtd}</b><br>
                    <small>⏱️ {tme_val}</small>
                </div>
            """, unsafe_allow_html=True)

def render():
    apply_styles()
    fuso = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(fuso)
    
    # Datas para as abas
    m_atual, a_atual = agora.month, agora.year
    dt_p = agora.replace(day=1) - timedelta(days=1)
    m_pass, a_pass = dt_p.month, dt_p.year
    
    st.title("📈 Performance Unificada")
    
    # Carrega Lista de Técnicos
    dados_planilha = load_technical_data()
    if not dados_planilha: return
    tecnicos = sorted([l[0] for l in dados_planilha if len(l) > 0 and l[0] in MAPEAMENTO_TECNICOS])
    
    selecionado = st.selectbox("Selecione o Técnico:", tecnicos)
    
    tab1, tab2 = st.tabs([f"📅 {m_atual:02d}/{a_atual}", f"⏪ {m_pass:02d}/{a_pass}"])
    
    with tab1:
        df_a = disparar_automacao_erp(Path("temp_downloads"), m_atual, a_atual)
        desenhar_conteudo_performance(dados_planilha, df_a, selecionado, m_atual, a_atual, agora.day - 1)

    with tab2:
        df_p = disparar_automacao_erp(Path("temp_downloads"), m_pass, a_pass)
        ultimo_dia_p = calendar.monthrange(a_pass, m_pass)[1]
        desenhar_conteudo_performance(dados_planilha, df_p, selecionado, m_pass, a_pass, ultimo_dia_p)
