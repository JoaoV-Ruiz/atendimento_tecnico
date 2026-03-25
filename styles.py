import streamlit as st

def apply_styles():
    st.markdown("""
        <style>
        /* FUNDO E TEXTO GLOBAL */
        [data-testid="stAppViewContainer"] {
            background-color: #0d1117 !important;
            color: #c9d1d9 !important;
        }

        /* REMOVE BORDAS FANTASMAS E FOCO NO TEXTO */
        div[data-testid="stRadio"] div, 
        div[data-testid="stCheckbox"] div {
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
            background-color: transparent !important;
        }

        /* AJUSTE DO RÁDIO (CÍRCULO) */
        /* Estado Desmarcado */
        div[data-testid="stRadio"] [data-baseweb="radio"] div:first-child {
            background-color: #161b22 !important;
            border: 2px solid #30363d !important;
        }

        /* Estado Marcado */
        div[data-testid="stRadio"] [aria-checked="true"] div:first-child {
            background-color: #ff4b4b !important; /* Fundo do círculo fica vermelho */
            border-color: #ff4b4b !important;
        }

        /* O ponto central do Radio (Branco para dar contraste no Vermelho) */
        div[data-testid="stRadio"] [aria-checked="true"] div:first-child div {
            background-color: white !important;
            width: 8px !important;
            height: 8px !important;
            display: block !important;
        }

        /* AJUSTE DO CHECKBOX (QUADRADO) */
        div[data-testid="stCheckbox"] [aria-checked="true"] div:first-child {
            background-color: #ff4b4b !important;
            border-color: #ff4b4b !important;
        }

        /* TEXTO DAS LABELS */
        div[data-testid="stRadio"] label p, 
        div[data-testid="stCheckbox"] label p {
            color: #ffffff !important;
            font-size: 14px !important;
            background: none !important;
            border: none !important;
        }

        /* INPUTS DE TEXTO */
        div[data-baseweb="input"], div[data-baseweb="textarea"] {
            background-color: #161b22 !important;
            border: 1px solid #30363d !important;
        }

        /* BOTÕES */
        button[kind="primary"] { background-color: #238636 !important; width: 100%; }
        button[kind="secondary"] { background-color: #21262d !important; color: #f85149 !important; width: 100%; }
        </style>
    """, unsafe_allow_html=True)
