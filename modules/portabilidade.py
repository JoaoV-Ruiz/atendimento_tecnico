import streamlit as st
import streamlit.components.v1 as components
import json
import re
from geopy.geocoders import Nominatim

# Configuração da página
st.set_page_config(page_title="Gerador de Relatório Técnico", page_icon="📶", layout="centered")

# --- FUNÇÕES DE SUPORTE ---

def buscar_cidade(coords_texto):
    if not coords_texto: return ""
    try:
        # Extrai números decimais da string de coordenadas
        nums = re.findall(r"[-+]?\d*\.\d+|\d+", coords_texto)
        if len(nums) >= 2:
            geolocator = Nominatim(user_agent="gerador_tecnico_osir_v2")
            location = geolocator.reverse(f"{nums[0]}, {nums[1]}", timeout=10)
            if location:
                address = location.raw.get('address', {})
                # Retorna cidade, vila ou município
                return address.get('city') or address.get('town') or address.get('village') or "Cidade não encontrada"
    except: 
        return "Erro na busca"
    return ""

def reset_form():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

# --- INTERFACE ---
st.title("📶 Registro de Campo")
st.info("Preencha os dados abaixo para gerar a máscara de fechamento.")

# Layout Superior
col_a, col_b = st.columns(2)
with col_a:
    nome_cliente = st.text_input("Nome do Cliente", placeholder="Ex: João Silva", key="nome_text")
with col_b:
    tipo_proto = st.radio("Tipo de Protocolo:", ["Ativação", "Manutenção"], key="tipo_proto_key", horizontal=True)

st.divider()

col1, col2 = st.columns(2)
with col1:
    protocolo = st.text_input("Protocolo da Solicitação", key="prot_text")
    tipo_caixa = st.radio("Tipo da Caixa:", ["1x16", "1x8"], key="tipo_caixa_key", horizontal=True)
    problema = st.radio("Problema Identificado:", ["CTO/porta sem sinal", "CTO cheia", "CTO/porta com sinal fora do padrão"], key="problema_key")

with col2:
    num_cto = st.text_input("Número da CTO", key="cto_text")
    sinal_cto = st.text_input("Sinal da CTO (Power Meter)", key="sinal_text")
    coords = st.text_input("Coordenadas (Lat, Long)", key="coords_text", help="Cole aqui as coordenadas do Google Maps")
    sem_id = st.radio("Caixa sem identificação?", ["Sim", "Não"], index=1, key="sem_id_key", horizontal=True)

# --- LÓGICA DAS PORTAS (Dinâmica) ---
portas_selecionadas = []
if problema == "CTO/porta sem sinal":
    st.markdown("---")
    st.write("🔧 **Selecione as portas afetadas:**")
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    
    with col_p1:
        check_todos = st.checkbox("TODAS", key="p_todos")
    
    if check_todos:
        portas_selecionadas = ["TODAS"]
    else:
        for i in range(1, 17):
            col_target = [col_p1, col_p2, col_p3, col_p4][(i) % 4]
            with col_target:
                if st.checkbox(f"Porta {i}", key=f"p_{i}"):
                    portas_selecionadas.append(str(i))

# Busca automática da cidade baseada nas coordenadas
cidade_detectada = buscar_cidade(coords)

# --- MÁSCARA DE TEXTO ---
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

st.divider()

# Botões de Rodapé
c_limpar, c_vazio = st.columns([1, 2])
with c_limpar:
    st.button("🗑️ Limpar Tudo", on_click=reset_form, use_container_width=True)

st.subheader("📄 Relatório Gerado")
st.code(mascara, language="text")

# Botão Copiar via JavaScript (Melhor experiência de usuário)
js_copy = json.dumps(mascara)
components.html(f"""
    <button id="cp" style="width:100%; height:50px; background:#007bff; color:white; border:none; border-radius:8px; cursor:pointer; font-weight:bold; font-size:16px; font-family:sans-serif; transition: 0.3s;">📋 COPIAR PARA O WHATSAPP / CRM</button>
    <script>
    document.getElementById('cp').onclick = function() {{
        const t = document.createElement("textarea"); 
        t.value = {js_copy}; 
        document.body.appendChild(t);
        t.select(); 
        document.execCommand('copy'); 
        document.body.removeChild(t);
        this.style.background = '#28a745'; 
        this.innerText = '✅ COPIADO COM SUCESSO!';
        setTimeout(() => {{ 
            this.style.background = '#007bff'; 
            this.innerText = '📋 COPIAR PARA O WHATSAPP / CRM'; 
        }}, 2500);
    }}
    </script>
""", height=70)
