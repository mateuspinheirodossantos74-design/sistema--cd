import streamlit as st
import pandas as pd
from PIL import Image
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
from modulos.conexao import conectar
import os

IMAGE_PATH = r"C:\Users\2960007532\Documents\Automacao\2.png"


# ==========================
# CARREGAR DADOS
# ==========================
@st.cache_data(ttl=300)
def carregar_dados():

    conn = conectar()
    query = "SELECT * FROM base_operacional"
    df = pd.read_sql(query, conn)
    conn.close()

    # Converter data corretamente
    if "data_limite_expedicao" in df.columns:
        df["data_limite_expedicao"] = pd.to_datetime(
            df["data_limite_expedicao"], errors="coerce"
        )

    return df


# ==========================
# RENDER
# ==========================
def render():

    # ==========================
    # AUTO REFRESH
    # ==========================
    st_autorefresh(interval=600000, key="auto_refresh_visao")

    # ==========================
    # RELÓGIO
    # ==========================
    components.html(
        """
        <div id="clock" style="
            position: fixed;
            top: 18px;
            right: 22px;
            font-size: 34px;
            font-weight: 900;
            padding: 10px 18px;
            border-radius: 14px;
            background-color: rgba(0,0,0,0.25);
            color: white;
            z-index: 9999;
            font-family: Arial, sans-serif;
        ">--:--:--</div>

        <script>
            function updateClock() {
                const now = new Date();
                document.getElementById("clock").innerHTML =
                    now.toLocaleTimeString('pt-BR');
            }
            setInterval(updateClock, 1000);
            updateClock();
        </script>
        """,
        height=80
    )

    # ==========================
    # ESTILO
    # ==========================
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 0.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # ==========================
    # CARREGAR DADOS
    # ==========================
    df = carregar_dados()

    if df is None or df.empty:
        st.warning("⏳ Banco de dados indisponível ou sem dados.")
        st.stop()

    # ==========================
    # SIDEBAR
    # ==========================
    if st.sidebar.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.rerun()

    # ==========================
    # FILTRO SETOR
    # ==========================
    st.sidebar.subheader("Filtro por Setor")

    setores = df["setor"].dropna().unique().tolist()
    setores_sel = st.sidebar.multiselect("Setor:", setores, default=setores)

    df = df[df["setor"].isin(setores_sel)]

    if df.empty:
        st.warning("Nenhum dado para o setor selecionado.")
        st.stop()

    # ==========================
    # FILTRO DATA
    # ==========================
    data_min = df["data_limite_expedicao"].min()
    data_max = df["data_limite_expedicao"].max()

    datas = st.sidebar.date_input(
        "Data Limite Expedição:",
        value=(data_min, data_max),
        min_value=data_min,
        max_value=data_max
    )

    if isinstance(datas, tuple) and len(datas) == 2:
        data_inicio, data_fim = datas
    else:
        data_inicio = datas
        data_fim = datas

    df = df[
        (df["data_limite_expedicao"] >= pd.to_datetime(data_inicio)) &
        (df["data_limite_expedicao"] <= pd.to_datetime(data_fim))
    ]

    # ==========================
    # TOPO
    # ==========================
    col_l, col_c, col_r = st.columns([1.5, 3, 1.5])

    with col_l:
        if IMAGE_PATH and os.path.exists(IMAGE_PATH):
            st.image(Image.open(IMAGE_PATH), width=220)

        st.markdown(
            f"<p style='font-size:30px;font-weight:800;margin-top:60px;'>"
            f"Data Expedição: {data_inicio.strftime('%d/%m/%Y')}</p>",
            unsafe_allow_html=True
        )

    with col_c:
        st.markdown(
            "<h1 style='text-align:center;font-size:40px;font-weight:900;margin-top:120px;'>SALÃO</h1>",
            unsafe_allow_html=True
        )

    # ==========================
    # FILTROS SALÃO / P.A.R
    # ==========================
    demanda_lista = ["— Nenhuma seleção —"] + df["demanda"].dropna().unique().tolist()

    st.sidebar.subheader("Filtros — Salão")
    demanda_salao = st.sidebar.selectbox("Demanda Salão:", demanda_lista)

    st.sidebar.subheader("Filtros — P.A.R")
    demanda_par = st.sidebar.selectbox("Demanda (P.A.R):", demanda_lista)

    df_salao = (
        df[df["demanda"] == demanda_salao]
        if demanda_salao != "— Nenhuma seleção —"
        else df.iloc[0:0]
    )

    df_par = (
        df[df["demanda"] == demanda_par]
        if demanda_par != "— Nenhuma seleção —"
        else df.iloc[0:0]
    )

    # ==========================
    # CÁLCULOS
    # ==========================
    status_col = "status_olpn"
    qtd_col = "qtde_pecas_item"

    def resumo_status(dataframe):
        return dataframe.groupby(status_col)[qtd_col].sum()

    def fmt(v):
        return f"{int(v):,}".replace(",", ".")

    status_colors = {
        "Created": "red",
        "Packed": "gold",
        "Loaded": "green",
        "Shipped": "black"
    }

    def card(col, titulo, valor, cor, subtitle=None, size="medium"):
        sizes = {
            "small": ("22px", "52px", "6px"),
            "medium": ("30px", "72px", "14px"),
        }
        t, v, p = sizes[size]

        col.markdown(
            f"""
            <div style="background:white;padding:{p};
            border-radius:18px;text-align:center;
            box-shadow:0 6px 18px rgba(0,0,0,0.18);">
                <h3 style="font-size:{t};margin:0;">{titulo}</h3>
                <p style="font-size:{v};color:{cor};
                font-weight:800;margin:6px 0;">{fmt(valor)}</p>
                {f"<p style='font-size:22px;font-weight:600;'>{subtitle}</p>" if subtitle else ""}
            </div>
            """,
            unsafe_allow_html=True
        )

    # ==========================
    # CARDS SALÃO
    # ==========================
    res_salao = resumo_status(df_salao)
    cols = st.columns(5)

    for i, status in enumerate(status_colors):
        card(cols[i], status, res_salao.get(status, 0), status_colors[status])

    card(cols[4], "Total Geral", df_salao[qtd_col].sum(), "black")

    # ==========================
    # P.A.R
    # ==========================
    st.markdown("<h2 style='text-align:center;font-size:34px;font-weight:800;'>P.A.R</h2>", unsafe_allow_html=True)

    res_par = resumo_status(df_par)
    cols = st.columns(5)

    for i, status in enumerate(status_colors):
        card(cols[i], status, res_par.get(status, 0), status_colors[status])

    card(cols[4], "Total Geral", df_par[qtd_col].sum(), "black")

    # ==========================
    # AUDIT
    # ==========================
    st.markdown(
        "<h2 style='text-align:center;font-size:34px;font-weight:800;'>AUDIT</h2>",
        unsafe_allow_html=True
    )

    if df_salao.empty or "audit" not in df_salao.columns:
        st.info("Sem dados de AUDIT para a seleção atual.")
    else:
        df_audit = (
            df_salao
            .groupby("audit", dropna=False)[qtd_col]
            .sum()
            .reset_index()
        )

        total_audit = df_audit[qtd_col].sum()
        cols = st.columns(len(df_audit))

        for i, row in df_audit.iterrows():
            pct = (row[qtd_col] / total_audit * 100) if total_audit else 0

            card(
                cols[i],
                str(row["audit"]) if pd.notna(row["audit"]) else "Sem Audit",
                row[qtd_col],
                "blue",
                subtitle=f"{pct:.1f}%",
                size="small"
            )
