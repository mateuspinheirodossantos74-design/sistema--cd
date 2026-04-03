import streamlit as st
from datetime import datetime


def render():

    st.title("🚀 Sistema de apoio Logístico")

    st.markdown("""
    Bem-vindo ao sistema de gestão logística.

    Este sistema foi desenvolvido para:

    - 📦 Acompanhar tarefas operacionais  
    - 📊 Monitorar produtividade  
    - 📊 Dashboards operacionais          
    - 🏢 Controlar demandas por setor  
    - ⏱️ Registrar ponto de colaboradores  
    - 🤖  Oferecer suporte via chatbot           
    - 💡 Receber sugestões de melhoria  

    Nosso objetivo é centralizar todas as informações operacionais em um único ambiente.
    """)

    st.divider()

    # ==========================
    # PROGRESSO DO SISTEMA
    # ==========================
    st.subheader("📈 Progresso do Sistema")

    progresso = 60  # altere conforme for evoluindo

    st.progress(progresso / 100)
    st.write(f"### {progresso}% concluído")

    st.divider()

    # ==========================
    # MÓDULOS
    # ==========================
    st.subheader("🧩 Módulos do Sistema")

    st.markdown("""
    - ✔️ Início  
    - ✔️ Visão Geral  
    - ✔️ Tarefas  
    - 🔄 Relatorio
    - 🔄 Dashboard  
    - 🔄 Produtividade  
    - ✔️ Registro de Ponto  
    - ✔️ Chatbot  
    - 🔄 Sugestões  
    """)

    st.divider()

    # ==========================
    # RODAPÉ PROFISSIONAL
    # ==========================
    ano_atual = datetime.now().year

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown(f"""
        ### 👨‍💻 Desenvolvido por  
        **Mateus Pinheiro**  
        Grupo Casas Bahia  

        Sistema interno de apoio operacional.
        """)

    with col2:
        st.success("Versão 0.2")

    st.markdown(f"""
    ---
    © {ano_atual} Mateus Pinheiro - Grupo Casas Bahia  
    Todos os direitos reservados.
    """)
