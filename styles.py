import streamlit as st

def apply_styles():
    st.markdown("""
        <style>
        .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
        h1, h2, h3, p, label, .stMarkdown { color: #ffffff !important; }
        .stTextInput input, .stSelectbox div, .stTextArea textarea {
            background-color: #1d2129 !important; color: white !important;
            border: 1px solid #30363d !important;
        }
        section[data-testid="stSidebar"] { background-color: #161b22 !important; }
        [data-testid="stMetricValue"] { font-size: 35px; color: #4da3ff !important; font-weight: bold; }
        [data-testid="stMetric"] { background-color: #1d2129; padding: 15px; border-radius: 12px; border: 1px solid #30363d; }
        .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: rgba(13, 17, 23, 0.9); 
                  color: #8b949e; text-align: center; padding: 5px; font-size: 13px; font-weight: bold; z-index: 100; }
        </style>
        <div class="footer"> © João Vitor Ruiz Barboza </div>
        """, unsafe_allow_html=True)