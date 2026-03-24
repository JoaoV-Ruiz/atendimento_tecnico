import streamlit as st

def apply_styles():
    st.markdown("""
        <style>
        /* 1. FUNDO GLOBAL DO APP */
        html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background-color: #0e1117 !important;
            color: #e6edf3 !important;
        }

        /* 2. SIDEBAR (MENU LATERAL) */
        [data-testid="stSidebar"] {
            background-color: #161b22 !important;
            border-right: 1px solid #30363d;
        }

        /* 3. INPUTS, TEXTAREAS E SELECTBOX (FUNDO PRETO, LETRA BRANCA) */
        /* Força o fundo escuro e texto branco em todos os campos de entrada */
        input, textarea, [data-baseweb="select"] > div, 
        .stTextArea textarea, .stTextInput input, .stSelectbox div[data-baseweb="select"] {
            background-color: #1d2129 !important;
            color: #ffffff !important;
            border: 1px solid #444c56 !important;
            border-radius: 6px !important;
            -webkit-text-fill-color: #ffffff !important; /* Essencial para alguns navegadores */
        }

        /* Garante que o texto digitado seja branco e visível */
        input:focus, textarea:focus {
            background-color: #0d1117 !important;
            color: #ffffff !important;
            border-color: #58a6ff !important;
            outline: none !important;
        }

        /* 4. LABELS (NOMES DOS CAMPOS) */
        .stWidgetLabel p, label {
            color: #f0f6fc !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
        }

        /* 5. CARDS / CONTAINERS (AGRUPAMENTOS) */
        div[data-testid="stVerticalBlock"] > div:has(div.stRadio),
        .st-emotion-cache-12w0qpk, .st-emotion-cache-6qob1r {
            background-color: #161b22 !important;
            padding: 15px !important;
            border-radius: 10px !important;
            border: 1px solid #30363d !important;
        }

        /* 6. BOTÕES */
        /* Botão Salvar (Verde) */
        button[kind="primary"] {
            background-color: #238636 !important;
            color: white !important;
            border: none !important;
            width: 100%;
        }
        button[kind="primary"]:hover {
            background-color: #2ea043 !important;
        }

        /* Botão Limpar / Trash */
        button[kind="secondary"] {
            background-color: #21262d !important;
            color: #f85149 !important;
            border: 1px solid #30363d !important;
        }
        button[kind="secondary"]:hover {
            border-color: #f85149 !important;
            background-color: #30363d !important;
        }

        /* 7. TEXTO DE INFO (📍 LOCALIDADE) */
        div[data-testid="stNotification"] {
            background-color: #0d1117 !important;
            border: 1px solid #388bfd !important;
            color: #58a6ff !important;
        }

        /* 8. CÓDIGO E MÁSCARA */
        code, .stCodeBlock {
            background-color: #010409 !important;
            border: 1px solid #30363d !important;
            color: #7ee787 !important;
        }

        /* 9. RADIOS E CHECKBOXES (TEXTO) */
        div[data-testid="stCheckbox"] p, div[data-testid="stRadio"] p {
            color: #c9d1d9 !important;
        }

        /* 10. SCROLLBAR (OPCIONAL - PARA FICAR DARK) */
        ::-webkit-scrollbar {
            width: 10px;
        }
        ::-webkit-scrollbar-track {
            background: #0e1117;
        }
        ::-webkit-scrollbar-thumb {
            background: #30363d;
            border-radius: 5px;
        }
        </style>
    """, unsafe_allow_html=True)
