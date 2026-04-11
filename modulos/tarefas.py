import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh
from modulos.conexao import get_connection


# ==========================
# CONEXÃO SEGURA
# ==========================
def executar_query(query):
    conn = get_connection()
    try:
        conn.ping(reconnect=True, attempts=3, delay=2)
        return pd.read_sql(query, conn)
    except Exception as e:
        st.error(f"Erro ao executar query: {e}")
        return pd.DataFrame()
    finally:
        try:
            conn.close()
        except:
            pass

# ==========================
# FILTROS
# ==========================
def montar_where(filtros):
    where = []

    if filtros.get("wave"):
        waves = ",".join([f"'{w}'" for w in filtros["wave"] if w])
        if waves:
            where.append(f"bo.wave IN ({waves})")

    if filtros.get("setor"):
        setores = ",".join([f"'{v}'" for v in filtros["setor"] if v])
        if setores:
            where.append(f"ms.setor IN ({setores})")

    if filtros.get("demanda"):
        demandas = ",".join([f"'{v}'" for v in filtros["demanda"] if v])
        if demandas:
            where.append(f"d.demanda IN ({demandas})")

    return " AND ".join(where)


# ==========================
# BASE JOIN
# ==========================
BASE_FROM = """
FROM base_operacional bo
LEFT JOIN mapa_box_setor ms ON bo.box = ms.box
LEFT JOIN demanda d ON bo.wave = d.wave
"""


# ==========================
# GRUPOS
# ==========================
def get_grupos(where_sql=""):
    query = f"""
    SELECT
        bo.grupo_tarefa,
        COUNT(DISTINCT bo.tarefa) AS qtde_tarefas,
        SUM(bo.qtde_pecas_item) AS qtde_pecas_pendentes,
        COUNT(DISTINCT bo.local_picking) AS qtde_locais
    {BASE_FROM}
    WHERE bo.status_olpn = 'Created'
    """

    if where_sql:
        query += " AND " + where_sql

    query += """
    GROUP BY bo.grupo_tarefa
    ORDER BY qtde_pecas_pendentes DESC
    """

    return executar_query(query)


# ==========================
# 🔥 DETALHAMENTO (VOLTOU COMO ERA)
# ==========================
def get_detalhamento(grupo, where_sql=""):
    query = f"""
    SELECT
        bo.tarefa,
        bo.local_picking,
        COUNT(*) AS qtde_linhas,
        SUM(bo.qtde_pecas_item) AS qtde_pecas,
        bo.status_olpn
    {BASE_FROM}
    WHERE bo.status_olpn = 'Created'
    AND bo.grupo_tarefa = '{grupo}'
    """

    if where_sql:
        query += " AND " + where_sql

    query += """
    GROUP BY bo.tarefa, bo.local_picking, bo.status_olpn
    ORDER BY qtde_pecas DESC
    """

    return executar_query(query)


# ==========================
# MÉTRICAS
# ==========================
def get_metricas(where_sql=""):
    query = f"""
    SELECT
        SUM(CASE WHEN bo.status_olpn = 'Created' THEN bo.qtde_pecas_item ELSE 0 END) AS created,
        SUM(CASE WHEN bo.status_olpn = 'Packed' THEN bo.qtde_pecas_item ELSE 0 END) AS packed,
        SUM(bo.qtde_pecas_item) AS total
    {BASE_FROM}
    """

    if where_sql:
        query += " WHERE " + where_sql

    df = executar_query(query)

    return df.iloc[0].to_dict() if not df.empty else {"created": 0, "packed": 0, "total": 0}


# ==========================
# PEÇAS
# ==========================
def get_pecas(where_sql=""):
    query = f"""
    SELECT
        bo.grupo_tarefa,
        SUM(bo.qtde_pecas_item) AS qtde_pecas_separadas
    {BASE_FROM}
    WHERE bo.status_olpn = 'Packed'
    """

    if where_sql:
        query += " AND " + where_sql

    query += """
    GROUP BY bo.grupo_tarefa
    ORDER BY qtde_pecas_separadas DESC
    """

    return executar_query(query)


# ==========================
# RENDER
# ==========================
def render():
    st_autorefresh(interval=600000, key="auto_refresh")

    st.title("📋 Acompanhamento de Tarefas")

    # filtros simples
    st.sidebar.header("🔎 Filtros")

    filtros = {
        "wave": st.sidebar.text_input("Wave (ex: 123,456)").split(","),
        "setor": st.sidebar.multiselect("Setor", []),
        "demanda": st.sidebar.multiselect("Demanda", [])
    }

    filtros["wave"] = [w.strip() for w in filtros["wave"] if w.strip()]

    where_sql = montar_where(filtros)

    # abas
    aba1, aba2 = st.tabs(["🏠 Início", "📦 Peças"])

    # INÍCIO
    with aba1:
        df = get_grupos(where_sql)
        st.dataframe(df, use_container_width=True)

        if not df.empty:
            grupo = st.selectbox("Grupo", df["grupo_tarefa"])
            df_det = get_detalhamento(grupo, where_sql)
            st.dataframe(df_det, use_container_width=True)

    # PEÇAS
    with aba2:
        m = get_metricas(where_sql)

        col1, col2, col3 = st.columns(3)
        col1.metric("Created", int(m["created"] or 0))
        col2.metric("Packed", int(m["packed"] or 0))
        col3.metric("Total", int(m["total"] or 0))

        st.dataframe(get_pecas(where_sql), use_container_width=True)
