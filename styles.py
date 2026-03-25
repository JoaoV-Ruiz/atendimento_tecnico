import streamlit as st

def apply_styles():
    st.markdown("""
        <style>
        /* 1. FUNDO E TEXTO GLOBAL */
        [data-testid="stAppViewContainer"] {
            background-color: #0d1117 !important;
            color: #c9d1d9 !important;
        }
        
        [data-testid="stHeader"] {
            background-color: rgba(0,0,0,0) !important;
        }

        /* 2. TÍTULOS E LABELS */
        h1, h2, h3, .stWidgetLabel p, label {
            color: #ffffff !important;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        /* 3. INPUTS GERAIS (TEXTO, SELECT, TEXTAREA) */
        div[data-baseweb="input"], 
        div[data-baseweb="base-input"], 
        div[data-baseweb="select"] > div,
        div[data-baseweb="textarea"] {
            background-color: #161b22 !important;
            border: 1px solid #30363d !important;
            border-radius: 8px !important;
        }

        /* 4. DESIGN CORRIGIDO: RADIO E CHECKBOX (SEM BORDAS NO TEXTO) */
        
        /* Remove bordas esquisitas e caixas de seleção ao redor do texto */
        div[data-testid="stRadio"] div, 
        div[data-testid="stCheckbox"] div,
        div[data-baseweb="radio"] div,
        div[data-baseweb="checkbox"] div {
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
        }

        /* Estilo da Caixa/Círculo quando DESMARCADO */
        div[data-testid="stRadio"] [data-baseweb="radio"] div:first-child,
        div[data-testid="stCheckbox"] [data-baseweb="checkbox"] div:first-child {
            background-color: #161b22 !important;
            border: 2px solid #30363d !important; /* Borda um pouco mais grossa para ver melhor */
        }

        /* Estilo quando MARCADO (RADIO) - Deixa o vermelho bem vivo */
        div[data-testid="stRadio"] [aria-checked="true"] div:first-child {
            background-color: #ffffff !important; /* Fundo branco para o ponto vermelho destacar */
            border-color: #ff4b4b !important;
        }

        /* O ponto central do Radio selecionado (Vermelho Intenso) */
        div[data-testid="stRadio"] [aria-checked="true"] div:first-child div {
            background-color: #ff4b4b !important;
            width: 12px !important;
            height: 12px !important;
            display: block !important;
        }

        /* Estilo quando MARCADO (CHECKBOX) */
        div[data-testid="stCheckbox"] [aria-checked="true"] div:first-child {
            background-color: #ff4b4b !important;
            border-color: #ff4b4b !important;
        }

        /* Garante que o ícone de check (SVG) fique branco e nítido */
        div[data-testid="stCheckbox"] [aria-checked="true"] div:first-child svg {
            fill: white !important;
            stroke: white !important;
            stroke-width: 2px !important;
        }

        /* Texto ao lado (Labels) - Remove qualquer fundo ou borda */
        div[data-testid="stRadio"] label, 
        div[data-testid="stCheckbox"] label {
            color: #c9d1d9 !important;
            border: none !important;
            background: none !important;
        }

        /* 5. BOTÕES */
        button[kind="primary"] {
            background-color: #238636 !important;
            border: none !important;
            border-radius: 6px !important;
            color: white !important;
            width: 100%;
        }

        button[kind="secondary"] {
            background-color: #21262d !important;
            color: #f85149 !important;
            border: 1px solid #30363d !important;
            width: 100%;
        }

        /* 6. DIVISOR E CÓDIGO */
        hr {
            border-top: 1px solid #30363d !important;
        }

        code {
            background-color: #010409 !important;
            color: #7ee787 !important;
        }

        /* 7. MÁSCARA PERSONALIZADA (SEM FUNDO NAS LETRAS) */
        .mascara-container {
            background-color: #161b22; 
            padding: 20px; 
            border-radius: 10px; 
            border: 1px solid #30363d;
        }
        
        .mascara-texto {
            color: #7ee787 !important; 
            font-family: 'Courier New', Courier, monospace !important;
            font-size: 14px !important;
            white-space: pre-wrap !important;
            line-height: 1.6 !important;
            margin: 0 !important;
            background: none !important;
        }
        </style>
    """, unsafe_allow_html=True)
