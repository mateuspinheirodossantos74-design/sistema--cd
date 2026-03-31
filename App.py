import streamlit as st
from modulos import inicio, visao, tarefas, login, chatbot, gestao_usuarios

st.set_page_config(
    page_title="Sistema Logístico",
    page_icon="📦",
    layout="wide"
)

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

# 🔒 PRIORIDADE: primeiro acesso (troca obrigatória)
if st.session_state.trocar_senha_obrigatorio:
    login.render()
    st.stop()

# 🔐 NÃO LOGADO
if not st.session_state.logado:
    login.render()
    st.stop()

# ==========================
# SIDEBAR (SISTEMA LIBERADO)
# ==========================
with st.sidebar:

    st.markdown("## 📌 Menu Principal")
    st.markdown(f"👤 **{st.session_state.nome_usuario}**")
    st.markdown("---")

    # MENU PADRÃO
    menu = [
        "🏠 Início",
        "📋 Visão Geral",
        "📦 Tarefas",
        "📊 Dashboard",
        "📈 Produtividade",
        "🤖 Chatbot",
        "💡 Sugestões",
        "Relatorios"
    ]

    # 🔐 SOMENTE ADMIN
    if st.session_state.nivel == "admin":
        menu.append("👥 Gestão de Usuários")

    pagina = st.radio("Navegação", menu)

    st.markdown("---")

    # 🚪 LOGOUT
    if st.button("🚪 Sair"):
        st.session_state.clear()
        st.rerun()

# ==========================
# SEGURANÇA EXTRA (ROTA)
# ==========================
if pagina == "👥 Gestão de Usuários" and st.session_state.nivel != "admin":
    st.error("Acesso não autorizado")
    st.stop()

# ==========================
# RENDERIZAÇÃO DAS PÁGINAS
# ==========================

if pagina == "🏠 Início":
    inicio.render()

elif pagina == "📋 Visão Geral":
    visao.render()

elif pagina == "📦 Tarefas":
    tarefas.render()

elif pagina == "📊 Dashboard":
    st.title("📊 Dashboard")
    st.info("Módulo em desenvolvimento...")

elif pagina == "📈 Produtividade":
    st.title("📈 Produtividade")
    st.info("Módulo em desenvolvimento...")

elif pagina == "🤖 Chatbot":
    chatbot.render()

elif pagina == "💡 Sugestões":
    st.title("💡 Sugestões")
    st.info("Módulo em desenvolvimento...")

elif pagina == "Relatorios":
    st.title("Relatorios")
    st.info("Módulo em desenvolvimento...")

elif pagina == "👥 Gestão de Usuários":
    gestao_usuarios.render()
