import streamlit as st
import streamlit.components.v1 as components
import json
import os
import re
from styles import apply_styles

# --- CONFIGURAÇÃO DE MODELOS ---
MAPA_TEMPLATES = {
    "RB 4011": "rb_4011",
    "RB 750/760": "rb_750_760",
    "RB HAP": "rb_hap",
    "RB HAP AC": "rb_hap_ac",
}

def render():
    apply_styles()
    
    # Inicializa contador de reset exclusivo para este módulo
    if 'reset_rb' not in st.session_state:
        st.session_state.reset_rb = 0

    def limpar_campos():
        st.session_state.reset_rb += 1
        # Limpa apenas as chaves que começam com 'rb_'
        keys_to_del = [k for k in st.session_state.keys() if k.startswith("rb_")]
        for k in keys_to_del:
            del st.session_state[k]
        st.rerun()

    st.title("📝 Gerador de Configuração MikroTik")

    # --- SELEÇÃO DE MODELO ---
    nome_modelo = st.selectbox(
        "📂 Selecione o Modelo de Roteador", 
        list(MAPA_TEMPLATES.keys()), 
        key=f"rb_modelo_sel_{st.session_state.reset_rb}"
    )

    st.divider()

    # --- INPUTS DO USUÁRIO ---
    col_dados, col_portas = st.columns([2, 1])

    with col_dados:
        st.subheader("👤 Dados do Cliente")
        cod_nome = st.text_input("Cód + Nome", key=f"rb_cod_nome_{st.session_state.reset_rb}", placeholder="Ex: 12345 - Nome do Cliente")
        
        c1, c2 = st.columns(2)
        with c1:
            pppoe_user = st.text_input("PPPoE do Cliente", key=f"rb_pppoe_user_{st.session_state.reset_rb}").replace(" ", "")
        with c2:
            pppoe_pass = st.text_input("Senha do PPPoE", key=f"rb_pppoe_pass_{st.session_state.reset_rb}").replace(" ", "")
        
        wifi_name, wifi_5ghz_name, wifi_pass = "", "", ""

        if "HAP" in nome_modelo:
            st.subheader("📶 Configurações Wi-Fi")
            wf1, wf2 = st.columns(2)
            with wf1:
                wifi_name = st.text_input("Nome do Wi-Fi (SSID)", key=f"rb_wifi_name_{st.session_state.reset_rb}")
                if "AC" in nome_modelo:
                    wifi_5ghz_name = st.text_input("Nome do Wi-Fi 5GHz", key=f"rb_wifi_5ghz_{st.session_state.reset_rb}")
            with wf2:
                wifi_pass = st.text_input("Senha do Wi-Fi", key=f"rb_wifi_pass_{st.session_state.reset_rb}")

        is_hotspot = False
        if "RB 4011" in nome_modelo:
            st.write("")
            is_hotspot = st.checkbox("🔥 MODO HOTSPOT (EAPs)", key=f"rb_check_hotspot_{st.session_state.reset_rb}")

    # --- COLUNA DAS PORTAS ---
    portas_selecionadas = []
    with col_portas:
        st.subheader("🔌 Portas LAN")
        if "RB 4011" in nome_modelo and is_hotspot:
            st.info("Selecione as portas LAN (Exceto Porta 2)")
            cp1, cp2 = st.columns(2)
            
            if cp1.checkbox("LAN 1", key=f"rb_lan_1_{st.session_state.reset_rb}"):
                portas_selecionadas.append(1)
            
            for i in range(3, 11):
                target_col = cp1 if i <= 6 else cp2
                if target_col.checkbox(f"LAN {i}", key=f"rb_lan_{i}_{st.session_state.reset_rb}"):
                    portas_selecionadas.append(i)
            portas_selecionadas.sort()
        else:
            st.write("Configuração de portas padrão.")
            if "RB 4011" in nome_modelo:
                st.info("📌 Modo Padrão: Bridge única.")

    st.divider()

    # --- LÓGICA DE GERAÇÃO DINÂMICA ---
    l_ether = 'set [ find default-name=ether2 ] comment=UPLINK'
    v1750_bloco, v1751_bloco, l_bridge, l_bridge_dinamica = "", "", "", ""

    if is_hotspot:
        for p in portas_selecionadas:
            l_ether += f'\nset [ find default-name=ether{p} ] comment="EAP"'
            v1750_bloco += f"add interface=ether{p} name=Vlan1750_ether{p} vlan-id=1750\n"
            v1751_bloco += f"add interface=ether{p} name=Vlan1751_ether{p} vlan-id=1751\n"
            l_bridge += f"add bridge=Bridge_LAN interface=ether{p}\n"
            l_bridge_dinamica += f"add bridge=Bridge_EasyAuth interface=Vlan1751_ether{p}\n"

    # --- CARREGAMENTO DO TEMPLATE ---
    sufixo = "_hotspot.rsc" if is_hotspot else ".rsc"
    arquivo_rsc = MAPA_TEMPLATES[nome_modelo] + sufixo

    try:
        # Busca o caminho dinâmico para a pasta templates na raiz
        base_path = os.path.dirname(os.path.abspath(__file__))
        caminho_final = os.path.normpath(os.path.join(base_path, "..", "templates", arquivo_rsc))

        if not os.path.exists(caminho_final):
            st.error(f"❌ Arquivo '{arquivo_rsc}' não encontrado!")
            st.code(f"Local buscado: {caminho_final}", language="text")
        else:
            with open(caminho_final, "r", encoding="utf-8") as f:
                template_raw = f.read()

            # Substituições no template
            final_script = template_raw.replace("XXXCOD_NOMEXXX", cod_nome)\
                .replace("XXXUSUARIOPPPOEXXX", pppoe_user)\
                .replace("XXXSENHAPPPOEXXX", pppoe_pass)\
                .replace("XXXWIFI_NAMEXXX", wifi_name)\
                .replace("XXXWIFI_5GHZ_NAMEXXX", wifi_5ghz_name)\
                .replace("XXXWIFI_PASSXXX", wifi_pass)\
                .replace("XXXLINHAS_ETHERNETXXX", l_ether)\
                .replace("XXXVLAN_1750_DINAMICAXXX", v1750_bloco.strip())\
                .replace("XXXVLAN_1751_DINAMICAXXX", v1751_bloco.strip())\
                .replace("XXXLINHAS_BRIDGEXXX", l_bridge.strip())\
                .replace("XXXLINHAS_BRIDGE_DINAMICAXXX", l_bridge_dinamica.strip())

            st.subheader("📄 Preview do Script")
            st.code(final_script, language="bash")

            # Componente de Cópia
            template_json = json.dumps(final_script)
            copy_html = f"""
                <button id="cpBtn" style="background-color: #238636; color: white; border: none; padding: 15px; border-radius: 8px; width: 100%; cursor: pointer; font-weight: bold; font-size: 16px; margin-top: 10px;">
                    📋 Copiar Script Completo
                </button>
                <script>
                document.getElementById("cpBtn").addEventListener("click", function() {{
                    const txt = {template_json};
                    const el = document.createElement("textarea");
                    el.value = txt; document.body.appendChild(el); el.select();
                    document.execCommand('copy'); document.body.removeChild(el);
                    this.innerText = "Copiado! ✅"; this.style.backgroundColor = "#28a745";
                    setTimeout(() => {{ this.innerText = "📋 Copiar Script Completo"; this.style.backgroundColor = "#238636"; }}, 2500);
                }});
                </script>
            """
            components.html(copy_html, height=80)

    except Exception as e:
        st.error(f"Erro ao processar template: {e}")

    # Botão de Reset
    st.write("")
    if st.button("🗑️ Limpar Todos os Campos", use_container_width=True):
        limpar_campos()
