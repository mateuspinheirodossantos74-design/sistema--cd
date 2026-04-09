import streamlit as st
import pandas as pd
from modulos.conexao import conectar

# ==========================
# INSERIR DEMANDA
# ==========================
def inserir_demanda(wave, demanda):
    conn = conectar()
    cursor = conn.cursor()

    # Verifica se já existe
    cursor.execute("SELECT wave FROM demanda WHERE wave = %s", (wave,))
    existe = cursor.fetchone()

    if existe:
        conn.close()
        return False  # Já existe

    # Inserir nova
    cursor.execute(
        "INSERT INTO demanda (wave, demanda) VALUES (%s, %s)",
        (wave, demanda)
    )
    conn.commit()
    conn.close()
    return True


# ==========================
# CARREGAR DADOS
# ==========================
@st.cache_data(ttl=60)
def carregar_demandas():
    conn = conectar()
    df = pd.read_sql("SELECT wave, demanda FROM demanda ORDER BY wave", conn)
    conn.close()

    # Padronizar
    df["wave"] = df["wave"].astype(str).str.strip()

    return df


# ==========================
# RENDER
# ==========================
def render():

    st.title("📥 Inserir Demanda")

    # ==========================
    # FORMULÁRIO
    # ==========================
    st.subheader("Cadastrar nova demanda")

    col1, col2 = st.columns(2)

    with col1:
        wave_input = st.text_input("Wave")

    with col2:
        demanda_input = st.text_input("Demanda")

    if st.button("Salvar"):

        wave = wave_input.strip()
        demanda = demanda_input.strip()

        if not wave or not demanda:
            st.warning("Preencha todos os campos.")
        else:
            sucesso = inserir_demanda(wave, demanda)

            if sucesso:
                st.success("Demanda cadastrada com sucesso!")
                st.cache_data.clear()
                st.rerun()
            else:
                st.warning("⚠️ Wave já cadastrada na tabela demanda.")

    # ==========================
    # FILTRO
    # ==========================
    st.subheader("🔎 Consultar demandas")

    df = carregar_demandas()

    busca_wave = st.text_input("Buscar por Wave")

    if busca_wave:
        df = df[df["wave"].str.contains(busca_wave.strip(), case=False, na=False)]

    # ==========================
    # TABELA
    # ==========================
    st.dataframe(df, use_container_width=True)
