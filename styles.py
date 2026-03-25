import streamlit as st

def apply_styles():
    st.markdown("""
        <style>
        /* 1. FUNDO E TEXTO GLOBAL */
        [data-testid="stAppViewContainer"] {
            background-color: #0d1117 !important;
            color: #c9d1d9 !important;
        }

        /* 2. REMOVER FUNDO ESTRANHO DOS TEXTOS (LABELS) */
        div[data-testid="stMarkdownContainer"] p {
            background-color: transparent !important;
            background: none !important;
        }
        
        /* Remove o destaque de seleção do texto */
        .st-emotion-cache-16idsys p, .st-emotion-cache-809syv p {
            background-color: transparent !important;
        }

        /* 3. RADIOS (REDONDOS) */
        /* Estilo em repouso */
        div[data-testid="stRadio"] [data-baseweb="radio"] div:first-child {
            background-color: #1d2129 !important;
            border: 1px solid #444c56 !important;
            width: 18px !important;
            height: 18px !important;
        }

        /* Estilo selecionado (Preenchimento total em vermelho) */
        div[data-testid="stRadio"] [data-baseweb="radio"][aria-checked="true"] div:first-child {
            background-color: #ff4b4b !important;
            border-color: #ff4b4b !important;
        }

        /* O ponto interno do rádio */
        div[data-testid="stRadio"] [data-baseweb="radio"][aria-checked="true"] div:first-child::after {
            background-color: white !important;
            width: 6px !important;
            height: 6px !important;
        }

        /* 4. CHECKBOXES (QUADRADOS) */
        div[data-testid="stCheckbox"] [data-baseweb="checkbox"] div:first-child {
            background-color: #1d2129 !important;
            border: 1px solid #444c56 !important;
            border-radius: 4px !important;
        }

        div[data-testid="stCheckbox"] [data-baseweb="checkbox"][aria-checked="true"] div:first-child {
            background-color: #ff4b4b !important;
            border-color: #ff4b4b !important;
        }

        /* 5. INPUTS DE TEXTO */
        div[data-baseweb="input"], div[data-baseweb="base-input"], 
        div[data-baseweb="select"] > div, div[data-baseweb="textarea"] {
            background-color: #161b22 !important;
            border: 1px solid #30363d !important;
            border-radius: 8px !important;
        }

        /* 6. LABELS GERAIS */
        .stWidgetLabel p, label {
            color: #f0f6fc !important;
            font-weight: 600 !important;
        }
        </style>
    """, unsafe_allow_html=True)
