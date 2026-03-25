import streamlit as st

def apply_styles():
    st.markdown("""
        <style>
        /* 1. FUNDO E ESTRUTURA GERAL */
        [data-testid="stAppViewContainer"] {
            background-color: #0d1117 !important;
            color: #c9d1d9 !important;
        }

        /* 2. RADIOS - empurra levemente para baixo sem usar st.markdown de espaço */
        div[data-testid="stRadio"] {
            margin-top: 6px !important;
        }
        div[data-testid="stRadio"] [data-baseweb="radio"] {
            background-color: transparent !important;
            margin-bottom: 4px !important;
        }
        div[data-testid="stRadio"] [data-baseweb="radio"] div:first-child {
            background-color: #1d2129 !important;
            border: 1px solid #444c56 !important;
        }
        div[data-testid="stRadio"] [data-baseweb="radio"][aria-checked="true"] div:first-child {
            background-color: #ff4b4b !important;
            border-color: #ff4b4b !important;
        }

        /* 3. CHECKBOXES */
        div[data-testid="stCheckbox"] [data-baseweb="checkbox"] div:first-child {
            background-color: #1d2129 !important;
            border: 1px solid #444c56 !important;
            border-radius: 4px !important;
        }
        div[data-testid="stCheckbox"] [data-baseweb="checkbox"][aria-checked="true"] div:first-child {
            background-color: #ff4b4b !important;
            border-color: #ff4b4b !important;
        }

        /* 4. INPUTS (TEXTO E SELECT) */
        div[data-baseweb="input"], div[data-baseweb="base-input"],
        div[data-baseweb="select"] > div, div[data-baseweb="textarea"] {
            background-color: #161b22 !important;
            border: 1px solid #30363d !important;
            border-radius: 8px !important;
        }

        /* 5. TÍTULOS E LABELS DOS CAMPOS */
        .stWidgetLabel p {
            color: #f0f6fc !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
        }

        /* 6. BOTÕES */
        button[kind="primary"] {
            background-color: #238636 !important;
            border: none !important;
        }
        </style>
    """, unsafe_allow_html=True)
