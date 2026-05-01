import streamlit as st
import streamlit.components.v1 as components
import json

def render():
    st.title("📲 Gerador de Máscara Multi-Chip (Demo)")
    st.info("💡 **Aviso de Portfólio:** Este módulo roda puramente no cliente e não requer banco de dados. Funcionalidade mantida em 100%.")

    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1:
        qtd_chips = st.selectbox("Quantidade de números:", list(range(1, 11)))
    with col_cfg2:
        tipo_chip_label = st.radio("Tipo de Chip (Geral):", ["SimCard", "ESim"], horizontal=True)

    sim_card_val = 1 if tipo_chip_label == "SimCard" else 0
    st.divider()

    # Loop para Gerar Inputs
    for i in range(1, qtd_chips + 1):
        with st.expander(f"📍 Configuração do Chip {i}", expanded=True):
            suffix = f"_{i}"
            label_suffix = f" {i}" if i > 1 else ""

            port_terceiro = st.checkbox(f"Portabilidade de Terceiro (Chip{label_suffix})", key=f"check{suffix}")
            
            if port_terceiro:
                st.text_input(f"Nome do Titular Original", key=f"nome{suffix}")

            c1, c2 = st.columns(2)
            with c1:
                st.text_input(f"Nº Telefone Provisório{label_suffix}", key=f"prov{suffix}")
                st.text_input(f"Iccid{label_suffix}", key=f"iccid{suffix}")
            with c2:
                st.text_input(f"Número Portado{label_suffix}", key=f"port{suffix}")
                st.text_input(f"Data Prevista{label_suffix}", key=f"data{suffix}")

    st.divider()
    status_geral = st.text_input("Status Geral (para todos)", value="PENDENTE")

    # Lógica de Construção da Máscara
    chip_line = f"CHIP: ESim ({'X' if sim_card_val == 0 else ' '}) Sim Card ({'X' if sim_card_val == 1 else ' '})"
    bloco_terceiros = "PORTABILIDADE EM NOME DE 3º:\n\n"
    bloco_telefones = ""
    bloco_dados_port = "Dados da Portabilidade:\n"

    for i in range(1, qtd_chips + 1):
        s = f"_{i}"
        ls = f" {i}" if i > 1 else ""
        
        is_terceiro = st.session_state.get(f"check{s}", False)
        nome = st.session_state.get(f"nome{s}", "")
        
        if is_terceiro:
            bloco_terceiros += f"CHIP{ls}: SIM (X) - Nome: {nome}\n"
        else:
            bloco_terceiros += f"CHIP{ls}: NÃO (X)\n"

        p = st.session_state.get(f"prov{s}", "")
        ic = st.session_state.get(f"iccid{s}", "")
        bloco_telefones += f"Nº Telefone Provisório{ls}: {p}\nIccid{ls}: {ic}\n\n"

        dt = st.session_state.get(f"data{s}", "")
        num = st.session_state.get(f"port{s}", "")
        bloco_dados_port += f"Data Prevista{ls}: {dt}\nNúmero Portado{ls}: {num}\nStatus{ls}: {status_geral}\n\n"

    mascara_final = f"""{chip_line}\n\n{bloco_terceiros}\n{bloco_telefones}\n{bloco_dados_port}
Cliente ciente do prazo de 24hs para a confirmação via sms?\nSIM (X)\nNÃO ( )\n\nCiente da Data Prevista?\nSIM (X)\nNÃO ( )"""

    # Exibição
    st.subheader("📄 Máscara Gerada")
    st.code(mascara_final, language="text")

    # Botão de Cópia com correção de escape usando JSON
    safe_text = json.dumps(mascara_final)

    html_button = f"""
        <div style="text-align: center; font-family: sans-serif;">
            <button id="copyBtn" style="
                background-color: #4da3ff; color: white; border: none;
                padding: 15px 30px; border-radius: 8px; cursor: pointer;
                font-weight: bold; width: 100%;
            ">📋 COPIAR MÁSCARA COMPLETA</button>
        </div>
        <script>
        document.getElementById('copyBtn').onclick = function() {{
            const text = {safe_text};
            const textArea = document.createElement("textarea");
            textArea.value = text;
            textArea.style.position = "fixed";  // Evitar scroll
            textArea.style.left = "-9999px";
            textArea.style.top = "0";
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            try {{
                document.execCommand('copy');
                const btn = document.getElementById('copyBtn');
                btn.style.backgroundColor = '#28a745';
                btn.innerText = '✅ COPIADO COM SUCESSO!';
                setTimeout(() => {{ 
                    btn.style.backgroundColor = '#4da3ff'; 
                    btn.innerText = '📋 COPIAR MÁSCARA COMPLETA'; 
                }}, 2000);
            }} catch (err) {{
                console.error("Erro ao copiar", err);
            }}
            document.body.removeChild(textArea);
        }};
        </script>
    """
    components.html(html_button, height=80)
