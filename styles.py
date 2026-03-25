import streamlit as st

def apply_styles():
    st.markdown("""
        <style>
        /* 1. FUNDO E TEXTO GLOBAL */
        [data-testid="stAppViewContainer"] {
            background-color: #0d1117 !important;
            color: #c9d1d9 !important;
        }

        /* 2. INPUTS DE TEXTO E SELECT */
        div[data-baseweb="input"], div[data-baseweb="base-input"], 
        div[data-baseweb="select"] > div, div[data-baseweb="textarea"] {
            background-color: #161b22 !important;
            border: 1px solid #30363d !important;
            border-radius: 8px !important;
        }

        /* 3. UNIFORMIZAÇÃO DE RADIOS (REDONDOS) E CHECKBOXES (QUADRADOS) */
        
        /* Cor da borda e fundo quando NÃO selecionado */
        div[data-testid="stCheckbox"] [data-baseweb="checkbox"] div:first-child,
        div[data-testid="stRadio"] [data-baseweb="radio"] div:first-child {
            background-color: #1d2129 !important;
            border: 1px solid #444c56 !important;
        }

        /* Cor quando SELECIONADO (Ambos ficam com fundo vermelho) */
        div[data-testid="stCheckbox"] [data-baseweb="checkbox"][aria-checked="true"] div:first-child,
        div[data-testid="stRadio"] [data-baseweb="radio"][aria-checked="true"] div:first-child {
            background-color: #ff4b4b !important;
            border-color: #ff4b4b !important;
        }

        /* Garante que o ponto interno do Radio seja branco para dar contraste */
        div[data-testid="stRadio"] [data-baseweb="radio"][aria-checked="true"] div:first-child::after {
            background-color: white !important;
        }

        /* Efeito de Hover (passar o mouse) */
        div[data-testid="stRadio"] [data-baseweb="radio"]:hover div:first-child,
        div[data-testid="stCheckbox"] [data-baseweb="checkbox"]:hover div:first-child {
            border-color: #58a6ff !important;
        }

        /* 4. LABELS */
        .stWidgetLabel p, label {
            color: #f0f6fc !important;
            font-weight: 600 !important;
        }

        /* 5. BOTÕES */
        button[kind="primary"] {
            background-color: #238636 !important;
            border: none !important;
            border-radius: 8px !important;
        }
        
        button[kind="secondary"] {
            background-color: #21262d !important;
            color: #f85149 !important;
            border: 1px solid #30363d !important;
        }

        /* 6. MÁSCARA DE TEXTO */
        code {
            background-color: #010409 !important;
            color: #7ee787 !important;
            border: 1px solid #30363d !important;
        }
        </style>
    """, unsafe_allow_html=True)
