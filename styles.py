import streamlit as st

def render_timer_box(hora_brasilia, hora_coleta):
    """
    Renderiza o box de horários seguindo o padrão visual do seu sistema
    """
    st.markdown(f"""
        <div style="
            background-color: #1d2129; 
            padding: 15px; 
            border-radius: 12px; 
            border: 1px solid #30363d; 
            margin-bottom: 25px;
            text-align: center;
            font-family: sans-serif;
            display: flex;
            justify-content: center;
            gap: 20px;
        ">
            <span style="color: #ffffff;">
                🕒 <b style="color: #4da3ff;">Brasília:</b> {hora_brasilia}
            </span>
            <span style="border-left: 1px solid #30363d; padding-left: 20px; color: #ffffff;">
                📥 <b style="color: #4da3ff;">Última Coleta:</b> {hora_coleta}
            </span>
        </div>
    """, unsafe_allow_html=True)

def apply_styles():
    st.markdown("""
        <style>
        /* 1. Remove bordas de foco e contornos genéricos que o Streamlit cria */
        .stTextInput div, .stSelectbox div, .stTextArea div {
            border: none !important;
            box-shadow: none !important;
        }

        /* 2. Aplica a borda apenas no campo real de input */
        div[data-baseweb="input"], div[data-baseweb="select"] {
            border: 1px solid #30363d !important;
            border-radius: 8px !important;
            background-color: #0d1117 !important;
        }

        /* 3. Estiliza o estado de foco (quando clica no campo) */
        div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within {
            border: 1px solid #4da3ff !important;
            box-shadow: 0 0 0 1px #4da3ff !important;
        }

        /* 4. Ajuste específico para Selectbox (evita borda dupla no dropdown) */
        div[role="combobox"] {
            border: none !important;
        }

        /* 5. Ajuste de cor do texto para garantir leitura */
        input, select, textarea {
            color: #ffffff !important;
        }

        /* 6. Remove a borda vermelha chata de erro/validação se houver */
        .stTextInput fieldset, .stSelectbox fieldset {
            border: none !important;
        }
        </style>
    """, unsafe_allow_html=True)
