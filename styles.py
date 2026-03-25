import streamlit as st

def apply_styles():
    st.markdown("""
        <style>
        /* FUNDO E TEXTO GLOBAL */
        [data-testid="stAppViewContainer"] {
            background-color: #0d1117 !important;
            color: #c9d1d9 !important;
        }
        
        [data-testid="stHeader"] {
            background-color: rgba(0,0,0,0) !important;
        }

        /* TÍTULOS E LABELS */
        h1, h2, h3, .stWidgetLabel p, label {
            color: #ffffff !important;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        /* INPUTS */
        div[data-baseweb="input"], 
        div[data-baseweb="base-input"], 
        div[data-baseweb="select"] > div,
        div[data-baseweb="textarea"] {
            background-color: #161b22 !important;
            border: 1px solid #30363d !important;
            border-radius: 8px !important;
        }

        /* RADIO BUTTONS (REDONDOS) */
        /* Estilo da bolinha desmarcada */
        div[data-testid="stRadio"] [data-baseweb="radio"] div:first-child {
            background-color: #161b22 !important;
            border-color: #30363d !important;
        }

        /* Quando checado (fundo vermelho) */
        div[data-testid="stRadio"] [aria-checked="true"] div:first-child {
            background-color: #ff4b4b !important;
            border-color: #ff4b4b !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }

        /* O ponto branco central do Radio */
        div[data-testid="stRadio"] [aria-checked="true"] div:first-child::after {
            content: "" !important;
            width: 8px !important;
            height: 8px !important;
            background-color: white !important;
            border-radius: 50% !important;
            display: block !important;
        }

        /* CHECKBOXES (QUADRADOS) */
        div[data-testid="stCheckbox"] [data-baseweb="checkbox"] div:first-child {
            background-color: #161b22 !important;
            border-color: #30363d !important;
        }

        div[data-testid="stCheckbox"] [aria-checked="true"] div:first-child {
            background-color: #ff4b4b !important;
            border-color: #ff4b4b !important;
        }
        
        /* BOTÕES */
        button[kind="primary"] {
            background-color: #238636 !important;
            border: none !important;
            border-radius: 6px !important;
            color: white !important;
        }

        button[kind="secondary"] {
            background-color: #21262d !important;
            color: #f85149 !important;
            border: 1px solid #30363d !important;
        }

        /* DIVISOR */
        hr {
            border-top: 1px solid #30363d !important;
        }

        /* ÁREA DE CÓDIGO */
        code {
            background-color: #010409 !important;
            color: #7ee787 !important;
        }
        </style>
    """, unsafe_allow_html=True)
