import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh
from modulos.conexao import conectar


# ==========================
# BUILD FILTROS SQL
# ==========================
def montar_where(filtros):
    where = []

    if filtros["wave"]:
        waves = ",".join([f"'{w}'" for w in filtros["wave"]])
        where.append(f"wave IN ({waves})")

    if filtros["setor"]:
        valores = ",".join([f"'{v}'" for v in filtros["setor"]])
        where.append(f"setor IN ({valores})")

    if filtros["departamento"]:
        valores = ",".join([f"'{v}'" for v in filtros["departamento"]])
        where.append(f"departamento IN ({valores})")

    if filtros["demanda"]:
        valores = ",".join([f"'{v}'" for v in filtros["demanda"]])
        where.append(f"demanda IN ({valores})")

    return " AND ".join(where)


# ==========================
# QUERIES OTIMIZADAS
# ==========================
@st.cache_data(ttl=60)
def get_grupos(where_sql=""):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    query = f"""
    SELECT
        grupo_tarefa,
        COUNT(DISTINCT tarefa) as qtde_tarefas,
        SUM(qtde_pecas_item) as qtde_pecas_pendentes,
        COUNT(DISTINCT local_picking) as qtde_locais
    FROM base_operacional
    WHERE status_olpn = 'Created'
    {f"AND {where_sql}" if where_sql else ""}
    GROUP BY grupo_tarefa
    ORDER BY qtde_pecas_pendentes DESC
    """

    cursor.execute(query)
    df = pd.DataFrame(cursor.fetchall())
    conn.close()
    return df


@st.cache_data(ttl=60)
def get_detalhamento(grupo, where_sql=""):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    query = f"""
    SELECT
        tarefa,
        COUNT(DISTINCT local_picking) as qtde_locais,
        SUM(qtde_pecas_item) as qtde_pecas,
        status_olpn
    FROM base_operacional
    WHERE status_olpn = 'Created'
    AND grupo_tarefa = '{grupo}'
    {f"AND {where_sql}" if where_sql else ""}
    GROUP BY tarefa, status_olpn
    ORDER BY qtde_pecas DESC
    """

    cursor.execute(query)
    df = pd.DataFrame(cursor.fetchall())
    conn.close()
    return df


@st.cache_data(ttl=60)
def get_metricas(where_sql=""):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    query = f"""
    SELECT
        SUM(CASE WHEN status_olpn = 'Created' THEN qtde_pecas_item ELSE 0 END) as created,
        SUM(CASE WHEN status_olpn = 'Packed' THEN qtde_pecas_item ELSE 0 END) as packed,
        SUM(qtde_pecas_item) as total
    FROM base_operacional
    {f"WHERE {where_sql}" if where_sql else ""}
    """

    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    return result


@st.cache_data(ttl=60)
def get_pecas(where_sql=""):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    query = f"""
    SELECT
        grupo_tarefa,
        SUM(qtde_pecas_item) as qtde_pecas_separadas
    FROM base_operacional
    WHERE status_olpn = 'Packed'
    {f"AND {where_sql}" if where_sql else ""}
    GROUP BY grupo_tarefa
    ORDER BY qtde_pecas_separadas DESC
    """

    cursor.execute(query)
    df = pd.DataFrame(cursor.fetchall())
    conn.close()
    return df


@st.cache_data(ttl=60)
def get_departamento(where_sql=""):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    query = f"""
    SELECT
        departamento,
        SUM(qtde_pecas_item) as total,
        SUM(CASE WHEN status_olpn = 'Packed' THEN qtde_pecas_item ELSE 0 END) as packed
    FROM base_operacional
    {f"WHERE {where_sql}" if where_sql else ""}
    GROUP BY departamento
    ORDER BY total DESC
    """

    cursor.execute(query)
    df = pd.DataFrame(cursor.fetchall())
    conn.close()

    df["created"] = df["total"] - df["packed"]
    df["%_completo"] = (df["packed"] / df["total"] * 100).round(1)

    return df


# ==========================
# RENDER
# ==========================
def render():
    st_autorefresh(interval=600000, key="auto_refresh")

    st.title("📋 Acompanhamento de Tarefas")

    # ==========================
    # FILTROS
    # ==========================
    st.sidebar.header("🔎 Filtros")

    filtros = {
        "wave": st.sidebar.text_input("Wave (ex: 123,456)").split(","),
        "setor": st.sidebar.multiselect("Setor", []),
        "departamento": st.sidebar.multiselect("Departamento", []),
        "demanda": st.sidebar.multiselect("Demanda", [])
    }

    filtros["wave"] = [w.strip() for w in filtros["wave"] if w.strip()]

    where_sql = montar_where(filtros)

    # ==========================
    # ABAS
    # ==========================
    aba1, aba2, aba3 = st.tabs(["🏠 Início", "📦 Peças", "🏢 Departamento"])

    # ==========================
    # INICIO
    # ==========================
    with aba1:
        df = get_grupos(where_sql)

        st.dataframe(df, use_container_width=True)

        if not df.empty:
            grupo = st.selectbox("Grupo", df["grupo_tarefa"])
            df_det = get_detalhamento(grupo, where_sql)
            st.dataframe(df_det, use_container_width=True)

    # ==========================
    # PEÇAS
    # ==========================
    with aba2:
        m = get_metricas(where_sql)

        col1, col2, col3 = st.columns(3)
        col1.metric("Created", int(m["created"] or 0))
        col2.metric("Packed", int(m["packed"] or 0))
        col3.metric("Total", int(m["total"] or 0))

        df = get_pecas(where_sql)
        st.dataframe(df, use_container_width=True)

    # ==========================
    # DEPARTAMENTO
    # ==========================
    with aba3:
        df = get_departamento(where_sql)

        m = get_metricas(where_sql)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total", int(m["total"] or 0))
        col2.metric("Packed", int(m["packed"] or 0))
        col3.metric("%", round((m["packed"] / m["total"] * 100), 1) if m["total"] else 0)

        st.dataframe(df, use_container_width=True)
