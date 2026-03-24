import streamlit as st

def apply_styles():
    st.markdown("""
        <style>
        /* 1. FORÇAR FUNDO ESCURO GLOBAL */
        html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background-color: #0e1117 !important;
            color: #e6edf3 !important;
        }

        /* 2. PADRONIZAR SIDEBAR (MENU ESQUERDO) */
        [data-testid="stSidebar"] {
            background-color: #161b22 !important;
            border-right: 1px solid #30363d;
        }

        /* 3. INPUTS, SELECTBOX E TEXTAREAS (ESTILO GRAFITE) */
        input, textarea, .stSelectbox div[data-baseweb="select"] {
            background-color: #1d2129 !important;
            color: #ffffff !important;
            border: 1px solid #30363d !important;
            border-radius: 6px !important;
        }
        
        /* Cor do placeholder (texto de fundo do input) */
        ::placeholder {
            color: #8b949e !important;
            opacity: 1;
        }

        /* 4. CARDS/CONTAINERS (PARA DEMANDA INFRA E BATIDA DE CAIXA) */
        [data-testid="stVerticalBlock"] > div:has(div.stRadio),
        .st-emotion-cache-12w0qpk, .st-emotion-cache-6qob1r {
            background-color: #161b22 !important;
            padding: 20px !important;
            border-radius: 12px !important;
            border: 1px solid #30363d !important;
            margin-bottom: 15px !important;
        }

        /* 5. LABELS E TÍTULOS */
        label, p, h1, h2, h3, span {
            color: #f0f6fc !important;
            font-weight: 500 !important;
        }

        /* 6. BOTÕES PERSONALIZADOS */
        /* Primário (Salvar) */
        button[kind="primary"] {
            background-color: #238636 !important;
            border: 1px solid rgba(240,246,252,0.1) !important;
            color: white !important;
            width: 100%;
        }
        
        /* Secundário (Limpar/🗑️) */
        button[kind="secondary"] {
            background-color: #21262d !important;
            color: #f85149 !important;
            border: 1px solid #30363d !important;
        }
        button[kind="secondary"]:hover {
            border-color: #f85149 !important;
            background-color: #30363d !important;
        }

        /* 7. INFO BOX E ALERTAS */
        div[data-testid="stNotification"] {
            background-color: #0d1117 !important;
            border: 1px solid #388bfd !important;
            color: #58a6ff !important;
        }

        /* 8. TABELAS E CÓDIGO (MÁSCARA) */
        code, .stCodeBlock {
            background-color: #010409 !important;
            border: 1px solid #30363d !important;
            color: #7ee787 !important;
        }

        /* 9. CHECKBOXES E RADIOS */
        div[data-testid="stCheckbox"] p, div[data-testid="stRadio"] p {
            color: #c9d1d9 !important;
        }
        
        /* 10. REMOVER O PADDING EXCESSIVO DO TOPO */
        .block-container {
            padding-top: 2rem !important;
        }
        </style>
    """, unsafe_allow_html=True)
