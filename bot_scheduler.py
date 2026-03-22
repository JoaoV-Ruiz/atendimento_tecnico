import os
import json
from modules import amarelos

# Mock do st.secrets para o script funcionar fora do Streamlit
class MockSecrets:
    def __getitem__(self, key):
        return os.environ.get(key)

# Injetando os segredos do ambiente no que o módulo amarelos espera
import streamlit as st
st.secrets = MockSecrets()

if __name__ == "__main__":
    print("🚀 Iniciando coleta via GitHub Actions...")
    sucesso = amarelos.realizar_coleta_e_envio_automatizado()
    if sucesso:
        print("✅ Relatório enviado com sucesso!")
    else:
        print("❌ Falha no envio.")
        exit(1) # Avisa o GitHub que deu erro
