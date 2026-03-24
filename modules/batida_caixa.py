import streamlit as st
import streamlit.components.v1 as components
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from datetime import datetime
import pytz
import traceback

# --- FUNÇÃO DE CONEXÃO REVISADA E BLINDADA ---
def conectar_google_sheets():
    try:
        # 1. Busca os Secrets (Tenta a chave 1 ou a chave 2 caso você tenha renomeado)
        raw_creds = st.secrets.get("GOOGLE_JSON_CREDENTIALS") or st.secrets.get("GOOGLE_JSON_CREDENTIALS_2")
        spreadsheet_url = st.secrets.get("URL_PLANILHA")
        
        if not raw_creds:
            st.error("❌ Erro: Credenciais do Google não encontradas nos Secrets.")
            return None
        if not spreadsheet_url:
            st.error("❌ Erro: URL da planilha não configurada.")
            return None

        # 2. Carrega e limpa a chave privada (Crucial para evitar Invalid JWT Signature)
        creds_info = json.loads(raw_creds)
        st.write(f"DEBUG: O e-mail que está tentando acessar é: {creds_info.get('client_email')}")
        if "private_key" in creds_info:
            creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        
        # 3. Autenticação
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)
        
        # 4. Abre a planilha (.strip() remove espaços invisíveis que quebram a conexão)
        planilha = client.open_by_url(spreadsheet_url.strip())
        return planilha.get_worksheet(0)
        
    except Exception as e:
        st.error(f"❌ Erro na conexão: {str(e)}")
        with st.expander("Ver Detalhes do Erro"):
            st.code(traceback.format_exc())
        return None

def render():
    # --- INICIALIZAÇÃO DE ESTADOS (LOGO NO INÍCIO) ---
    if 'batida_version' not in st.session_state:
        st.session_state.batida_version = 0
    if 'portas' not in st.session_state:
        st.session_state.portas = []
        
    v = st.session_state.batida_version

    campos_init = ['batida_proto', 'batida_tec', 'batida_cx', 'anot_batida']
    for c in campos_init:
        if c not in st.session_state: st.session_state[c] = ""
    
    for i in range(16):
        for pref in ['e_b_', 's_b_', 'id_b_']:
            if f"{pref}{i}" not in st.session_state: st.session_state[f"{pref}{i}"] = ""
        if f"c_batida_{i}" not in st.session_state: st.session_state[f"c_batida_{i}"] = False

    # --- FUNÇÕES INTERNAS ---
    def salvar_campo(chave_permanente):
        key_temp = f"temp_{chave_permanente}_{v}"
        if key_temp in st.session_state:
            st.session_state[chave_permanente] = st.session_state[key_temp]

    def atualizar_portas():
        st.session_state.portas = [f"{i+1:02d}" for i in range(16) if st.session_state.get(f"temp_c_batida_{i}_{v}")]

    def salvar_checkbox(indice):
        key_temp = f"temp_c_batida_{indice}_{v}"
        if key_temp in st.session_state:
            st.session_state[f"c_batida_{indice}"] = st.session_state[key_temp]
            atualizar_portas()

    def limpar_campos():
        for c in campos_init: st.session_state[c] = ""
        for i in range(16):
            for pref in ['e_b_', 's_b_', 'id_b_']: st.session_state[f"{pref}{i}"] = ""
            st.session_state[f"c_batida_{i}"] = False
        st.session_state.portas = []
        st.session_state.batida_version += 1
        st.rerun()

    st.title("📦 BATIDA DE CAIXA 3000")

    # --- CABEÇALHO ---
    c1, c2, c3, c_btn = st.columns([2, 2, 1, 0.5])
    with c1: st.text_input("PROTOCOLO", value=st.session_state.batida_proto, key=f"temp_batida_proto_{v}", on_change=salvar_campo, args=("batida_proto",))
    with c2: st.text_input("TÉCNICO", value=st.session_state.batida_tec, key=f"temp_batida_tec_{v}", on_change=salvar_campo, args=("batida_tec",))
    with c3: st.text_input("CAIXA", value=st.session_state.batida_cx, key=f"temp_batida_cx_{v}", on_change=salvar_campo, args=("batida_cx",))
    with c_btn:
        st.write(" ")
        if st.popover("🗑️").button("Confirmar Limpeza", type="primary", use_container_width=True):
            limpar_campos()

    portas_str = ", ".join(st.session_state.portas) if st.session_state.portas else "Nenhuma"
    st.info(f"**Portas Liberadas:** {portas_str}")

    col_tabela, col_lateral = st.columns([3, 1.4], gap="large")

    with col_tabela:
        pesos = [0.3, 1, 1, 1, 0.4]
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
        st.text_area("Notas", value=st.session_state.anot_batida, height=80, key=f"temp_anot_batida_{v}", on_change=salvar_campo, args=("anot_batida",), label_visibility="collapsed")
        
        # Relatório dinâmico
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
        
        st.text_area("Relatório Final", res, height=300, label_visibility="collapsed")
        
        js_copy = json.dumps(res)
        components.html(f"""
            <button id="cp" style="width:100%; height:40px; background:#4da3ff; color:white; border:none; border-radius:6px; cursor:pointer; font-weight:bold; font-family:sans-serif;">📋 COPIAR RELATÓRIO</button>
            <script>
            document.getElementById('cp').onclick = function() {{
                const t = document.createElement("textarea"); t.value = {js_copy}; document.body.appendChild(t);
                t.select(); document.execCommand('copy'); document.body.removeChild(t);
                const btn = document.getElementById('cp'); btn.style.background = '#28a745'; btn.innerText = '✅ COPIADO!';
                setTimeout(() => {{ btn.style.background = '#4da3ff'; btn.innerText = '📋 COPIAR RELATÓRIO'; }}, 2000);
            }}
            </script>
        """, height=50)

        if st.button("💾 REGISTRAR NA PLANILHA", use_container_width=True, type="primary"):
            if not st.session_state.batida_proto or not st.session_state.batida_cx:
                st.error("Protocolo e Caixa são obrigatórios!")
            else:
                with st.spinner("Conectando ao Google..."):
                    aba = conectar_google_sheets()
                    if aba:
                        try:
                            fuso_br = pytz.timezone('America/Sao_Paulo')
                            data_hora = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M")
                            
                            # Preparamos os dados
                            linha = [
                                str(data_hora), 
                                str(st.session_state.batida_proto), # Adicionei o técnico que faltava na sua lista anterior
                                str(st.session_state.batida_cx), 
                                str(portas_str)
                            ]
                            
                            # --- SOLUÇÃO PARA ADICIONAR SEMPRE NO FINAL ---
                            # O table_range garante que ele procure a próxima linha livre a partir da coluna A
                            aba.append_row(
                                linha, 
                                value_input_option='USER_ENTERED',
                                insert_data_option='INSERT_ROWS',
                                table_range='A1'
                            )
                            
                            st.toast("Registrado com sucesso!", icon="✅")
                            st.balloons()
                            
                            # Opcional: Limpar campos após sucesso para evitar registros duplicados acidentais
                            # limpar_campos() 
                            
                        except Exception as e:
                            st.error(f"Erro ao inserir linha: {e}")
