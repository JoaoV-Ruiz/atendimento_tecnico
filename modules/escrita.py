import streamlit as st
import speech_recognition as sr
import tempfile
import os
import streamlit.components.v1 as components
import json
from styles import apply_styles

def render():
    apply_styles()

    st.title("🎙️ Escrita por Microfone")
    
    if 'reset_counter' not in st.session_state:
        st.session_state.reset_counter = 0

    col1, col2 = st.columns([4, 1])
    with col1:
        st.write("Grave seu áudio e veja o texto convertido!")
    with col2:
        if st.button("🔄 Limpar", use_container_width=True):
            st.session_state.reset_counter += 1
            st.rerun()

    # O audio_input do Streamlit já captura o áudio, não precisa de PyAudio aqui
    audio_file = st.audio_input(
        "Fale agora e clique em 'Stop' para enviar", 
        key=f"audio_input_{st.session_state.reset_counter}"
    )

    if audio_file is not None:
        st.audio(audio_file, format="audio/wav")
        
        with st.spinner("🤖 Convertendo voz em texto..."):
            # Usamos um arquivo temporário para que o Recognizer possa ler
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_filename = temp_file.name
                temp_file.write(audio_file.getvalue())
            
            try:
                reconhecedor = sr.Recognizer()
                with sr.AudioFile(temp_filename) as source:
                    # Ajuste opcional para ruído
                    reconhecedor.adjust_for_ambient_noise(source)
                    audio_data = reconhecedor.record(source)
                    
                    # Chamada da API
                    texto = reconhecedor.recognize_google(audio_data, language='pt-BR')
                
                st.success("✅ Texto reconhecido!")
                
                # Exibição do resultado
                st.markdown(f"""
                    <div style="background:#1d2129; padding:15px; border-radius:10px; border:1px solid #30363d;">
                        {texto}
                    </div>
                """, unsafe_allow_html=True)
                
                # Botão Copiar
                js_copy = json.dumps(texto)
                components.html(f"""
                    <button id="cp" style="width:100%; height:40px; background:#4da3ff; color:white; border:none; border-radius:6px; cursor:pointer; font-weight:bold;">📋 COPIAR TEXTO</button>
                    <script>
                    document.getElementById('cp').onclick = function() {{
                        const t = document.createElement("textarea"); t.value = {js_copy}; document.body.appendChild(t);
                        t.select(); document.execCommand('copy'); document.body.removeChild(t);
                        this.style.background = '#28a745'; this.innerText = '✅ COPIADO!';
                    }}
                    </script>
                """, height=50)

            except sr.UnknownValueError:
                st.error("❌ Não entendi o áudio. Tente falar mais perto do microfone.")
            except Exception as e:
                st.error(f"❌ Erro no processamento: {e}")
            finally:
                if os.path.exists(temp_filename):
                    os.unlink(temp_filename)
