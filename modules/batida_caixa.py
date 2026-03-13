import streamlit as st
import streamlit.components.v1 as components
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from datetime import datetime
import pytz # Certifique-se de que 'pytz' esteja no seu requirements.txt


def render():
    # Puxa a versão atual do cache para garantir que os widgets resetem visualmente
    v = st.session_state.batida_version

    # --- 1. FUNÇÕES DE SUPORTE ---
    def salvar_campo(chave_permanente):
        """ Sincroniza o widget temp (com versão) com a memória permanente """
        key_temp = f"temp_{chave_permanente}_{v}"
        if key_temp in st.session_state:
            st.session_state[chave_permanente] = st.session_state[key_temp]

    def atualizar_portas():
        """ Atualiza a lista de strings das portas selecionadas """
        st.session_state.portas = [f"{i+1:02d}" for i in range(16) if st.session_state.get(f"c_batida_{i}")]

    def salvar_checkbox(indice):
        """ Sincroniza o checkbox temp e atualiza a lista de portas """
        key_temp = f"temp_c_batida_{indice}_{v}"
        if key_temp in st.session_state:
            st.session_state[f"c_batida_{indice}"] = st.session_state[key_temp]
            atualizar_portas()

    def conectar_google_sheets():
        """ Conecta ao Google Sheets e retorna a aba configurada """
        try:
            # Lê as credenciais JSON direto dos Secrets
            creds_info = json.loads(st.secrets["GOOGLE_JSON_CREDENTIALS"])
            
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
            client = gspread.authorize(creds)
            
            # Abre a planilha pela URL nos Secrets e seleciona a primeira aba
            planilha = client.open_by_url(st.secrets["SPREADSHEET_URL"])
            return planilha.get_worksheet(0)
        except Exception as e:
            st.error(f"Erro na conexão com Google Sheets: {e}")
            return None

    def limpar_campos():
        """ Reseta todos os campos, incrementa versão e recarrega o app """
        campos_texto = ['batida_proto', 'batida_tec', 'batida_cx', 'anot_batida']
        for c in campos_texto:
            st.session_state[c] = ""
        
        for i in range(16):
            for pref in ['e_b_', 's_b_', 'id_b_']:
                st.session_state[f"{pref}{i}"] = ""
            st.session_state[f"c_batida_{i}"] = False
        
        st.session_state.portas = []
        st.session_state.batida_version += 1
        
        for key in list(st.session_state.keys()):
            if key.startswith('temp_'):
                del st.session_state[key]
        st.rerun()

    st.title("📦 BATIDA DE CAIXA 3000")

    # --- 2. CABEÇALHO ---
    c1, c2, c3, c_btn = st.columns([2, 2, 1, 0.5])
    with c1: 
        st.text_input("PROTOCOLO", value=st.session_state.batida_proto, 
                      key=f"temp_batida_proto_{v}", on_change=salvar_campo, args=("batida_proto",))
    with c2: 
        st.text_input("TÉCNICO", value=st.session_state.batida_tec, 
                      key=f"temp_batida_tec_{v}", on_change=salvar_campo, args=("batida_tec",))
    with c3: 
        st.text_input("CAIXA", value=st.session_state.batida_cx, 
                      key=f"temp_batida_cx_{v}", on_change=salvar_campo, args=("batida_cx",))
    with c_btn: 
        st.write(" ") 
        confirmar = st.popover("🗑️", help="Limpar tudo")
        if confirmar.button("Sim, apagar tudo!", type="primary", use_container_width=True):
            limpar_campos()

    portas_str = ", ".join(st.session_state.portas) if st.session_state.portas else "Nenhuma"
    st.info(f"**Portas Liberadas:** {portas_str}")

    col_tabela, col_lateral = st.columns([3, 1.3], gap="large")

    # --- 3. TABELA DE ENTRADA ---
    with col_tabela:
        pesos = [0.2, 1, 1, 1, 0.3]
        h = st.columns(pesos)
        h[0].write("**#**"); h[1].write("**ETIQUETA**"); h[2].write("**SERIAL**"); h[3].write("**ID**"); h[4].write("**Livre**")

        for i in range(16):
            r = st.columns(pesos)
            r[0].markdown(f"**{i+1:02d}**")
            for idx, pref in enumerate(['e_b_', 's_b_', 'id_b_'], start=1):
                k_orig = f"{pref}{i}"
                r[idx].text_input(f"in_{k_orig}", value=st.session_state[k_orig], 
                                  key=f"temp_{k_orig}_{v}", on_change=salvar_campo, 
                                  args=(k_orig,), label_visibility="collapsed")
            r[4].checkbox(f"l{i}", value=st.session_state[f"c_batida_{i}"], 
                          key=f"temp_c_batida_{i}_{v}", on_change=salvar_checkbox, 
                          args=(i,), label_visibility="collapsed")

    # --- 4. COLUNA LATERAL ---
    with col_lateral:
        st.write("**ANOTAÇÕES**")
        st.text_area("Notas", value=st.session_state.anot_batida, height=100, 
                     key=f"temp_anot_batida_{v}", on_change=salvar_campo, args=("anot_batida",), label_visibility="collapsed")
        
        res = (f"Protocolo: {st.session_state.batida_proto}\n"
               f"Técnico: {st.session_state.batida_tec}\n"
               f"Caixa: {st.session_state.batida_cx}\n"
               f"Portas: {portas_str}\n"
               f"Notas: {st.session_state.anot_batida}\n"
               f"{'-'*20}\n")
        
        for i in range(16):
            et, se, idx = st.session_state[f"e_b_{i}"], st.session_state[f"s_b_{i}"], st.session_state[f"id_b_{i}"]
            if et or se or idx:
                res += f"{i+1:02d} - {et} | {se} | {idx}\n"
        
        st.text_area("Relatório Final", res, height=250, label_visibility="collapsed")
        
        js_copy = json.dumps(res)
        components.html(f"""
            <button id="cp" style="width:100%; height:40px; background:#4da3ff; color:white; border:none; border-radius:6px; cursor:pointer; font-weight:bold; font-family:sans-serif;">📋 COPIAR RELATÓRIO</button>
            <script>
            document.getElementById('cp').onclick = function() {{
                const t = document.createElement("textarea"); t.value = {js_copy}; document.body.appendChild(t);
                t.select(); document.execCommand('copy'); document.body.removeChild(t);
                alert("Copiado!");
            }}
            </script>
        """, height=50)

        # Registro no Google Sheets
        if st.button("💾 REGISTRAR NA PLANILHA", use_container_width=True, type="primary"):
            if not st.session_state.batida_proto or not st.session_state.batida_cx:
                st.error("Protocolo e Caixa são obrigatórios!")
            else:
                try:
                    with st.spinner('Enviando para o Google Sheets...'):
                        aba = conectar_google_sheets()
                        if aba:
                            # CORREÇÃO DE HORÁRIO (AMERICA/SAO_PAULO)
                            fuso_br = pytz.timezone('America/Sao_Paulo')
                            data_hora = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M")
                            
                            linha = [
                                str(data_hora), 
                                str(st.session_state.batida_proto), 
                                str(st.session_state.batida_cx), 
                                str(portas_str), 
                            ]
                            
                            # append_row com insert_data_option garante que crie uma NOVA linha
                            aba.append_row(
                                linha, 
                                value_input_option='USER_ENTERED',
                                insert_data_option='INSERT_ROWS'
                            )
                            
                            st.toast(f"Registrado com sucesso às {data_hora}!", icon="✅")
                            st.balloons()
                except Exception as e:
                    st.error(f"Erro ao salvar na planilha: {e}")
