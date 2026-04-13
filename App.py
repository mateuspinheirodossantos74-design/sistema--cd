import streamlit as st
from modulos import (
    inicio,
    visao,
    tarefas,
    login,
    chatbot,
    gestao_usuarios,
    inserir_demanda
)
from modulos.style import aplicar_estilo


st.set_page_config(
    page_title="Sistema Logístico",
    page_icon="📦",
    layout="wide"
)

aplicar_estilo()

# ==========================
# SESSION STATE PADRÃO
# ==========================
if "logado" not in st.session_state:
    st.session_state.logado = False

if "nome_usuario" not in st.session_state:
    st.session_state.nome_usuario = ""

if "nivel" not in st.session_state:
    st.session_state.nivel = ""

if "trocar_senha_obrigatorio" not in st.session_state:
    st.session_state.trocar_senha_obrigatorio = False


# ==========================
# CONTROLE DE ACESSO
# ==========================
if st.session_state.trocar_senha_obrigatorio:
    login.render()
    st.stop()

if not st.session_state.logado:
    login.render()
    st.stop()


# ==========================
# SIDEBAR
# ==========================
with st.sidebar:

    st.markdown("## 📦 Sistema CD")
    st.markdown("---")

    st.markdown(f"👤 **{st.session_state.nome_usuario}**")
    st.markdown("---")

    st.markdown("### 🚀 Operação")

    # ==========================
    # MENU (MAPEAMENTO DE ROTAS)
    # ==========================
    menu = {
        "🏠 Início": inicio.render,
        "📝 Inserir Demanda": inserir_demanda.render,
        "📋 Visão Geral": visao.render,
        "📦 Tarefas": tarefas.render,
        "📊 Dashboard": lambda: st.info("Módulo em desenvolvimento..."),
        "📈 Produtividade": lambda: st.info("Módulo em desenvolvimento..."),
        "🤖 Chatbot": chatbot.render,
        "💡 Sugestões": lambda: st.info("Módulo em desenvolvimento..."),
        "📄 Relatórios": lambda: st.info("Módulo em desenvolvimento...")
    }

    # ADMIN
    if st.session_state.nivel == "admin":
        menu["👥 Gestão de Usuários"] = gestao_usuarios.render

    pagina = st.radio(
        "Navegação",
        list(menu.keys()),
        label_visibility="collapsed"
    )

    st.markdown("---")

    st.markdown("### ⚙️ Sistema")

    if st.button("🚪 Sair"):
        st.session_state.clear()
        st.rerun()


# ==========================
# SEGURANÇA EXTRA
# ==========================
if pagina == "👥 Gestão de Usuários" and st.session_state.nivel != "admin":
    st.error("Acesso não autorizado")
    st.stop()


# ==========================
# EXECUÇÃO DAS PÁGINAS
# ==========================
menu[pagina]()
