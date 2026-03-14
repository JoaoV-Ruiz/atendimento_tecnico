# --- REGISTRO SIMPLIFICADO NO GOOGLE SHEETS ---
        if st.button("💾 REGISTRAR NA PLANILHA", use_container_width=True, type="primary"):
            if not st.session_state.batida_proto or not st.session_state.batida_cx:
                st.error("Protocolo e Caixa são obrigatórios!")
            else:
                try:
                    with st.spinner('Enviando para o Google Sheets...'):
                        aba = conectar_google_sheets()
                        if aba:
                            fuso_br = pytz.timezone('America/Sao_Paulo')
                            data_hora = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M")
                            
                            # Dados: Data, Protocolo, Caixa e Portas
                            linha = [
                                str(data_hora), 
                                str(st.session_state.batida_proto), 
                                str(st.session_state.batida_cx), 
                                str(portas_str)
                            ]
                            
                            # SOLUÇÃO PARA NOVA LINHA: 
                            # 'INSERT_ROWS' força o Google a criar uma linha física nova
                            aba.append_row(
                                linha, 
                                value_input_option='USER_ENTERED',
                                insert_data_option='INSERT_ROWS'
                            )
                            
                            st.toast(f"Registrado com sucesso!", icon="✅")
                            st.balloons()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
