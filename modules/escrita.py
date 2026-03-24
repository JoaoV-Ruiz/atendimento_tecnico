import streamlit as st
import speech_recognition as sr
import tempfile
import os
import streamlit.components.v1 as components
import json
from styles import apply_styles

def render():
    # Aplica o visual padrão do sistema e remove as bordas esquisitas
    apply_styles()

    st.title("🎙️ Escrita por Microfone")
    st.markdown("""
        Esta ferramenta converte sua fala em texto automaticamente. 
        Ideal para ditar observações rápidas ou relatórios de campo.
    """)

    # --- INICIALIZAÇÃO DO ESTADO ---
    if 'reset_counter' not in st.session_state:
        st.session_state.reset_counter = 0

    # --- INTERFACE ---
    with st.container():
        col1, col2 = st.columns([4, 1])
        with col1:
            st.subheader("Grave seu Áudio")
        with col2:
            # Botão para resetar o componente de áudio
            if st.button("🔄 Limpar", use_container_width=True):
                st.session_state.reset_counter += 1
                st.rerun()

    # Input de áudio oficial do Streamlit com chave dinâmica para reset
    audio_file = st.audio_input(
        "Clique no microfone para gravar, fale e clique em 'Stop' para processar", 
        key=f"audio_input_{st.session_state.reset_counter}"
    )

    if audio_file is not None:
        st.divider()
        st.audio(audio_file, format="audio/wav")
        
        # Processamento com Spinner para dar feedback visual
        with st.spinner("🤖 Reconhecendo sua voz..."):
            # Salvar temporariamente para o Recognizer ler
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_filename = temp_file.name
                temp_file.write(audio_file.getvalue())
            
            try:
                # Inicializa o reconhecedor
                reconhecedor = sr.Recognizer()
                with sr.AudioFile(temp_filename) as source:
                    audio_data = reconhecedor.record(source)
                    # Traduz para texto usando a API do Google (requer internet)
                    texto = reconhecedor.recognize_google(audio_data, language='pt-BR')
                
                st.success("✅ Texto reconhecido com sucesso!")
                
                # Exibe o texto em um box estilizado
                st.markdown(f"""
                    <div style="background:#1d2129; padding:20px; border-radius:10px; border:1px solid #30363d; color:white; margin-bottom:15px;">
                        <strong>Texto Convertido:</strong><br>
                        <p style="font-size:1.1rem; margin-top:10px;">{texto}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # --- BOTÃO COPIAR (JS INTEGRADO) ---
                js_copy = json.dumps(texto)
                components.html(f"""
                    <button id="cp" style="width:100%; height:45px; background:#4da3ff; color:white; border:none; border-radius:8px; cursor:pointer; font-weight:bold; font-size:16px; font-family:sans-serif;">📋 COPIAR TEXTO</button>
                    <script>
                    document.getElementById('cp').onclick = function() {{
                        const t = document.createElement("textarea"); t.value = {js_copy}; document.body.appendChild(t);
                        t.select(); document.execCommand('copy'); document.body.removeChild(t);
                        const btn = document.getElementById('cp'); 
                        btn.style.background = '#28a745'; btn.innerText = '✅ COPIADO!';
                        setTimeout(() => {{ 
                            btn.style.background = '#4da3ff'; btn.innerText = '📋 COPIAR TEXTO'; 
                        }}, 2000);
                    }}
                    </script>
                """, height=60)

            except sr.UnknownValueError:
                st.error("❌ O sistema não conseguiu entender o que foi dito. Tente falar mais pausadamente.")
            except sr.RequestError:
                st.error("❌ Erro de conexão com o serviço de reconhecimento.")
            except Exception as e:
                st.error(f"❌ Ocorreu um erro inesperado: {e}")
            finally:
                # Garante que o arquivo temporário seja apagado
                if os.path.exists(temp_filename):
                    os.unlink(temp_filename)

    st.divider()
    st.caption("Nota: Esta ferramenta utiliza processamento em nuvem. Certifique-se de estar em um ambiente com pouco ruído para melhor precisão.")
