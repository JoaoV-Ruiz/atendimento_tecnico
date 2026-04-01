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

# --- MAPEAMENTO E SUPORTE (MANTIDOS) ---
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

def super_limpeza(texto):
    if not isinstance(texto, str): return ""
    texto = texto.upper()
    texto = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in texto if not unicodedata.combining(c)])

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

# --- CARREGAMENTO DE DADOS ---

@st.cache_data(ttl=600)
def load_technical_data(aba_nome="AtendimentoTécnico"):
    url = st.secrets.get("SPREADSHEET_URL")
    creds_json_str = st.secrets.get("GOOGLE_JSON_CREDENTIALS_2") or st.secrets.get("GOOGLE_JSON_CREDENTIALS")
    if not url or not creds_json_str: return None
    try:
        from google.oauth2.service_account import Credentials
        scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds_dict = json.loads(creds_json_str)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_url(url)
        # Tenta carregar a aba do mês (você precisará garantir que a planilha tenha abas nomeadas ex: "03-2026")
        # Por enquanto, mantemos a lógica da aba fixa se não houver abas por mês
        sheet = spreadsheet.worksheet(aba_nome)
        return sheet.get("A8:AF20")
    except: return None

@st.cache_data(ttl=900)
def disparar_automacao_erp(download_path_obj, mes, ano):
    # A lógica da automação permanece a mesma, apenas passando mes/ano no filtro de data
    # ... (Sua função Selenium completa aqui dentro, ajustando os filtros de data para mes/ano)
    # Importante: No seu código original, a data de fim estava pegando hj.replace(day=...)
    # Ajuste para: fim_mes = calendar.monthrange(ano, mes)[1] e usar mes/ano passados como parâmetro.
    pass 

# --- INTERFACE PRINCIPAL ---

def render_aba_performance(dados_tme_brutos, df_erp, tecnico, mes, ano, dia_limite):
    """Função para desenhar o conteúdo da aba (Métricas + Progressos + Grid)"""
    if not dados_tme_brutos:
        st.warning(f"Sem dados para {mes:02d}/{ano}")
        return

    df_tec_erp = df_erp[df_erp['Atendente_Planilha'] == tecnico] if df_erp is not None else pd.DataFrame()
    total_atual = len(df_tec_erp)
    meta_normal = 550
    super_meta = 681

    # TME - Tratamento
    mapa = {l[0]: l for l in dados_tme_brutos if len(l) > 0}
    if tecnico not in mapa:
        st.error("Técnico não encontrado na base deste mês.")
        return
        
    linha_tecnico = mapa[tecnico]
    dados_tecnico_raw = linha_tecnico[3:]
    
    # Pega apenas até o dia limite (hoje-1 para mês atual, ou mês cheio para passado)
    tempos_seg = [converter_para_segundos(t) for t in dados_tecnico_raw[:dia_limite]]
    tempos_validos = [s for s in tempos_seg if s is not None]
    tme_acumulado = formatar_segundos(sum(tempos_validos)/len(tempos_validos)) if tempos_validos else "00:00:00"

    # Métricas Topo
    c_n, c_m1, c_m2 = st.columns([2, 1, 1])
    with c_n:
        st.markdown(f"#### {tecnico}")
        st.caption(f"Referência: {mes:02d}/{ano}")
    with c_m1: st.metric("TME Acumulado", tme_acumulado)
    with c_m2: st.metric("Total ENC", f"{total_atual} un")

    # Progress Bars
    p_normal = min(total_atual / meta_normal, 1.0)
    p_super = min(total_atual / super_meta, 1.0)
    cm1, cm2 = st.columns(2)
    with cm1:
        st.markdown(f"**🎯 Meta Normal ({meta_normal})**")
        st.progress(p_normal)
    with cm2:
        st.markdown(f"**🚀 Super Meta ({super_meta})**")
        st.progress(p_super)

    st.divider()

    # Histórico Diário
    st.subheader("📅 Histórico Diário")
    grid = st.columns(7)
    counts_enc = df_tec_erp['DATA_REF'].dt.day.value_counts().to_dict() if not df_tec_erp.empty else {}

    for i in range(dia_limite):
        dia = i + 1
        with grid[i % 7]:
            val_tme = str(dados_tecnico_raw[i]).strip() if i < len(dados_tecnico_raw) else ""
            seg = converter_para_segundos(val_tme)
            qtd = counts_enc.get(dia, 0)

            cor_tme = "#FFFFFF"
            if val_tme in ["", "FORA"]: cor_tme = "#FFD700"; val_tme = "FORA"
            elif seg is not None and seg > 15: cor_tme = "#FF4B4B"

            st.markdown(f"""
                <div style="background:#1d2129; padding:10px; border-radius:10px; border:1px solid #30363d; margin-bottom:10px; text-align:center;">
                    <div style="color:#8b949e; font-size:0.75rem;">{dia:02d}/{mes:02d}</div>
                    <div style="font-size:1rem; font-weight:bold; color:{cor_tme};">⏱️ {val_tme}</div>
                    <div style="font-size:1rem; font-weight:bold; color:#4da3ff; border-top:1px solid #30363d; margin-top:5px;">E: {qtd}</div>
                </div>
            """, unsafe_allow_html=True)

def render():
    apply_styles()
    st_autorefresh(interval=10 * 60 * 1000, key="perf_refresh")

    fuso_br = pytz.timezone('America/Sao_Paulo')
    hoje = datetime.now(fuso_br)
    
    # Datas Mês Atual
    mes_atual = hoje.month
    ano_atual = hoje.year
    dia_ontem = hoje.day - 1

    # Datas Mês Anterior
    data_mes_passado = hoje.replace(day=1) - timedelta(days=1)
    mes_passado = data_mes_passado.month
    ano_passado = data_mes_passado.year
    dias_mes_passado = calendar.monthrange(ano_passado, mes_passado)[1]

    # Pastas
    base_dir = Path(__file__).parent.parent
    download_folder = base_dir / "temp_downloads"
    download_folder.mkdir(parents=True, exist_ok=True)

    # Carrega base de nomes (Usa a aba principal para pegar a lista de técnicos)
    base_nomes_raw = load_technical_data() # Mantém a aba fixa para pegar os nomes
    if not base_nomes_raw:
        st.warning("Aguardando base de dados da Planilha...")
        return

    lista_nomes = sorted([l[0] for l in base_nomes_raw if len(l) > 0 and l[0] in MAPEAMENTO_TECNICOS])

    st.markdown("### 📊 Performance de Atendimento")
    selecionado = st.selectbox("Selecione o Atendente:", options=lista_nomes)

    # Criando as Abas
    aba_atual, aba_passado = st.tabs([f"📅 Mês Atual ({mes_atual:02d}/{ano_atual})", f"⏪ Mês Anterior ({mes_passado:02d}/{ano_passado})"])

    with aba_atual:
        # Aqui você dispara a automação para o mês atual
        df_atual = disparar_automacao_erp(download_folder, mes_atual, ano_atual)
        render_aba_performance(base_nomes_raw, df_atual, selecionado, mes_atual, ano_atual, dia_ontem)

    with aba_passado:
        # Aqui você dispara a automação para o mês passado (O Selenium vai filtrar o período cheio)
        df_anterior = disparar_automacao_erp(download_folder, mes_passado, ano_passado)
        
        # Dica: Para o TME do mês passado ser correto, você precisaria de uma aba na planilha 
        # chamada por exemplo "AtendimentoTécnico_Passado". Se não tiver, ele vai mostrar os dados da atual.
        render_aba_performance(base_nomes_raw, df_anterior, selecionado, mes_passado, ano_passado, dias_mes_passado)
