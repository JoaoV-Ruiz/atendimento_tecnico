import streamlit as st
import streamlit.components.v1 as components
import json
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from geopy.geocoders import Nominatim
from datetime import datetime
from styles import apply_styles 

# --- CONFIGURAÇÕES DO MÓDULO ---
LISTA_TECNICOS = [
    " ", "Alisson G", "Caio Alves", "Filipe Vieira", "Kauã Larri", 
    "Igor Saldanha", "Richer Falcão", "João Vitor", "Diogo Bitencourt", 
    "Nathali Xabier", "Cristiano Weber", "Sindew Crizel", 
    "Vinicius Maciel", "Julia Da Silva"
]

def render():
    apply_styles()
    
    # 1. FUNÇÕES DE SUPORTE
    def conectar_google_sheets():
        try:
            creds_json = st.secrets.get("GOOGLE_PLANS_JSON") 
            spreadsheet_url = st.secrets.get("URL_PLANILHA_DEMANDA")
            if not creds_json or not spreadsheet_url:
                return None
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            creds_info = json.loads(creds_json)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
            return gspread.authorize(creds).open_by_url(spreadsheet_url).get_worksheet(0)
        except Exception as e:
            st.error(f"Erro ao conectar: {e}")
            return None

    @st.cache_data(ttl=3600)
    def buscar_cidade(coords_texto):
        if not coords_texto or len(coords_texto) < 5: return ""
        try:
            nums = re.findall(r"[-+]?\d*\.\d+|\d+", coords_texto)
            if len(nums) >= 2:
                geolocator = Nominatim(user_agent="gerador_tecnico_osir")
                location = geolocator.reverse(f"{nums[0]}, {nums[1]}", timeout=10)
                if location:
                    address = location.raw.get('address', {})
                    return address.get('city') or address.get('town') or address.get('village') or ""
        except: return "Erro na busca"
        return ""

    def reset_form():
        """
        Limpa todos os campos do session_state. 
        Para limpar as checkboxes de portas (p_1, p_2...), usamos um loop.
        """
        for key in list(st.session_state.keys()):
            # Mantemos apenas o que for essencial para o sistema (login/menu)
            if key not in ["auth_status", "menu_selecionado"]:
                del st.session_state[key]
        
        # Opcional: Definir valores padrões para chaves específicas se o del não bastar
        st.session_state["tec_select"] = LISTA_TECNICOS[0]
        st.session_state["tipo_proto_key"] = "Ativação"
        st.session_state["tipo_caixa_key"] = "1x16"
        st.session_state["sem_id_key"] = "Não"
        st.session_state["problema_key"] = "CTO/porta sem sinal"

    # --- INTERFACE ---
    st.title("📶 Registro de Campo")
    st.subheader("Informe os dados da operação:")

    with st.container():
        col_top1, col_top2 = st.columns(2)
        with col_top1:
            tecnico_selecionado = st.selectbox("Técnico Responsável", LISTA_TECNICOS, key="tec_select")
        with col_top2:
            protocolo_demanda = st.text_input("Protocolo da Demanda", key="prot_demanda_text")

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        nome_cliente = st.text_input("Nome do Cliente", key="nome_text")
        protocolo = st.text_input("Protocolo da Solicitação", key="prot_text")
    with col_b:
        tipo_proto = st.radio("Tipo de Protocolo:", ["Ativação", "Manutenção"], key="tipo_proto_key", horizontal=True)
        tipo_caixa = st.radio("Tipo da Caixa:", ["1x16", "1x8"], key="tipo_caixa_key", horizontal=True)

    col1, col2 = st.columns(2)
    with col1:
        num_cto = st.text_input("Número da CTO", key="cto_text")
        sinal_cto = st.text_input("Sinal da CTO (Power Meter)", key="sinal_text")
        problema = st.radio("Problema identificado:", ["CTO/porta sem sinal", "CTO cheia", "CTO/porta com sinal fora do padrão"], key="problema_key")

    with col2:
        coords = st.text_input("Coordenadas (Lat, Long)", key="coords_text")
        sem_id = st.radio("Caixa sem identificação?", ["Sim", "Não"], key="sem_id_key", horizontal=True)
        
        cidade_detectada = buscar_cidade(coords)
        if cidade_detectada:
            st.info(f"📍 Localidade: **{cidade_detectada}**")

    # --- PORTAS ---
    portas_selecionadas = []
    if problema == "CTO/porta sem sinal":
        st.write("---")
        st.markdown("**Selecione as portas afetadas:**")
        check_todos = st.checkbox("Selecionar TODAS", key="p_todos")
        
        if check_todos:
            portas_selecionadas = ["TODAS"]
        else:
            max_p = 16 if tipo_caixa == "1x16" else 8
            cols_p = st.columns(4)
            for i in range(1, max_p + 1):
                with cols_p[(i-1) % 4]:
                    if st.checkbox(f"Porta {i}", key=f"p_{i}"):
                        portas_selecionadas.append(str(i))

    st.divider()
    c_limpar, c_salvar = st.columns(2)
    with c_limpar:
        # O on_click chamará o reset_form e o rerun do Streamlit atualizará os widgets
        st.button("🗑️ Limpar Formulário", on_click=reset_form, use_container_width=True)

    with c_salvar:
        if st.button("💾 Salvar na Planilha", type="primary", use_container_width=True):
            if tecnico_selecionado == " " or not nome_cliente:
                st.warning("Preencha o Técnico e o Nome do Cliente!")
            else:
                aba = conectar_google_sheets()
                if aba:
                    try:
                        problema_final = problema
                        if portas_selecionadas:
                            problema_final += f" (Portas: {', '.join(portas_selecionadas)})"
                        
                        data_registro = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        nova_linha = [data_registro, cidade_detectada, tecnico_selecionado, protocolo, problema_final, protocolo_demanda]
                        
                        aba.append_row(nova_linha)
                        st.toast("Dados registrados com sucesso!", icon="✅")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

    # --- MÁSCARA ---
    def check_mark(opcao_selecionada, opcao_alvo):
        return "(X)" if opcao_selecionada == opcao_alvo else "( )"

    txt_portas = f"\n          Portas Afetadas: {', '.join(portas_selecionadas)}" if portas_selecionadas else ""

    mascara = f"""Nome do Cliente: {nome_cliente}
Protocolo da Solicitação: {protocolo}
Localidade: {cidade_detectada}
=================================================
Tipo de Protocolo: {check_mark(tipo_proto, "Ativação")} Ativação {check_mark(tipo_proto, "Manutenção")} Manutenção
=================================================
Tipo da Caixa: {check_mark(tipo_caixa, "1x16")} 1x16 {check_mark(tipo_caixa, "1x8")} 1x8

Problema: {check_mark(problema, "CTO/porta sem sinal")} CTO/porta sem sinal {txt_portas}
          {check_mark(problema, "CTO cheia")} CTO cheia
          {check_mark(problema, "CTO/porta com sinal fora do padrão")} CTO/porta com sinal fora do padrão
          
Número da CTO: {num_cto}
Sinal da CTO: {sinal_cto}
Coordenadas: {coords}
=================================================
Caixa sem identificação: {check_mark(sem_id, "Sim")} Sim {check_mark(sem_id, "Não")} Não"""

    st.subheader("📄 Máscara para Copiar")
    st.code(mascara, language="text")

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
