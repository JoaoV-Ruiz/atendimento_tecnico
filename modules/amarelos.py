import streamlit as st
import pandas as pd
import json
import pytz
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# 1. Configurações Iniciais e Acesso aos Secrets
st.set_page_config(page_title="Monitor de Produtividade", layout="wide")

# Buscando as configurações diretamente do st.secrets
# No Streamlit Cloud, você deve configurar:
# GOOGLE_JSON_CREDENTIALS = "..." (o conteúdo do JSON em string)
# SPREADSHEET_URL = "..."
try:
    GOOGLE_JSON_CREDENTIALS_2 = st.secrets["GOOGLE_JSON_CREDENTIALS_2"]
    SPREADSHEET_URL = st.secrets["SPREADSHEET_URL"]
except Exception as e:
    st.error("Erro: Variáveis de configuração não encontradas no st.secrets.")
    st.stop()

# --- FUNÇÕES DE APOIO E FORMATAÇÃO ---

def formatar_nome_exibicao(nome_bruto):
    """Transforma 'Contagem_10_04_2026_18_02' em '10/04/2026 - 18:02'"""
    try:
        partes = nome_bruto.split("_")
        if len(partes) >= 6:
            return f"{partes[1]}/{partes[2]}/{partes[3]} - {partes[4]}:{partes[5]}"
        elif len(partes) >= 4:
            return f"{partes[1]}/{partes[2]}/{partes[3]}"
        return nome_bruto
    except:
        return nome_bruto

def conectar_google_sheets():
    try:
        # Tenta carregar o JSON das credenciais
        creds_json = json.loads(GOOGLE_JSON_CREDENTIALS_2)
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
        client = gspread.authorize(creds)
        return client.open_by_url(SPREADSHEET_URL)
    except Exception as e:
        st.error(f"Erro na conexão com Google Sheets: {e}")
        return None

def listar_abas_historico(client):
    """Lista abas que começam com 'Contagem_'"""
    try:
        todas_abas = client.worksheets()
        nomes_reais = [aba.title for aba in todas_abas if aba.title.startswith("Contagem_")]
        return sorted(nomes_reais, reverse=True)
    except:
        return []

def coletar_dados_aba(client, nome_aba):
    """Lê aba específica e processa ranking/métricas"""
    try:
        aba = client.worksheet(nome_aba)
        dados = aba.get_all_records()
        if not dados: return pd.DataFrame(), 0, 0, 0
            
        df = pd.DataFrame(dados)
        
        # Processamento Quantidade
        if "Quantidade" in df.columns:
            df["Quantidade"] = pd.to_numeric(df["Quantidade"], errors="coerce").fillna(0).astype(int)
            total_checados = int(df["Quantidade"].sum())
        else:
            total_checados = 0

        # Processamento de Totais
        def extrair_maximo(col_name):
            if col_name in df.columns:
                val = pd.to_numeric(df[col_name], errors="coerce").max()
                return int(val) if pd.notna(val) else 0
            return 0

        t_s = extrair_maximo("total_sucesso")
        t_nc = extrair_maximo("total_nao_checados")
        
        # Processamento do Ranking (Apenas > 0)
        if "Nome" in df.columns and "Quantidade" in df.columns:
            df_ranking = df[df["Quantidade"] > 0][["Nome", "Quantidade"]].copy()
            df_ranking = df_ranking.rename(columns={"Nome": "Colaborador"})
            df_ranking = df_ranking.sort_values(by="Quantidade", ascending=False).reset_index(drop=True)
        else:
            df_ranking = pd.DataFrame()
        
        return df_ranking, total_checados, t_s, t_nc
    except Exception as e:
        st.error(f"Erro ao ler aba '{nome_aba}': {e}")
        return pd.DataFrame(), 0, 0, 0

# --- COMPONENTES VISUAIS ---

def exibir_metricas_cards(t_s, t_c, t_nc):
    m1, m2, m3 = st.columns(3)
    m1.metric("✅ Total Sucesso", t_s)
    m2.metric("🔍 Total Checados (Soma)", t_c)
    m3.metric("⏳ Não Checados", t_nc)
    st.divider()

def exibir_ranking_visual(df_rank):
    if not df_rank.empty:
        col_tabela, col_grafico = st.columns([1, 2])
        with col_tabela:
            df_vis = df_rank.copy()
            df_vis.index = df_vis.index + 1
            st.dataframe(df_vis, use_container_width=True)
        with col_grafico:
            st.bar_chart(df_rank.set_index("Colaborador"), color="#ffaa00")
    else:
        st.info("Nenhum dado de produtividade registrado.")

# --- RENDERIZAÇÃO ---

def render():
    st.title("📊 Sistema de Monitoramento")
    
    # Atualização automática a cada 30 segundos
    st_autorefresh(interval=30000, key="global_refresh")
    
    client = conectar_google_sheets()
    if not client: return

    tab_atual, tab_historico = st.tabs(["🚀 Tempo Real", "📅 Histórico Diário"])

    with tab_atual:
        st.subheader("Situação Atual")
        df_r, t_c, t_s, t_nc = coletar_dados_aba(client, "Dados Atuais")
        exibir_metricas_cards(t_s, t_c, t_nc)
        exibir_ranking_visual(df_r)

    with tab_historico:
        abas_reais = listar_abas_historico(client)
        
        if abas_reais:
            # Mapeamento para garantir nomes únicos (inclui hora no menu)
            mapeamento_abas = {formatar_nome_exibicao(aba): aba for aba in abas_reais}
            
            opcoes = list(mapeamento_abas.keys())
            selecao = st.selectbox("Escolha um relatório histórico:", opcoes)
            
            aba_real = mapeamento_abas[selecao]
            st.subheader(f"🏆 Ranking: {selecao}")
            
            df_h, _, _, _ = coletar_dados_aba(client, aba_real)
            exibir_ranking_visual(df_h)
        else:
            st.warning("Nenhuma aba de histórico encontrada.")

if __name__ == "__main__":
    render()
