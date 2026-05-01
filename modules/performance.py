import streamlit as st
import pandas as pd
import re
import calendar
import unicodedata
import pytz
from datetime import datetime, timedelta
import random

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

# --- 3. MOCKS PARA DEMONSTRAÇÃO (Substitui Google Sheets e Selenium) ---
@st.cache_data(ttl=600, show_spinner=False)
def carregar_tme_por_mes_mock(mes_numero):
    """Simula os dados vindos da planilha do Google"""
    dados_simulados = []
    for nome in MAPEAMENTO_TECNICOS.values():
        linha = [nome, "", ""] # Nome e colunas em branco que tinham na planilha original
        for dia in range(1, 32):
            # Gera tempos aleatórios, incluindo folgas ("FORA")
            if random.random() < 0.15:
                linha.append("FORA")
            else:
                m = random.randint(5, 25)
                s = random.randint(0, 59)
                linha.append(f"00:{m:02d}:{s:02d}")
        dados_simulados.append(linha)
    return dados_simulados

@st.cache_data(ttl=900, show_spinner="🤖 Coletando base unificada do ERP (Modo Demo)...")
def sincronizar_periodo_completo_mock():
    """Simula a exportação de CSV do ERP com dados falsos"""
    fuso = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(fuso)
    datas_simuladas = []
    tecnicos_simulados = []
    
    # Gera cerca de 1500 encerramentos divididos nos últimos 60 dias
    tecnicos_list = list(MAPEAMENTO_TECNICOS.values())
    for _ in range(1500):
        dias_atras = random.randint(0, 60)
        data_registro = agora - timedelta(days=dias_atras)
        datas_simuladas.append(data_registro.strftime("%d/%m/%Y %H:%M:%S"))
        tecnicos_simulados.append(random.choice(tecnicos_list))
        
    return pd.DataFrame({
        "Data Encerramento": datas_simuladas,
        "Usuário Encerramento": tecnicos_simulados
    })

# --- 4. LÓGICA MANTIDA ---
def preparar_csv_consolidado(dados_tme_raw, df_bruto, mes, ano):
    try:
        df_mes = pd.DataFrame()
        if df_bruto is not None and not df_bruto.empty:
            df = df_bruto.copy()
            df['DATA_DT'] = pd.to_datetime(df['Data Encerramento'], dayfirst=True, errors='coerce')
            df['Tec_Formatado'] = df['Usuário Encerramento']
            df_mes = df[(df['DATA_DT'].dt.month == mes) & (df['DATA_DT'].dt.year == ano)]

        counts_geral = df_mes['Tec_Formatado'].value_counts().to_dict() if not df_mes.empty else {}
        mapa_tme = {str(l[0]).strip(): l[3:] for l in dados_tme_raw if len(l) > 0}

        lista_relatorio = []
        for nome_tecnico in MAPEAMENTO_TECNICOS.keys():
            nome_formatado = MAPEAMENTO_TECNICOS[nome_tecnico]
            tempos_raw = mapa_tme.get(nome_formatado, [])
            segundos_validos = [converter_para_segundos(t) for t in tempos_raw]
            segundos_validos = [s for s in segundos_validos if s is not None]
            media_seg = sum(segundos_validos) / len(segundos_validos) if segundos_validos else 0
            
            total_e = counts_geral.get(nome_formatado, 0)
            
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

def desenhar_aba(dados_tme_raw, df_bruto, tecnico_sel, mes, ano, dia_limite):
    counts = {}
    total_enc = 0
    
    if df_bruto is not None and not df_bruto.empty:
        df = df_bruto.copy()
        df['DATA_DT'] = pd.to_datetime(df['Data Encerramento'], dayfirst=True, errors='coerce')
        df['Tec_Formatado'] = df['Usuário Encerramento']
        
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
    
    st.progress(min(total_enc/681, 1.0), text=f"Meta Normal (681): {total_enc}")
    st.progress(min(total_enc/800, 1.0), text=f"Super Meta (800): {total_enc}")
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
    fuso = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(fuso)
    
    mes_atual = agora.month
    dt_p = agora.replace(day=1) - timedelta(days=1)
    mes_passado = dt_p.month
    
    st.markdown("### 📈 Painel de Performance Operacional (Modo Demo)")
    st.info("💡 **Aviso de Portfólio:** Os dados apresentados neste calendário (Tempos Médios e Volumes) são gerados aleatoriamente para demonstrar a capacidade de renderização visual e processamento de datas do sistema.")
    
    with st.spinner("⏳ Sincronizando dados simulados..."):
        dados_planilha_historico = carregar_tme_por_mes_mock(mes_passado)
        dados_planilha_atual = carregar_tme_por_mes_mock(mes_atual)
        df_bruto_unificado = sincronizar_periodo_completo_mock()
        
    nomes = sorted([l[0] for l in dados_planilha_atual if len(l) > 0 and l[0] in MAPEAMENTO_TECNICOS.values()])
    
    selecionado = st.selectbox("Selecione o Técnico:", nomes, label_visibility="collapsed")
    
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
