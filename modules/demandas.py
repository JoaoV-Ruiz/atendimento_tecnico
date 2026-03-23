import streamlit as st
import streamlit.components.v1 as components
import json
import re
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from geopy.geocoders import Nominatim
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

# Configuração da página
st.set_page_config(page_title="Gerador Técnico Pro", page_icon="📶", layout="centered")

# --- LISTA DE TÉCNICOS ---
LISTA_TECNICOS = [
    " ", "Alisson G", "Caio Alves", "Filipe Vieira", "Kauã Larri", 
    "Igor Saldanha", "Richer Falcão", "João Vitor", "Diogo Bitencourt", 
    "Nathali Xabier", "Cristiano Weber", "Sindew Crizel", 
    "Vinicius Maciel", "Julia Da Silva"
]

# --- FUNÇÕES DE SUPORTE ---

def conectar_google_sheets():
    try:
        caminho_json = os.getenv("GOOGLE_PLANS_JSON")
        spreadsheet_url = os.getenv("URL_PLANILHA")
        
        if not caminho_json or os.path.isdir(caminho_json) or not os.path.exists(caminho_json):
            st.error("Erro no caminho do arquivo JSON no .env. Verifique se apontou para o ARQUIVO e não para a PASTA.")
            return None

        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(caminho_json, scope)
        client = gspread.authorize(creds)
        return client.open_by_url(spreadsheet_url).get_worksheet(0)
    except Exception as e:
        st.error(f"Erro ao conectar com Google Sheets: {e}")
        return None

def buscar_cidade(coords_texto):
    if not coords_texto: return ""
    try:
        nums = re.findall(r"[-+]?\d*\.\d+|\d+", coords_texto)
        if len(nums) >= 2:
            geolocator = Nominatim(user_agent="meu_gerador_tecnico_osir")
            location = geolocator.reverse(f"{nums[0]}, {nums[1]}", timeout=10)
            if location:
                address = location.raw.get('address', {})
                return address.get('city') or address.get('town') or address.get('village') or address.get('hamlet') or ""
    except: return "Erro na busca"
    return ""

def reset_form():
    """Callback para limpar o formulário. O rerun é automático após esta função."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]

# --- INTERFACE ---
st.title("📶 Registro de Campo")
st.subheader("Preencha as informações:")

col_top1, col_top2 = st.columns(2)
with col_top1:
    tecnico_selecionado = st.selectbox("Técnico Responsável", LISTA_TECNICOS, key="tec_select")
with col_top2:
    protocolo_demanda = st.text_input("Protocolo da Demanda", key="prot_demanda_text")

st.divider()

col_a, col_b = st.columns(2)
with col_a:
    nome_cliente = st.text_input("Nome do Cliente", key="nome_text")
with col_b:
    tipo_proto = st.radio("Tipo de Protocolo:", ["Ativação", "Manutenção"], key="tipo_proto_key", horizontal=True)

col1, col2 = st.columns(2)
with col1:
    protocolo = st.text_input("Protocolo da Solicitação", key="prot_text")
    tipo_caixa = st.radio("Tipo da Caixa:", ["1x16", "1x8"], key="tipo_caixa_key", horizontal=True)
    problema = st.radio("Problema:", ["CTO/porta sem sinal", "CTO cheia", "CTO/porta com sinal fora do padrão"], key="problema_key")

with col2:
    num_cto = st.text_input("Número da CTO", key="cto_text")
    sinal_cto = st.text_input("Sinal da CTO (Power Meter)", key="sinal_text")
    coords = st.text_input("Coordenadas (Lat, Long)", key="coords_text")
    sem_id = st.radio("Caixa sem identificação?", ["Sim", "Não"], key="sem_id_key", horizontal=True)

# --- LÓGICA DAS PORTAS ---
portas_selecionadas = []
if problema == "CTO/porta sem sinal":
    st.info("Selecione as portas afetadas:")
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    
    with col_p1:
        check_todos = st.checkbox("TODOS", key="p_todos")
    
    if check_todos:
        portas_selecionadas = ["TODAS"]
    else:
        for i in range(1, 17):
            col_target = [col_p1, col_p2, col_p3, col_p4][(i) % 4]
            with col_target:
                if st.checkbox(f"Porta {i}", key=f"p_{i}"):
                    portas_selecionadas.append(str(i))

cidade_detectada = buscar_cidade(coords)

# --- BOTÕES DE AÇÃO ---
c_limpar, c_salvar = st.columns(2)
with c_limpar:
    # Ao clicar aqui, reset_form roda e o streamlit faz o rerun sozinho
    st.button("🗑️ Limpar Informações", on_click=reset_form, use_container_width=True)

with c_salvar:
    if st.button("💾 Salvar na Planilha", type="primary", use_container_width=True):
        aba = conectar_google_sheets()
        if aba:
            try:
                problema_final = problema
                if portas_selecionadas:
                    problema_final += f" (Portas: {', '.join(portas_selecionadas)})"
                
                nova_linha = [cidade_detectada, tecnico_selecionado, protocolo, problema_final, protocolo_demanda]
                aba.append_row(nova_linha)
                st.toast("Dados registrados!", icon="✅")
                st.balloons()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

st.divider()

# --- MÁSCARA ---
def check(opcao_selecionada, opcao_alvo):
    return "(X)" if opcao_selecionada == opcao_alvo else "( )"

txt_portas = ""
if portas_selecionadas:
    txt_portas = f"\n          Portas Afetadas: {', '.join(portas_selecionadas)}"

mascara = f"""Nome do Cliente: {nome_cliente}
Protocolo da Solicitação: {protocolo}
Localidade: {cidade_detectada}
=================================================
Tipo de Protocolo: {check(tipo_proto, "Ativação")} Ativação {check(tipo_proto, "Manutenção")} Manutenção
=================================================
Tipo da Caixa: {check(tipo_caixa, "1x16")} 1x16 {check(tipo_caixa, "1x8")} 1x8

Problema: {check(problema, "CTO/porta sem sinal")} CTO/porta sem sinal {txt_portas}
          {check(problema, "CTO cheia")} CTO cheia
          {check(problema, "CTO/porta com sinal fora do padrão")} CTO/porta com sinal fora do padrão
          
Número da CTO: {num_cto}
Sinal da CTO: {sinal_cto}
Coordenadas: {coords}
=================================================
Caixa sem identificação: {check(sem_id, "Sim")} Sim {check(sem_id, "Não")} Não"""

st.subheader("📄 Máscara para Copiar")
st.code(mascara, language="text")

# Botão Copiar JS
js_copy = json.dumps(mascara)
components.html(f"""
    <button id="cp" style="width:100%; height:45px; background:#4da3ff; color:white; border:none; border-radius:8px; cursor:pointer; font-weight:bold; font-size:16px; font-family:sans-serif;">📋 COPIAR RELATÓRIO</button>
    <script>
    document.getElementById('cp').onclick = function() {{
        const t = document.createElement("textarea"); t.value = {js_copy}; document.body.appendChild(t);
        t.select(); document.execCommand('copy'); document.body.removeChild(t);
        this.style.background = '#28a745'; this.innerText = '✅ COPIADO!';
        setTimeout(() => {{ this.style.background = '#4da3ff'; this.innerText = '📋 COPIAR RELATÓRIO'; }}, 2000);
    }}
    </script>
""", height=60)
