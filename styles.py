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

        /* INPUTS GERAIS */
        div[data-baseweb="input"], 
        div[data-baseweb="base-input"], 
        div[data-baseweb="select"] > div,
        div[data-baseweb="textarea"] {
            background-color: #161b22 !important;
            border: 1px solid #30363d !important;
            border-radius: 8px !important;
        }

        /* --- DESIGN UNIFICADO: RADIO E CHECKBOX --- */
        
        /* 1. Estilo da Caixa (Desmarcada) */
        div[data-testid="stRadio"] [data-baseweb="radio"] div:first-child,
        div[data-testid="stCheckbox"] [data-baseweb="checkbox"] div:first-child {
            background-color: #161b22 !important;
            border-radius: 4px !important; /* Deixa o Radio quadrado/levemente arredondado como o checkbox */
        }

        /* 2. Estilo da Caixa (Quando Marcada) */
        div[data-testid="stRadio"] [aria-checked="true"] div:first-child,
        div[data-testid="stCheckbox"] [aria-checked="true"] div:first-child {
            background-color: #ff4b4b !important;
            border-color: #ff4b4b !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }

        /* 3. O "Check" ou "Ponto" interno */
        /* Para o Radio parecer um Checkbox marcado, vamos usar um ícone ou ponto central */
        div[data-testid="stRadio"] [aria-checked="true"] div:first-child::after {
            content: "✓" !important; /* Adiciona um check no rádio também */
            color: white !important;
            font-size: 10px !important;
            font-weight: bold !important;
        }

        /* Remove o círculo interno padrão do Radio que o Streamlit tenta colocar */
        div[data-testid="stRadio"] [aria-checked="true"] div:first-child div {
            display: none !important;
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
