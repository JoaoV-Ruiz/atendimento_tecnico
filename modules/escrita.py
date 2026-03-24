import streamlit as st
import speech_recognition as sr
import tempfile
import os
import streamlit.components.v1 as components
import json

def render():
    st.title("🎙️ Bot Escrita por Microfone")
    st.write("Grave seu áudio e veja o texto convertido!")
    
    # Inicializar estado
    if 'audio_file' not in st.session_state:
        st.session_state.audio_file = None
    if 'reset_counter' not in st.session_state:
        st.session_state.reset_counter = 0
    
    # Botão para regravar
    if st.button("Regravar"):
        st.session_state.audio_file = None
        st.session_state.reset_counter += 1
        st.rerun()
    
    # Input de áudio com chave dinâmica para resetar
    audio_file = st.audio_input("Fale agora e clique em 'Stop' para enviar", key=f"audio_input_{st.session_state.reset_counter}")
    
    if audio_file is not None:
        st.session_state.audio_file = audio_file
        st.audio(audio_file, format="audio/wav")
        
        # Salvar temporariamente
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_filename = temp_file.name
            temp_file.write(audio_file.getvalue())
        
        try:
            # Reconhecer
            reconhecedor = sr.Recognizer()
            with sr.AudioFile(temp_filename) as source:
                audio_data = reconhecedor.record(source)
                texto = reconhecedor.recognize_google(audio_data, language='pt-BR')
            
            st.success("✅ Texto reconhecido!")
            
            # Exibir texto
            st.write(f"**Texto:** {texto}")
            
            # Botão para copiar usando JS
            js_copy = json.dumps(texto)
            components.html(f"""
                <button id="cp" style="width:100%; height:40px; background:#4da3ff; color:white; border:none; border-radius:6px; cursor:pointer; font-weight:bold; font-family:sans-serif;">📋 COPIAR TEXTO</button>
                <script>
                document.getElementById('cp').onclick = function() {{
                    const t = document.createElement("textarea"); t.value = {js_copy}; document.body.appendChild(t);
                    t.select(); document.execCommand('copy'); document.body.removeChild(t);
                    const btn = document.getElementById('cp'); btn.style.background = '#28a745'; btn.innerText = '✅ COPIADO!';
                    setTimeout(() => {{ btn.style.background = '#4da3ff'; btn.innerText = '📋 COPIAR TEXTO'; }}, 2000);
                }}
                </script>
            """, height=50)
        
        except sr.UnknownValueError:
            st.error("❌ Não consegui entender o áudio.")
        except Exception as e:
            st.error(f"❌ Erro: {e}")
        finally:
            # Limpar arquivo temporário
            os.unlink(temp_filename)
    
    st.write("---")
