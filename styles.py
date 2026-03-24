import streamlit as st

def apply_styles():
    st.markdown("""
        <style>
        /* 1. FUNDO GLOBAL E ESTRUTURA */
        html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background-color: #0e1117 !important;
            color: #e6edf3 !important;
        }

        /* 2. SIDEBAR (MENU LATERAL) */
        [data-testid="stSidebar"] {
            background-color: #161b22 !important;
            border-right: 1px solid #30363d;
        }

        /* 3. BLINDAGEM DOS INPUTS (PONTO 2 - ANTI-FUNDO BRANCO) */
        /* Atacamos a estrutura interna 'Base Web' do Streamlit */
        [data-baseweb="base-input"], [data-baseweb="input"], [data-baseweb="textarea"] {
            background-color: #1d2129 !important;
            border-radius: 6px !important;
        }

        .stTextInput input, .stTextArea textarea {
            background-color: #1d2129 !important;
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important; /* Força cor branca no Chrome/Edge */
            box-shadow: none !important;
            border: 1px solid #444c56 !important;
            border-radius: 6px !important;
        }

        /* Ajuste de Hover e Foco (Evita que o fundo mude para branco ao clicar) */
        [data-baseweb="base-input"]:hover, 
        [data-baseweb="input"]:focus-within,
        .stTextInput input:focus, 
        .stTextArea textarea:focus {
            background-color: #0d1117 !important;
            border-color: #58a6ff !important;
            color: #ffffff !important;
        }

        /* 4. LABELS (NOMES DOS CAMPOS) */
        .stWidgetLabel p, label {
            color: #f0f6fc !important;
            font-weight: 600 !important;
        }

        /* 5. CARDS / CONTAINERS */
        div[data-testid="stVerticalBlock"] > div:has(div.stRadio),
        .st-emotion-cache-12w0qpk, .st-emotion-cache-6qob1r {
            background-color: #161b22 !important;
            padding: 15px !important;
            border-radius: 10px !important;
            border: 1px solid #30363d !important;
        }

        /* 6. BOTÕES */
        button[kind="primary"] {
            background-color: #238636 !important;
            color: white !important;
            border: none !important;
            width: 100%;
        }
        
        button[kind="secondary"] {
            background-color: #21262d !important;
            color: #f85149 !important;
            border: 1px solid #30363d !important;
        }

        /* 7. INFO BOX (LOCALIDADE) */
        div[data-testid="stNotification"] {
            background-color: #0d1117 !important;
            border: 1px solid #388bfd !important;
            color: #58a6ff !important;
        }

        /* 8. MÁSCARA E CÓDIGO */
        code, .stCodeBlock {
            background-color: #010409 !important;
            border: 1px solid #30363d !important;
            color: #7ee787 !important;
        }

        /* 9. RADIOS E CHECKBOXES */
        div[data-testid="stCheckbox"] p, div[data-testid="stRadio"] p {
            color: #c9d1d9 !important;
        }
        
        /* 10. SELECTBOX (TÉCNICO) */
        [data-baseweb="select"] > div {
            background-color: #1d2129 !important;
            color: #ffffff !important;
            border: 1px solid #444c56 !important;
        }
        </style>
    """, unsafe_allow_html=True)
