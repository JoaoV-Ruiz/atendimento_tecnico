import time
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import pytz
import random

def render():
    # --- GERADOR DE DADOS FICTÍCIOS (MODO DEMO) ---
    def gerar_dados_mock():
        atendentes = [
            "ALISSON DO COUTO GUERREIRO", "IGOR SALDANHA", 
            "JOÃO VITOR RUIZ BARBOZA", "VINICIUS COPPA", 
            "JULIA DA SILVA DUARTE", "KAUÃ LARRI GOCKS DA SILVEIRA", 
            "CAIO REIS", "DIOGO BITENCOURT", "MARIA EDUARDA BARBOSA VIANA", 
            "NATHALI VALLIER", "RICHER FALCÃO ARAUJO", 
            "SINDEW CRIZEL NUNES", "CRISTIANO MARQUES", "FILIPE VIEIRA VAZ"
        ]
        
        # Gera 600 encerramentos fictícios distribuídos nos últimos 90 dias
        hoje = datetime.now()
        datas = [hoje - timedelta(days=random.randint(0, 90)) for _ in range(600)]
        
        # Cria um "peso" para dar variação no ranking (alguns técnicos com mais, outros com menos)
        pesos = [random.uniform(0.5, 1.5) for _ in atendentes]
        tecnicos_escolhidos = random.choices(atendentes, weights=pesos, k=600)
        
        df = pd.DataFrame({
            'DATA_REF': datas,
            'Atendente': tecnicos_escolhidos
        })
        
        df['MES_ANO'] = df['DATA_REF'].dt.strftime('%m/%Y')
        return df

    # --- AUTOMAÇÃO SIMULADA ---
    @st.cache_data(ttl=900, show_spinner=False)
    def disparar_automacao_cached():
        prog_container = st.empty()
        p_bar = prog_container.progress(0)
        
        try:
            # Simula as etapas do Selenium visualmente
            p_bar.progress(10, text="[DEMO] Simulando Login no ERP...")
            time.sleep(1)
            
            p_bar.progress(30, text="[DEMO] Acessando a Tela Antiga...")
            time.sleep(1)
            
            p_bar.progress(60, text="[DEMO] Aplicando Filtros (COP Encerramentos)...")
            time.sleep(1.5)
            
            p_bar.progress(80, text="[DEMO] 📥 Gerando dados fictícios...")
            df_mock = gerar_dados_mock()
            time.sleep(1)
            
            p_bar.progress(100, text="✅ Concluído!")
            time.sleep(1)
            prog_container.empty()
            
            hora_br = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%H:%M:%S")
            return {"dados": df_mock, "horario": hora_br}
            
        except Exception as e:
            st.error(f"Ocorreu um erro no robô simulado: {str(e)}")
            return None

    # --- LÓGICA DE EXIBIÇÃO (MANTIDA ORIGINAL) ---
    st.title("🚀 É A EQUIPE DO ENCERRAS!!! (Versão Demo)")
    st.info("💡 **Aviso de Portfólio:** A automação real do ERP com Selenium foi substituída por um gerador de dados fictícios para proteger credenciais e permitir a visualização do dashboard.")
    
    resultado = disparar_automacao_cached()
    
    if resultado and resultado.get("dados") is not None:
        df_completo = resultado["dados"]
        hora = resultado["horario"]
        
        if not df_completo.empty:
            st.markdown(f"**🕒 Última Sincronização Simulada:** `{hora}`")
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
        else: st.warning("⚠️ Nenhum dado encontrado na simulação.")
    else: st.info("⏳ Aguardando sincronização do ERP...")
