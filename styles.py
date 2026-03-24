import streamlit as st

def apply_styles():
    st.markdown("""
        <style>
        /* 1. Remove bordas de foco e contornos genéricos */
        .stTextInput div, .stSelectbox div, .stTextArea div {
            border: none !important;
            box-shadow: none !important;
        }

        /* 2. Aplica a borda apenas no campo real de input */
        div[data-baseweb="input"], div[data-baseweb="select"], textarea {
            border: 1px solid #30363d !important;
            border-radius: 8px !important;
            background-color: #0d1117 !important;
        }

        /* 3. Estado de foco */
        div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within {
            border: 1px solid #4da3ff !important;
            box-shadow: 0 0 0 1px #4da3ff !important;
        }

        /* 4. Cor do texto */
        input, select, textarea {
            color: #ffffff !important;
        }

        /* 5. Correção para Selectbox */
        div[role="combobox"] {
            border: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

def render_timer_box(hora_brasilia, hora_coleta):
    st.markdown(f"""
        <div style="background-color: #1d2129; padding: 15px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 25px; text-align: center; display: flex; justify-content: center; gap: 20px;">
            <span style="color: #ffffff;">🕒 <b style="color: #4da3ff;">Brasília:</b> {hora_brasilia}</span>
            <span style="border-left: 1px solid #30363d; padding-left: 20px; color: #ffffff;">📥 <b style="color: #4da3ff;">Última Coleta:</b> {hora_coleta}</span>
        </div>
    """, unsafe_allow_html=True)
