import streamlit as st

def render_timer_box(hora_brasilia, hora_coleta):
    """
    Renderiza o box de horários seguindo o padrão visual do seu sistema
    """
    st.markdown(f"""
        <div style="
            background-color: #1d2129; 
            padding: 15px; 
            border-radius: 12px; 
            border: 1px solid #30363d; 
            margin-bottom: 25px;
            text-align: center;
            font-family: sans-serif;
            display: flex;
            justify-content: center;
            gap: 20px;
        ">
            <span style="color: #ffffff;">
                🕒 <b style="color: #4da3ff;">Brasília:</b> {hora_brasilia}
            </span>
            <span style="border-left: 1px solid #30363d; padding-left: 20px; color: #ffffff;">
                📥 <b style="color: #4da3ff;">Última Coleta:</b> {hora_coleta}
            </span>
        </div>
    """, unsafe_allow_html=True)

def apply_styles():
    st.markdown("""
        <style>
        /* Fundo Geral */
        .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
        
        /* Textos e Títulos */
        h1, h2, h3, p, label, .stMarkdown { color: #ffffff !important; }
        
        /* Inputs e Campos de Texto */
        .stTextInput input, .stSelectbox div, .stTextArea textarea {
            background-color: #1d2129 !important; 
            color: white !important;
            border: 1px solid #30363d !important;
        }
        
        /* Barra Lateral */
        section[data-testid="stSidebar"] { background-color: #161b22 !important; }
        
        /* Estilização de Metrics */
        [data-testid="stMetricValue"] { 
            font-size: 35px; 
            color: #4da3ff !important; 
            font-weight: bold; 
        }
        [data-testid="stMetric"] { 
            background-color: #1d2129; 
            padding: 15px; 
            border-radius: 12px; 
            border: 1px solid #30363d; 
        }
        
        /* Rodapé Fixo */
        .footer { 
            position: fixed; 
            left: 0; 
            bottom: 0; 
            width: 100%; 
            background-color: rgba(13, 17, 23, 0.9); 
            color: #8b949e; 
            text-align: center; 
            padding: 5px; 
            font-size: 13px; 
            font-weight: bold; 
            z-index: 100; 
        }
        </style>
        <div class="footer"> © João Vitor Ruiz Barboza </div>
        """, unsafe_allow_html=True)
