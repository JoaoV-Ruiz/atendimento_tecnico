import streamlit as st

def apply_styles():
    st.markdown("""
        <style>
        /* 1. FUNDO E ESTRUTURA GERAL */
        [data-testid="stAppViewContainer"] {
            background-color: #0d1117 !important;
            color: #c9d1d9 !important;
        }

        /* 2. CORREÇÃO DA QUEBRA DE TEXTO */
        /* Aplica apenas em markdown puro, sem afetar labels de widgets */
        div[data-testid="stMarkdownContainer"] > p {
            background-color: transparent !important;
            color: #ffffff !important;
            margin: 0 !important;
            /* REMOVIDO: display: inline-block e width: auto
               Esses eram os causadores do fundo estranho nas checkboxes */
        }

        /* 3. RADIOS */
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

        /* 4. CHECKBOXES */
        div[data-testid="stCheckbox"] {
            background-color: transparent !important;
        }
        div[data-testid="stCheckbox"] label {
            background-color: transparent !important;
        }
        /* Garante que nenhum filho herde fundo indevido */
        div[data-testid="stCheckbox"] * {
            background-color: transparent !important;
        }
        /* Caixa do checkbox em si */
        div[data-testid="stCheckbox"] [data-baseweb="checkbox"] div:first-child {
            background-color: #1d2129 !important;
            border: 1px solid #444c56 !important;
            border-radius: 4px !important;
        }
        div[data-testid="stCheckbox"] [data-baseweb="checkbox"][aria-checked="true"] div:first-child {
            background-color: #ff4b4b !important;
            border-color: #ff4b4b !important;
        }

        /* 5. INPUTS (TEXTO E SELECT) */
        div[data-baseweb="input"], div[data-baseweb="base-input"],
        div[data-baseweb="select"] > div, div[data-baseweb="textarea"] {
            background-color: #161b22 !important;
            border: 1px solid #30363d !important;
            border-radius: 8px !important;
        }

        /* 6. TÍTULOS E LABELS DOS CAMPOS */
        .stWidgetLabel p, label {
            color: #f0f6fc !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
        }

        /* 7. BOTÕES */
        button[kind="primary"] {
            background-color: #238636 !important;
            border: none !important;
        }
        </style>
    """, unsafe_allow_html=True)
