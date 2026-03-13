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
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from datetime import datetime
import traceback
from dotenv import load_dotenv
import pytz
from datetime import datetime

def realizar_coleta_e_envio_automatizado():
    """ Função que o servidor chamará mesmo se ninguém estiver logado """
    import pytz
    fuso_br = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(fuso_br)
    
    # 1. Executa a coleta (disparar_automacao)
    df, checados, tela = disparar_automacao() # Certifique-se que esta função use st.secrets
    
    if df is not None:
        # 2. Salva o Excel
        salvar_fechamento_diario(df, tela, checados)
        # 3. Envia para o Zulip/Chat
        executar_fluxo_completo() 
        return True
    return False
    
def render():
    load_dotenv()
    st_autorefresh(interval=30000, key="refresh_amarelos")
    
    URL_COLETA = "https://atendimento.osir.net.br/inviabilidade/huawei/filaProvisionamento.php"
    ARQUIVO_EXCEL = "fechamento_diario_osir.xlsx"
    ARQUIVO_TRAVA = "trava_relatorio.txt"
    
    TABELA_NOMES = {
        "396": "DIOGO TABORDA", "728": "VINICIUS COPPA", "734": "NATHALI VALLIER",
        "956": "ERICA MARLOW", "1153": "MARIA EDUARDA", "1163": "JULIA DUARTE",
        "1177": "KAUÃ GOCKS", "1318": "FILIPE VAZ", "1267": "ALISSON GUERREIRO",
        "931": "JOÃO VITOR RUIZ", "960": "RICHER ARAUJO", "667": "CRISTIANO MARQUES", 
        "441": "CAIO ALVES DOS REIS", "968": "SINDEW CRIZEL", "322" : "IGOR SALDANHA"
    }

    # --- FUNÇÃO DE SALVAMENTO (FECHAMENTO DIÁRIO) ---

    # --- CONFIGURAÇÕES ---
    URL_COLETA = "https://atendimento.osir.net.br/inviabilidade/huawei/filaProvisionamento.php"
    URL_CHAT = "https://chat.osirnet.com.br/accounts/login/"
    ARQUIVO_SAIDA = "historico_geral_osir.xlsx"
    ARQUIVO_TRAVA = "trava_relatorio.txt"

    # Credenciais
    EMAIL = os.getenv("EMAIL_CORP")
    SENHA = os.getenv("SENHA_SISTEMA")
    SENHA_ZULIP = os.getenv("SENHA_ZULIP")
    flag_mensagem = 0

    def executar_fluxo_completo():   
        # --- 1. COLETA DE DADOS ---
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Passo 1: Iniciando Coleta de Dados...")
        chrome_options = Options()
        chrome_options.add_argument("--headless=new") 
        
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 30)

        try:
            # Login no Sistema de Coleta
            driver.get(URL_COLETA)
            wait.until(EC.element_to_be_clickable((By.ID, "login"))).send_keys(EMAIL)
            driver.find_element(By.ID, "password").send_keys(SENHA)
            driver.find_element(By.NAME, "entrar").click()
            
            # Espera as tabelas carregarem
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tbody.busca-sucesso, tbody.busca-falha")))
            print(EMAIL)
            print(SENHA)
            time.sleep(5) 

            total_sucesso = len(driver.find_elements(By.CSS_SELECTOR, "tbody.busca-sucesso tr"))
            total_falha = len(driver.find_elements(By.CSS_SELECTOR, "tbody.busca-falha tr"))
            total_geral = total_sucesso + total_falha

            # --- 2. SALVAMENTO NO EXCEL ---
            agora = datetime.now()
            ARQUIVO_SAIDA_BANCO = "banco_dados_osir.xlsx"
            
            df_novo = pd.DataFrame({
                "Data": [agora.strftime("%d/%m/%Y")],
                "Hora": [agora.strftime("%H:%M:%S")],
                "Sucesso": [total_sucesso],
                "Falha": [total_falha],
                "Total": [total_geral]
            })

            try:
                if not os.path.exists(ARQUIVO_SAIDA_BANCO):
                    df_novo.to_excel(ARQUIVO_SAIDA_BANCO, index=False, sheet_name="Dados_Gerais")
                    print("✨ Banco de dados criado.")
                else:
                    df_antigo = pd.read_excel(ARQUIVO_SAIDA_BANCO, sheet_name="Dados_Gerais")
                    df_final = pd.concat([df_antigo, df_novo], ignore_index=True)
                    df_final.to_excel(ARQUIVO_SAIDA_BANCO, index=False, sheet_name="Dados_Gerais")
                    print(f"📥 Nova linha adicionada: {total_sucesso} S / {total_falha} F")
            except Exception as e:
                print(f"⚠️ Erro ao atualizar o banco de dados: {e}")

            # --- 3. ENVIO PARA O CHAT ---
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Passo 2: Acessando Chat...")
            driver.get(URL_CHAT)

            wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(EMAIL)
            driver.find_element(By.NAME, "password").send_keys(SENHA_ZULIP)
            driver.find_element(By.NAME, "button").click()

            print("Buscando Cauê na lista...")
            xpath_caue = "//span[contains(@class, 'conversation-partners-list') and contains(text(), 'Cauê Arócha')]"
            contato = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_caue)))
            driver.execute_script("arguments[0].scrollIntoView(true);", contato)
            time.sleep(1)
            contato.click()

            print("Enviando relatório...")
            textarea = wait.until(EC.element_to_be_clickable((By.ID, "compose-textarea")))
            
            mensagem_relatorio = (
                f"📊 *Relatório Automático de Provisionamento*\n"
                f"🕒 Horário: {agora.strftime('%H:%M:%S')}\n"
                f"----------------------------------\n"
                f"✅ *Total Sucesso:* {total_sucesso}\n"
                f"❌ *Total Falha:* {total_falha}\n"
                f"📈 *Total Geral:* {total_geral}\n"
                f"----------------------------------"
            )
            
            driver.execute_script("arguments[0].value = arguments[1];", textarea, mensagem_relatorio)
            driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", textarea)
            time.sleep(2)
            
            try:
                botao_enviar = driver.find_element(By.ID, "compose-send-button")
                driver.execute_script("arguments[0].click();", botao_enviar)
                print("🚀 Relatório enviado com sucesso!")
                flag_mensagem = 1
            except Exception as e:
                print(f"⚠️ Erro ao clicar no botão: {e}")

        except Exception as e:
            print(f"❌ Ocorreu um erro no fluxo: {e}")
        
        finally:
            driver.quit()
            print("Navegador fechado. Aguardando próximo agendamento...")


    def salvar_fechamento_diario(df_atual, total_tela, total_checados):
        agora = datetime.now()
        nome_aba = f"FECHAMENTO_{agora.strftime('%d-%m-%Y')}"
        
        # Verifica se já existe a aba de hoje para não duplicar no intervalo de 5min
        if os.path.exists(ARQUIVO_EXCEL):
            excel_file = pd.ExcelFile(ARQUIVO_EXCEL)
            if nome_aba in excel_file.sheet_names:
                return # Já salvou hoje, não faz nada

        todos_nomes = list(TABELA_NOMES.values())
        df_base = pd.DataFrame({
            "Colaborador": todos_nomes,
            "Qtd": 0,
            "Data_Fechamento": agora.strftime("%d/%m/%Y %H:%M"),
            "Total_Tela": total_tela,
            "Total_Checados": total_checados
        })

        df_base.set_index("Colaborador", inplace=True)
        if not df_atual.empty:
            for _, row in df_atual.iterrows():
                if row["Colaborador"] in df_base.index:
                    df_base.at[row["Colaborador"], "Qtd"] = row["Qtd"]
        df_base.reset_index(inplace=True)

        try:
            if not os.path.exists(ARQUIVO_EXCEL):
                with pd.ExcelWriter(ARQUIVO_EXCEL, engine='openpyxl') as writer:
                    df_base.to_excel(writer, sheet_name=nome_aba, index=False)
            else:
                with pd.ExcelWriter(ARQUIVO_EXCEL, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
                    df_base.to_excel(writer, sheet_name=nome_aba, index=False)
            st.toast(f"✅ Fechamento {nome_aba} salvo com sucesso!", icon="💾")
        except Exception as e:
            st.error(f"Erro ao salvar fechamento: {e}")

    # --- INICIALIZAÇÃO DO CACHE ---
    if 'dados_cache' not in st.session_state:
        st.session_state['dados_cache'] = None 
    if 'ultima_coleta' not in st.session_state:
        st.session_state['ultima_coleta'] = None

    # --- MOTOR DE COLETA ---
    def disparar_automacao():
        prog_container = st.empty()
        p_bar = prog_container.progress(0)
        
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        # Crie uma variável para o fuso de Brasília
        fuso_br = pytz.timezone('America/Sao_Paulo')
        
        # Quando for registrar a hora da coleta:
        st.session_state['ultima_coleta'] = datetime.now(fuso_br)
        driver = None
        try:
            driver = webdriver.Chrome(options=chrome_options)
            wait = WebDriverWait(driver, 30)
            p_bar.progress(30)
            driver.get(URL_COLETA)

            wait.until(EC.element_to_be_clickable((By.ID, "login"))).send_keys("joao.barboza@osirnet.com.br")
            driver.find_element(By.ID, "password").send_keys("699068983")
            driver.find_element(By.NAME, "entrar").click()

            p_bar.progress(60)
            wait.until(EC.presence_of_element_located((By.XPATH, "//a[@data-checado]")))
            time.sleep(3) 

            links = driver.find_elements(By.XPATH, "//a[@data-checado]")
            total_tela = len(links)
            contagem = {nome: 0 for nome in TABELA_NOMES.values()}
            total_checados = 0
            
            for link in links:
                try:
                    valor = link.get_attribute("data-checado")
                    if valor in TABELA_NOMES:
                        nome_colaborador = TABELA_NOMES[valor]
                        contagem[nome_colaborador] += 1
                        total_checados += 1
                except: continue

            df_resultado = pd.DataFrame(list(contagem.items()), columns=["Colaborador", "Qtd"])

            

            df_interface = df_resultado[df_resultado["Qtd"] > 0].sort_values(by="Qtd", ascending=False)
            p_bar.progress(100)
            time.sleep(1)
            prog_container.empty()
            
            return df_interface, total_checados, total_tela

        except Exception as e:
            st.error(f"❌ Erro na coleta: {e}")
            return None, 0, 0
        finally:
            if driver: driver.quit()

    # --- CONTROLE DE TRAVA DE DISPARO ---
    if 'ultimo_sucesso_relatorio' not in st.session_state:
        st.session_state['ultimo_sucesso_relatorio'] = None

    agora = datetime.now()
    HORA_TESTE = 23
    MINUTO_TESTE = 45 # Ajuste para o próximo minuto de teste
    data_hoje = agora.date()

    # Verifica se já rodou hoje (compara a data do último sucesso com hoje)
    ja_enviou_hoje = False
    if st.session_state['ultimo_sucesso_relatorio']:
        if st.session_state['ultimo_sucesso_relatorio'].date() == data_hoje:
            ja_enviou_hoje = True

    # --- FLUXO DO RELATÓRIO AGENDADO (VERSÃO BLINDADA COM ARQUIVO) ---
    if agora.hour == HORA_TESTE and agora.minute == MINUTO_TESTE:
        
        # Verifica se o arquivo de trava existe e se é de hoje
        ja_rodou_com_arquivo = False
        if os.path.exists(ARQUIVO_TRAVA):
            data_arquivo = datetime.fromtimestamp(os.path.getmtime(ARQUIVO_TRAVA)).date()
            if data_arquivo == agora.date():
                ja_rodou_com_arquivo = True

        if not ja_rodou_com_arquivo:
            # 1. CRIA A TRAVA NO DISCO IMEDIATAMENTE
            with open(ARQUIVO_TRAVA, "w") as f:
                f.write(f"Relatorio enviado em: {agora.strftime('%H:%M:%S')}")
            
            st.warning(f"⚠️ Horário atingido! Iniciando processo único via trava de disco...")
            
            # 2. Executa a coleta e envio
            df_para_envio, checados_envio, tela_envio = disparar_automacao()
            
            if df_para_envio is not None:
                salvar_fechamento_diario(df_para_envio, tela_envio, checados_envio)
                executar_fluxo_completo()
                
                # Sincroniza o session_state também por segurança
                st.session_state['ultimo_sucesso_relatorio'] = agora
                st.success("✅ Relatório finalizado com sucesso!")
                time.sleep(2)
                st.rerun()
            else:
                # Se falhou, deleta o arquivo para permitir que o próximo refresh tente de novo
                if os.path.exists(ARQUIVO_TRAVA):
                    os.remove(ARQUIVO_TRAVA)
                st.session_state['ultimo_sucesso_relatorio'] = None

    # --- DISPARO NORMAL DO MONITOR (CARREGAMENTO) ---
    # Só entra aqui se NÃO for a hora do relatório OU se o relatório já tiver sido enviado
    if not (agora.hour == HORA_TESTE and agora.minute == MINUTO_TESTE) or ja_enviou_hoje:
        
        # Se o cache está vazio, força a primeira coleta
        if st.session_state['dados_cache'] is None:
            df, checados, tela = disparar_automacao()
            if df is not None:
                st.session_state['dados_cache'] = (df, checados, tela)
                st.session_state['ultima_coleta'] = agora
                # Removido st.rerun() daqui para evitar travar o carregamento inicial
                
        # Se já tem cache, mas passaram 5 minutos, atualiza
        elif (agora - st.session_state['ultima_coleta'] >= timedelta(minutes=5)):
            df, checados, tela = disparar_automacao()
            if df is not None:
                st.session_state['dados_cache'] = (df, checados, tela)
                st.session_state['ultima_coleta'] = agora
                st.rerun()

    st.title("📊 Monitor de Provisionamento (Amarelos)")
    aba_monitor, aba_historico = st.tabs(["🖥️ Painel Realtime", "📂 Fechamentos Diários"])
    
    with aba_monitor:
        if st.session_state['dados_cache']:
            df_dados, total_checados, total_tela = st.session_state['dados_cache']
            st.info(f"🕒 Monitorando em tempo real. Última leitura: {st.session_state['ultima_coleta'].strftime('%H:%M:%S')}")
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Fila Total", total_tela)
            m2.metric("Checados", total_checados)
            m3.metric("Pendente", total_tela - total_checados)

            st.divider()
            c1, c2 = st.columns([1, 1.5])
            with c1:
                st.dataframe(df_dados, use_container_width=True, hide_index=True)
            with c2:
                st.bar_chart(df_dados.set_index("Colaborador"))
        else:
            st.info("Iniciando monitoramento...")

    with aba_historico:
        st.subheader("Histórico de Fechamentos (23:45)")
        if os.path.exists(ARQUIVO_EXCEL):
            excel_file = pd.ExcelFile(ARQUIVO_EXCEL)
            abas = list(reversed(excel_file.sheet_names))
            
            if abas:
                selecionada = st.selectbox("Selecione o dia do fechamento:", abas)
                df_h = pd.read_excel(ARQUIVO_EXCEL, sheet_name=selecionada)
                
                st.write(f"### Dados de {selecionada}")
                st.dataframe(df_h.sort_values(by="Qtd", ascending=False), use_container_width=True, hide_index=True)
                
                with open(ARQUIVO_EXCEL, "rb") as f:
                    st.download_button("📥 Baixar Planilha de Fechamentos", f, file_name=ARQUIVO_EXCEL)
            else:
                st.info("Nenhum fechamento diário registrado ainda.")
        else:
            st.info("O arquivo de fechamento será criado hoje às 23:45.")
