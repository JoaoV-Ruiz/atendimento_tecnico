import streamlit as st

def apply_styles():
    st.markdown("""
        <style>
        /* 1. Fundo Principal e Sidebar */
        [data-testid="stAppViewContainer"] {
            background-color: #0e1117;
        }
        
        /* 2. Estilização dos Inputs (Dark Mode) */
        input, textarea, .stSelectbox div[data-baseweb="select"] {
            background-color: #1d2129 !important;
            color: #ffffff !important;
            border: 1px solid #30363d !important;
            border-radius: 8px !important;
        }

        /* 3. Estilização dos Containers/Cards (Fundo levemente mais claro que o principal) */
        div[data-testid="stVerticalBlock"] > div:has(div.stRadio), 
        .st-emotion-cache-12w0qpk {
            background-color: #161b22 !important;
            padding: 20px !important;
            border-radius: 12px !important;
            border: 1px solid #30363d !important;
            margin-bottom: 10px !important;
        }

        /* 4. Títulos e Subtítulos */
        h1, h2, h3, label, p, .stMarkdown {
            color: #e6edf3 !important;
        }

        /* 5. Ajuste nos Radios (Bolinhas de seleção) */
        div[data-testid="stRadio"] label {
            background-color: transparent !important;
            border: none !important;
            color: #c9d1d9 !important;
        }

        /* 6. Info Box (📍 Localidade) - Azul Dark */
        div[data-testid="stNotification"] {
            background-color: #0d1117 !important;
            border: 1px solid #388bfd !important;
            color: #58a6ff !important;
        }

        /* 7. Botão Primário (Salvar) */
        button[kind="primary"] {
            background-color: #238636 !important;
            border: none !important;
            color: white !important;
        }
        
        button[kind="primary"]:hover {
            background-color: #2ea043 !important;
        }

        /* 8. Botão Secundário (Limpar) */
        button[kind="secondary"] {
            background-color: #30363d !important;
            color: #f85149 !important;
            border: 1px solid #f85149 !important;
        }

        /* 9. Área de Código (Máscara) */
        code {
            background-color: #0d1117 !important;
            color: #7ee787 !important;
        }
        </style>
    """, unsafe_allow_html=True)
