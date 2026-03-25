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

        /* INPUTS (CAIXAS DE TEXTO E SELEÇÃO) */
        div[data-baseweb="input"], 
        div[data-baseweb="base-input"], 
        div[data-baseweb="select"] > div,
        div[data-baseweb="textarea"] {
            background-color: #161b22 !important;
            border: 1px solid #30363d !important;
            border-radius: 8px !important;
        }

        /* FOCO NO INPUT */
        div[data-baseweb="input"]:focus-within {
            border-color: #58a6ff !important;
            box-shadow: 0 0 0 1px #58a6ff !important;
        }

        /* --- AJUSTE DOS COMPONENTES DE SELEÇÃO --- */

        /* RADIO BUTTONS (REDONDOS) */
        /* Estilo base */
        div[data-testid="stRadio"] [data-baseweb="radio"] div:first-child {
            background-color: #161b22 !important;
            border-color: #30363d !important;
        }

        /* Quando checado (fundo vermelho) */
        div[data-testid="stRadio"] [aria-checked="true"] div:first-child {
            background-color: #ff4b4b !important;
            border-color: #ff4b4b !important;
        }

        /* Forçar o ponto branco central no Radio */
        div[data-testid="stRadio"] [aria-checked="true"] div:first-child::after {
            content: "";
            width: 6px;
            height: 6px;
            background-color: white !important;
            border-radius: 50%;
            display: block;
        }

        /* CHECKBOXES (QUADRADOS) */
        div[data-testid="stCheckbox"] [data-baseweb="checkbox"] div:first-child {
            background-color: #161b22 !important;
            border-color: #30363d !important;
        }

        div[data-testid="stCheckbox"] [aria-checked="true"] div:first-child {
            background-color: #ff4b4b !important;
            border-color: #ff4b4b !important;
        }
        
        /* Espaçamento entre as opções */
        div[data-testid="stRadio"] div[role="radiogroup"] {
            gap: 20px !important;
        }

        /* BOTÕES */
        button[kind="primary"] {
            background-color: #238636 !important;
            border: none !important;
            border-radius: 6px !important;
            padding: 0.5rem 1rem !important;
            font-weight: bold !important;
        }

        button[kind="secondary"] {
            background-color: #21262d !important;
            color: #f85149 !important;
            border: 1px solid #30363d !important;
        }

        /* DIVISOR */
        hr {
            border-top: 1px solid #30363d !important;
            margin: 1.5rem 0 !important;
        }

        /* ÁREA DE CÓDIGO (MÁSCARA) */
        code {
            background-color: #010409 !important;
            color: #7ee787 !important;
            border: 1px solid #30363d !important;
        }
        </style>
    """, unsafe_allow_html=True)

# Chamada da função para testar
apply_styles()

# Exemplos para visualização
st.title("Teste de Estilo")
st.radio("Escolha uma opção (Redonda):", ["Opção A", "Opção B", "Opção C"])
st.checkbox("Marque esta opção (Quadrada)")
st.text_input("Campo de texto", placeholder="Digite algo...")
st.button("Botão Primário", kind="primary")
