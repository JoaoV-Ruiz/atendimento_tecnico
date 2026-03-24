import streamlit as st
import streamlit.components.v1 as components
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from datetime import datetime
import pytz

# --- FUNÇÃO DE CONEXÃO REVISADA ---
def conectar_google_sheets():
    try:
        # 1. Busca o Secret com parênteses no .get() ou direto no dicionário
        raw_creds = st.secrets.get("GOOGLE_JSON_CREDENTIALS")
        spreadsheet_url = st.secrets.get("URL_PLANILHA")

        if not raw_creds or not spreadsheet_url:
            st.error("❌ Erro: 'GOOGLE_JSON_CREDENTIALS' ou 'URL_PLANILHA' não configurados nos Secrets.")
            return None

        # 2. Carrega e limpa a chave privada
        creds_info = json.loads(raw_creds)
        if "private_key" in creds_info:
            creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        
        # 3. Autentica
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)
        
        # 4. Abre a planilha
        return client.open_by_url(spreadsheet_url).get_worksheet(0)
        
    except Exception as e:
        st.error(f"❌ Erro na conexão: {str(e)}")
        return None

def render():
    # Inicializa variáveis de controle no session_state se não existirem
    if 'batida_version' not in st.session_state:
        st.session_state.batida_version = 0
    if 'portas' not in st.session_state:
        st.session_state.portas = []
        
    v = st.session_state.batida_version

    # --- FUNÇÕES INTERNAS DE UI ---
    def salvar_campo(chave_permanente):
        key_temp = f"temp_{chave_permanente}_{v}"
        if key_temp in st.session_state:
            st.session_state[chave_permanente] = st.session_state[key_temp]

    def atualizar_portas():
        st.session_state.portas = [f"{i+1:02d}" for i in range(16) if st.session_state.get(f"c_batida_{i}")]

    def salvar_checkbox(indice):
        key_temp = f"temp_c_batida_{indice}_{v}"
        if key_temp in st.session_state:
            st.session_state[f"c_batida_{indice}"] = st.session_state[key_temp]
            atualizar_portas()

    def limpar_campos():
        campos_texto = ['batida_proto', 'batida_tec', 'batida_cx', 'anot_batida']
        for c in campos_texto:
            st.session_state[c] = ""
        for i in range(16):
            for pref in ['e_b_', 's_b_', 'id_b_']:
                st.session_state[f"{pref}{i}"] = ""
            st.session_state[f"c_batida_{i}"] = False
        st.session_state.portas = []
        st.session_state.batida_version += 1
        st.rerun()

    # Garante que os campos existam no estado antes de renderizar os widgets
    campos_init = ['batida_proto', 'batida_tec', 'batida_cx', 'anot_batida']
    for c in campos_init:
        if c not in st.session_state: st.session_state[c] = ""
    for i in range(16):
        for pref in ['e_b_', 's_b_', 'id_b_']:
            if f"{pref}{i}" not in st.session_state: st.session_state[f"{pref}{i}"] = ""
        if f"c_batida_{i}" not in st.session_state: st.session_state[f"c_batida_{i}"] = False

    st.title("📦 BATIDA DE CAIXA 3000")

    # --- CABEÇALHO ---
    c1, c2, c3, c_btn = st.columns([2, 2, 1, 0.5])
    with c1: st.text_input("PROTOCOLO", value=st.session_state.batida_proto, key=f"temp_batida_proto_{v}", on_change=salvar_campo, args=("batida_proto",))
    with c2: st.text_input("TÉCNICO", value=st.session_state.batida_tec, key=f"temp_batida_tec_{v}", on_change=salvar_campo, args=("batida_tec",))
    with c3: st.text_input("CAIXA", value=st.session_state.batida_cx, key=f"temp_batida_cx_{v}", on_change=salvar_campo, args=("batida_cx",))
    with c_btn:
        st.write(" ")
        if st.popover("🗑️").button("Confirmar Limpeza", type="primary"):
            limpar_campos()

    portas_str = ", ".join(st.session_state.portas) if st.session_state.portas else "Nenhuma"
    st.info(f"**Portas Liberadas:** {portas_str}")

    col_tabela, col_lateral = st.columns([3, 1.3], gap="large")

    with col_tabela:
        pesos = [0.2, 1, 1, 1, 0.3]
        h = st.columns(pesos)
        h[0].write("**#**"); h[1].write("**ETIQUETA**"); h[2].write("**SERIAL**"); h[3].write("**ID**"); h[4].write("**Livre**")
        for i in range(16):
            r = st.columns(pesos)
            r[0].write(f"**{i+1:02d}**")
            for idx, pref in enumerate(['e_b_', 's_b_', 'id_b_']):
                k = f"{pref}{i}"
                r[idx+1].text_input(f"in_{k}", value=st.session_state[k], key=f"temp_{k}_{v}", on_change=salvar_campo, args=(k,), label_visibility="collapsed")
            r[4].checkbox(f"l{i}", value=st.session_state[f"c_batida_{i}"], key=f"temp_c_batida_{i}_{v}", on_change=salvar_checkbox, args=(i,), label_visibility="collapsed")

    with col_lateral:
        st.write("**ANOTAÇÕES**")
        st.text_area("Notas", value=st.session_state.anot_batida, height=100, key=f"temp_anot_batida_{v}", on_change=salvar_campo, args=("anot_batida",), label_visibility="collapsed")
        
        res = f"Protocolo: {st.session_state.batida_proto}\nTécnico: {st.session_state.batida_tec}\nCaixa: {st.session_state.batida_cx}\nPortas: {portas_str}\nNotas: {st.session_state.anot_batida}\n{'-'*20}\n"
        for i in range(16):
            et, se, idx = st.session_state[f"e_b_{i}"], st.session_state[f"s_b_{i}"], st.session_state[f"id_b_{i}"]
            if et or se or idx: res += f"{i+1:02d} - {et} | {se} | {idx}\n"
        
        st.text_area("Relatório Final", res, height=250, label_visibility="collapsed")
        
        # Botão Copiar JS
        js_copy = json.dumps(res)
        components.html(f"""
            <button id="cp" style="width:100%; height:40px; background:#4da3ff; color:white; border:none; border-radius:6px; cursor:pointer; font-weight:bold;">📋 COPIAR RELATÓRIO</button>
            <script>
            document.getElementById('cp').onclick = function() {{
                const t = document.createElement("textarea"); t.value = {js_copy}; document.body.appendChild(t);
                t.select(); document.execCommand('copy'); document.body.removeChild(t);
                this.style.background = '#28a745'; this.innerText = '✅ COPIADO!';
                setTimeout(() => {{ this.style.background = '#4da3ff'; this.innerText = '📋 COPIAR RELATÓRIO'; }}, 2000);
            }}
            </script>
        """, height=50)

        if st.button("💾 REGISTRAR NA PLANILHA", use_container_width=True, type="primary"):
            if not st.session_state.batida_proto or not st.session_state.batida_cx:
                st.error("Preencha Protocolo e Caixa!")
            else:
                aba = conectar_google_sheets()
                if aba:
                    fuso_br = pytz.timezone('America/Sao_Paulo')
                    data_hora = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M")
                    linha = [str(data_hora), str(st.session_state.batida_proto), str(st.session_state.batida_cx), str(portas_str)]
                    aba.append_row(linha)
                    st.toast("Registrado com sucesso!", icon="✅")
                    st.balloons()
