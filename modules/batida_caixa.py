import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from datetime import datetime
import pytz

def render():
    # Puxa a versão para resetar widgets quando necessário
    v = st.session_state.batida_version

    # --- FUNÇÕES DE SUPORTE ---
    def salvar_campo(chave_permanente):
        key_temp = f"temp_{chave_permanente}_{v}"
        if key_temp in st.session_state:
            st.session_state[chave_permanente] = st.session_state[key_temp]

    def atualizar_portas(indice):
        # Salva o estado do checkbox primeiro
        key_temp = f"temp_c_batida_{indice}_{v}"
        if key_temp in st.session_state:
            st.session_state[f"c_batida_{indice}"] = st.session_state[key_temp]
        
        # Atualiza a lista de portas selecionadas
        st.session_state.portas = [f"{i+1:02d}" for i in range(16) if st.session_state.get(f"c_batida_{i}")]

    def conectar_google_sheets():
        try:
            creds_info = json.loads(st.secrets["GOOGLE_JSON_CREDENTIALS"])
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
            client = gspread.authorize(creds)
            planilha = client.open_by_url(st.secrets["SPREADSHEET_URL"])
            return planilha.get_worksheet(0)
        except Exception as e:
            st.error(f"Erro Google Sheets: {e}")
            return None

    def limpar_campos():
        # Reset total das chaves permanentes
        st.session_state.batida_proto = ""
        st.session_state.batida_tec = ""
        st.session_state.batida_cx = ""
        st.session_state.anot_batida = ""
        for i in range(16):
            st.session_state[f"e_b_{i}"] = ""
            st.session_state[f"s_b_{i}"] = ""
            st.session_state[f"id_b_{i}"] = ""
            st.session_state[f"c_batida_{i}"] = False
        st.session_state.portas = []
        st.session_state.batida_version += 1
        st.rerun()

    st.title("💰 BATIDA DE CAIXA")

    # --- CABEÇALHO ---
    c1, c2, c3, c_btn = st.columns([2, 2, 1, 0.5])
    with c1: 
        proto = st.text_input("PROTOCOLO", value=st.session_state.batida_proto, 
                              key=f"temp_batida_proto_{v}", on_change=salvar_campo, args=("batida_proto",))
    with c2: 
        tec = st.text_input("TÉCNICO", value=st.session_state.batida_tec, 
                            key=f"temp_batida_tec_{v}", on_change=salvar_campo, args=("batida_tec",))
    with c3: 
        cx = st.text_input("CAIXA", value=st.session_state.batida_cx, 
                           key=f"temp_batida_cx_{v}", on_change=salvar_campo, args=("batida_cx",))
    with c_btn: 
        st.write(" ") 
        if st.button("🗑️", help="Limpar tudo"): limpar_campos()

    # --- LISTAGEM DE PORTAS ---
    portas_str = ", ".join(st.session_state.portas) if st.session_state.portas else "Nenhuma"
    st.info(f"**Portas Liberadas:** {portas_str}")

    col_tabela, col_lateral = st.columns([3, 1.3])

    # --- TABELA DE ENTRADA ---
    with col_tabela:
        pesos = [0.2, 1, 1, 1, 0.3]
        h = st.columns(pesos)
        h[0].write("**#**"); h[1].write("**ETIQUETA**"); h[2].write("**SERIAL**"); h[3].write("**ID**"); h[4].write("**L**")

        for i in range(16):
            r = st.columns(pesos)
            r[0].write(f"{i+1:02d}")
            # Colunas de texto (Etiqueta, Serial, ID)
            for pref in ['e_b_', 's_b_', 'id_b_']:
                chave = f"{pref}{i}"
                r[['e_b_', 's_b_', 'id_b_'].index(pref) + 1].text_input(
                    f"in_{chave}", value=st.session_state[chave], 
                    key=f"temp_{chave}_{v}", on_change=salvar_campo, 
                    args=(chave,), label_visibility="collapsed"
                )
            # Coluna Checkbox (Liberação)
            r[4].checkbox(
                f"cb_{i}", value=st.session_state[f"c_batida_{i}"], 
                key=f"temp_c_batida_{i}_{v}", on_change=atualizar_portas, 
                args=(i,), label_visibility="collapsed"
            )

    # --- RELATÓRIO E ENVIO ---
    with col_lateral:
        st.write("**ANOTAÇÕES**")
        notas = st.text_area("Notas", value=st.session_state.anot_batida, height=80, 
                             key=f"temp_anot_batida_{v}", on_change=salvar_campo, args=("anot_batida",), label_visibility="collapsed")
        
        # MONTAGEM DO TEXTO (Usa as variáveis locais proto, cx, portas_str para atualizar NA HORA)
        texto_relatorio = (
            f"✅ *BATIDA DE CAIXA REALIZADA*\n"
            f"🔢 Protocolo: {proto}\n"
            f"👷 Técnico: {tec}\n"
            f"📦 Caixa: {cx}\n"
            f"🔌 Portas: {portas_str}\n"
            f"📝 Notas: {notas}\n"
        )
        
        st.text_area("📋 Relatório Final (Copiar)", value=texto_relatorio, height=200)

        if st.button("💾 REGISTRAR PLANILHA", use_container_width=True, type="primary"):
            if not proto or not cx:
                st.error("Preencha Protocolo e Caixa!")
            else:
                aba = conectar_google_sheets()
                if aba:
                    fuso = pytz.timezone('America/Sao_Paulo')
                    agora = datetime.now(fuso).strftime("%d/%m/%Y %H:%M")
                    aba.append_row([agora, proto, tec, cx, portas_str, notas])
                    st.success("Dados salvos no Google Sheets!")
