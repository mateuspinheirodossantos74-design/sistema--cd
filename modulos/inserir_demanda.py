import streamlit as st
import pandas as pd
import io
import re

from modulos.conexao import get_connection


# ==========================
# CONEXÃO DIRETA (ANTIGO PADRÃO)
# ==========================
def executar_query(query):
    conn = get_connection()
    try:
        conn.ping(reconnect=True, attempts=3, delay=2)
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Erro ao executar query: {e}")
        return pd.DataFrame()
    finally:
        try:
            conn.close()
        except:
            pass


# ==========================
# DEMANDA
# ==========================
def inserir_demanda(wave, demanda):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO demanda (wave, demanda)
            VALUES (%s, %s)
        """, (wave, demanda))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        st.error(f"Erro ao salvar demanda: {e}")
        return False


# ==========================
# CONFERENTE INSERIR
# ==========================
def inserir_conferente(box, conferente):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT box FROM conferentes WHERE box = %s
        """, (box,))

        if cursor.fetchone():
            return False

        cursor.execute("""
            INSERT INTO conferentes (box, conferente)
            VALUES (%s, %s)
        """, (box, conferente))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        st.error(f"Erro ao salvar conferente: {e}")
        return False


# ==========================
# ATUALIZAR CONFERENTE
# ==========================
def atualizar_conferente(box, conferente):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE conferentes
            SET conferente = %s
            WHERE box = %s
        """, (conferente, box))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        st.error(f"Erro ao atualizar conferente: {e}")
        return False


# ==========================
# CARREGAR DEMANDAS
# ==========================
@st.cache_data(ttl=60)
def carregar_demandas():
    query = """
    SELECT wave, demanda
    FROM demanda
    ORDER BY wave
    """

    df = executar_query(query)

    if not df.empty:
        df["wave"] = df["wave"].astype(str).str.strip()

    return df


# ==========================
# CARREGAR CONFERENTES
# ==========================
@st.cache_data(ttl=60)
def carregar_conferentes():
    query = """
    SELECT box, conferente
    FROM conferentes
    ORDER BY box
    """

    df = executar_query(query)

    if not df.empty:
        df["box"] = df["box"].astype(str).str.strip()
        df["conferente"] = df["conferente"].astype(str).str.strip()

    return df


# ==========================
# UPLOAD CONFERENTES
# ==========================
def upload_conferentes(df):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        for _, row in df.iterrows():
            box = row["box"]
            conferente = row["conferente"]

            cursor.execute("""
                SELECT box FROM conferentes WHERE box = %s
            """, (box,))

            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO conferentes (box, conferente)
                    VALUES (%s, %s)
                """, (box, conferente))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        st.error(f"Erro no upload: {e}")
        return False


# ==========================
# PROCESSAR TXT
# ==========================
def processar_txt(arquivo):
    try:
        conteudo = arquivo.read().decode("utf-8")
        linhas = conteudo.splitlines()

        dados = []

        for linha in linhas:
            linha = linha.strip()
            if not linha:
                continue

            linha = linha.replace("\t", " ")
            linha = " ".join(linha.split())

            if ";" in linha:
                partes = linha.split(";")
            else:
                partes = linha.split(" ", 1)

            if len(partes) >= 2:
                box = str(partes[0]).strip()
                conferente = str(partes[1]).strip()

                if box and conferente:
                    dados.append({
                        "box": box,
                        "conferente": conferente
                    })

        return pd.DataFrame(dados)

    except Exception as e:
        st.error(f"Erro ao processar TXT: {e}")
        return pd.DataFrame()


# ==========================
# RENDER
# ==========================
def render():

    st.title("📥 Cadastro Operacional")

    aba1, aba2 = st.tabs([
        "📊 Inserir Demanda",
        "👤 Conferentes"
    ])

    # ==========================
    # DEMANDA
    # ==========================
    with aba1:

        st.subheader("Cadastrar nova demanda")

        col1, col2 = st.columns(2)

        with col1:
            wave_input = st.text_input("Wave")

        with col2:
            demanda_input = st.text_input("Demanda")

        if st.button("Salvar Demanda"):

            if wave_input and demanda_input:
                if inserir_demanda(wave_input.strip(), demanda_input.strip()):
                    st.success("Demanda cadastrada!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.warning("Erro ao salvar ou já existe.")
            else:
                st.warning("Preencha todos os campos.")

        st.markdown("---")

        st.subheader("Consultar demandas")

        df_demanda = carregar_demandas()

        busca = st.text_input("Buscar Wave")

        if busca:
            df_demanda = df_demanda[
                df_demanda["wave"].str.contains(busca, na=False)
            ]

        st.dataframe(df_demanda, use_container_width=True)

    # ==========================
    # CONFERENTES
    # ==========================
    with aba2:

        st.subheader("Cadastrar conferente")

        col1, col2 = st.columns(2)

        with col1:
            box_input = st.text_input("Box")

        with col2:
            conf_input = st.text_input("Conferente")

        if st.button("Salvar Conferente"):

            if box_input and conf_input:

                if inserir_conferente(box_input.strip(), conf_input.strip()):
                    st.success("Conferente cadastrado!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.warning("Box já existe.")
            else:
                st.warning("Preencha todos os campos.")

        st.markdown("---")

        st.subheader("Upload TXT")

        arquivo = st.file_uploader("Arquivo TXT", type=["txt"])

        if arquivo:

            df_upload = processar_txt(arquivo)

            if not df_upload.empty:

                st.dataframe(df_upload, use_container_width=True)

                if st.button("Salvar Upload"):

                    if upload_conferentes(df_upload):
                        st.success("Upload realizado!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Erro no upload")

        st.markdown("---")

        st.subheader("Editar conferentes")

        busca_box = st.text_input("Buscar Box")

        if busca_box:

            df_conf = carregar_conferentes()

            df_conf = df_conf[
                df_conf["box"].str.contains(busca_box, na=False)
            ]

            for i, row in df_conf.iterrows():

                col1, col2, col3 = st.columns([1, 3, 1])

                with col1:
                    st.text(row["box"])

                with col2:
                    novo = st.text_input(
                        f"conf_{i}",
                        value=row["conferente"]
                    )

                with col3:
                    if st.button("Salvar", key=f"s_{i}"):

                        if atualizar_conferente(row["box"], novo):
                            st.success("Atualizado!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("Erro ao atualizar")
