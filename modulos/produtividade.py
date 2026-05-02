import streamlit as st


# ==========================
# ABA: PASSAGEM DE BOX
# ==========================
def aba_passagem_box():
    st.subheader("📦 Produtividade - Passagem de Box")

    st.info("Em construção...")

    # 👉 aqui depois entra:
    # filtros
    # métricas
    # gráficos


# ==========================
# ABA: PICKING
# ==========================
def aba_picking():
    st.subheader("🛒 Produtividade - Picking")

    st.info("Em construção...")

    # 👉 aqui depois entra:
    # filtros
    # ranking
    # produtividade por operador


# ==========================
# ABA: CONFERÊNCIA
# ==========================
def aba_conferencia():
    st.subheader("✔ Produtividade - Conferência")

    st.info("Em construção...")

    # 👉 aqui depois entra:
    # produtividade por conferente
    # volume conferido
    # desempenho


# ==========================
# RENDER PRINCIPAL
# ==========================
def render():
    st.title("📊 Produtividade Operacional")

    abas = st.tabs([
        "📦 Passagem de Box",
        "🛒 Picking",
        "✔ Conferência"
    ])

    with abas[0]:
        aba_passagem_box()

    with abas[1]:
        aba_picking()

    with abas[2]:
        aba_conferencia()
