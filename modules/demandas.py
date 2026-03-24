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
    
    # 1. INICIALIZAÇÃO DE ESTADOS
    chaves_texto = ["nome_text", "prot_text", "prot_demanda_text", "cto_text", "sinal_text", "coords_text", "obs_text"]
    for key in chaves_texto:
        if key not in st.session_state: st.session_state[key] = ""
    
    if "tec_select" not in st.session_state: st.session_state["tec_select"] = " "
    if "tipo_proto_key" not in st.session_state: st.session_state["tipo_proto_key"] = "Ativação"
    if "tipo_caixa_key" not in st.session_state: st.session_state["tipo_caixa_key"] = "1x16"
    if "problema_key" not in st.session_state: st.session_state["problema_key"] = "CTO/porta sem sinal"
    if "sem_id_key" not in st.session_state: st.session_state["sem_id_key"] = "Não"

    # 2. FUNÇÕES DE SUPORTE
    def conectar_google_sheets():
        try:
            creds_json = st.secrets.get("GOOGLE_JSON_CREDENTIALS") or st.secrets.get("GOOGLE_JSON_CREDENTIALS_2")
            spreadsheet_url = st.secrets.get("URL_PLANILHA_DEMANDA")
            if not creds_json or not spreadsheet_url: return None
            creds_info = json.loads(creds_json)
            if "private_key" in creds_info:
                creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
            return gspread.authorize(creds).open_by_url(spreadsheet_url.strip()).get_worksheet(0)
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
        for key in chaves_texto: st.session_state[key] = ""
        st.session_state["tec_select"] = " "
        st.session_state["tipo_proto_key"] = "Ativação"
        st.session_state["tipo_caixa_key"] = "1x16"
        st.session_state["problema_key"] = "CTO/porta sem sinal"
        st.session_state["sem_id_key"] = "Não"
        for i in range(1, 17):
            if f"p_{i}" in st.session_state: st.session_state[f"p_{i}"] = False
        if "p_todos" in st.session_state: st.session_state["p_todos"] = False
        st.rerun()

    # --- INTERFACE ---
    st.title("📶 Registro de Campo")
    
    # 1. Linha Superior: Técnico e Protocolo Demanda
    col_t1, col_t2 = st.columns([1.5, 1])
    with col_t1:
        tecnico_selecionado = st.selectbox("Técnico Responsável", LISTA_TECNICOS, key="tec_select")
    with col_t2:
        protocolo_demanda = st.text_input("Protocolo da Demanda", key="prot_demanda_text")

    st.markdown("---")

    # 2. BLOCO DE CAMPOS ORGANIZADOS (Exatamente como na Imagem)
    col_esquerda, col_direita = st.columns([1.5, 1])

    with col_esquerda:
        nome_cliente = st.text_input("Nome do Cliente", key="nome_text")
        protocolo = st.text_input("Protocolo da Solicitação", key="prot_text")
        num_cto = st.text_input("Número da CTO", key="cto_text")
        sinal_cto = st.text_input("Sinal da CTO (Power Meter)", key="sinal_text")
        
        # Problema identificado fica na esquerda, abaixo dos inputs
        st.write(" ")
        problema = st.radio("Problema identificado:", ["CTO/porta sem sinal", "CTO cheia", "CTO/porta com sinal fora do padrão"], key="problema_key")

    with col_direita:
        tipo_proto = st.radio("Tipo de Protocolo:", ["Ativação", "Manutenção"], key="tipo_proto_key", horizontal=True)
        st.write(" ") # Espaçamento para alinhar
        tipo_caixa = st.radio("Tipo da Caixa:", ["1x16", "1x8"], key="tipo_caixa_key", horizontal=True)
        
        coords = st.text_input("Coordenadas (Lat, Long)", key="coords_text")
        cidade_detectada = buscar_cidade(coords)
        if cidade_detectada:
            st.info(f"📍 Localidade: **{cidade_detectada}**")
            
        sem_id = st.radio("Caixa sem identificação?", ["Sim", "Não"], key="sem_id_key", horizontal=True)
        
        # Observações agora fica aqui, na direita, fechando o bloco
        observacoes = st.text_area("Observações Adicionais (Opcional):", key="obs_text", height=110)

    # --- Restante do código (Portas, Botões e Máscara) ---

    # 4. Portas (Aparece se o problema for falta de sinal)
    portas_selecionadas = []
    if problema == "CTO/porta sem sinal":
        st.write("---")
        st.markdown("**Selecione as portas afetadas:**")
        check_todos = st.checkbox("Selecionar TODAS", key="p_todos")
        if check_todos:
            portas_selecionadas = ["TODAS"]
        else:
            max_p = 16 if tipo_caixa == "1x16" else 8
            cols_p = st.columns(8)
            for i in range(1, max_p + 1):
                with cols_p[(i-1) % 8]:
                    if st.checkbox(f"P{i}", key=f"p_{i}"):
                        portas_selecionadas.append(str(i))

    st.divider()

    # 5. Botões de Ação
    c_limpar, c_salvar = st.columns(2)
    with c_limpar:
        st.button("🗑️ Limpar Formulário", on_click=reset_form, use_container_width=True)
    with c_salvar:
        if st.button("💾 Salvar na Planilha", type="primary", use_container_width=True):
            if tecnico_selecionado == " " or not nome_cliente:
                st.warning("Preencha o Técnico e o Nome do Cliente!")
            else:
                aba = conectar_google_sheets()
                if aba:
                    try:
                        detalhes_p = f" (Portas: {', '.join(portas_selecionadas)})" if portas_selecionadas else ""
                        obs_final = f" | OBS: {observacoes}" if observacoes else ""
                        prob_f = problema + detalhes_p + obs_final
                        data_reg = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        nova_linha = [data_reg, cidade_detectada, tecnico_selecionado, protocolo, prob_f, protocolo_demanda]
                        aba.append_row(nova_linha)
                        st.toast("Dados registrados com sucesso!", icon="✅")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

    # --- MÁSCARA ---
    def ck(o_s, o_a): return "(X)" if o_s == o_a else "( )"
    txt_p = f"\n          Portas Afetadas: {', '.join(portas_selecionadas)}" if portas_selecionadas else ""
    txt_obs = f"\nOBSERVAÇÕES: {observacoes}" if observacoes else ""
    
    mascara = f"""Nome do Cliente: {nome_cliente}
Protocolo da Solicitação: {protocolo}
Localidade: {cidade_detectada}
=================================================
Tipo de Protocolo: {ck(tipo_proto, "Ativação")} Ativação {ck(tipo_proto, "Manutenção")} Manutenção
=================================================
Tipo da Caixa: {ck(tipo_caixa, "1x16")} 1x16 {ck(tipo_caixa, "1x8")} 1x8

Problema: {ck(problema, "CTO/porta sem sinal")} CTO/porta sem sinal {txt_p}
          {ck(problema, "CTO cheia")} CTO cheia
          {ck(problema, "CTO/porta com sinal fora do padrão")} CTO/porta com sinal fora do padrão
{txt_obs}
          
Número da CTO: {num_cto}
Sinal da CTO: {sinal_cto}
Coordenadas: {coords}
=================================================
Caixa sem identificação: {ck(sem_id, "Sim")} Sim {ck(sem_id, "Não")} Não"""

    st.subheader("📄 Máscara para Copiar")
    
    st.subheader("📄 Máscara para Copiar")
    
    # Criamos um estilo que "trava" o tamanho da fonte para tudo que estiver lá dentro
    st.markdown(f"""
        <div style="
            background-color: #161b22; 
            color: #7ee787; 
            padding: 20px; 
            border-radius: 10px; 
            border: 1px solid #30363d;
            font-family: 'Courier New', Courier, monospace;
            white-space: pre-wrap;
            line-height: 1.6;
            font-size: 15px !important;
        ">
            <span style="color: #7ee787 !important; font-size: 15px !important; font-weight: normal !important;">
{mascara}
            </span>
        </div>
    """, unsafe_allow_html=True)

    st.write("") # Espaçamento

    # Mantenha o seu botão de copiar (JS) logo abaixo
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
