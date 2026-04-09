import streamlit as st
import pandas as pd
from PIL import Image
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
from modulos.conexao import conectar
import os

IMAGE_PATH = os.path.join("imagens", "2.png")

# ==========================
# CARREGAR DADOS
# ==========================
@st.cache_data(ttl=300)
def carregar_dados():

    conn = conectar()

    # Base principal
    df = pd.read_sql("SELECT * FROM base_operacional", conn)

    # Tabelas auxiliares
    df_setores = pd.read_sql("SELECT DISTINCT box, setor FROM mapa_box_setor", conn)
    df_demandas = pd.read_sql("SELECT DISTINCT wave, demanda FROM demanda", conn)

    conn.close()

    # Padronizar tipos
    df["box"] = df["box"].astype(str).str.strip()
    df_setores["box"] = df_setores["box"].astype(str).str.strip()

    df["wave"] = df["wave"].astype(str).str.strip()
    df_demandas["wave"] = df_demandas["wave"].astype(str).str.strip()

    # MERGES
    df = df.merge(df_setores, on="box", how="left")
    df = df.merge(df_demandas, on="wave", how="left")

    # Datas
    if "data_limite_expedicao" in df.columns:
        df["data_limite_expedicao"] = pd.to_datetime(
            df["data_limite_expedicao"], errors="coerce"
        )

    return df


# ==========================
# RENDER
# ==========================
def render():

    st_autorefresh(interval=600000, key="auto_refresh_visao")

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

    df = carregar_dados()

    if df is None or df.empty:
        st.warning("⏳ Banco de dados indisponível ou sem dados.")
        st.stop()

    if st.sidebar.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.rerun()

    # ==========================
    # FILTRO SETOR
    # ==========================
    st.sidebar.subheader("Filtro por Setor")

    setores = sorted(df["setor"].dropna().unique().tolist())
    setores_sel = st.sidebar.multiselect("Setor:", setores, default=setores)

    df = df[df["setor"].isin(setores_sel)]

    if df.empty:
        st.warning("Nenhum dado para o setor selecionado.")
        st.stop()

    # ==========================
    # FILTRO DATA
    # ==========================
    df = df.dropna(subset=["data_limite_expedicao"])

    data_min = df["data_limite_expedicao"].min().date()
    data_max = df["data_limite_expedicao"].max().date()

    datas = st.sidebar.date_input(
        "Data Limite Expedição:",
        value=(data_min, data_max),
        min_value=data_min,
        max_value=data_max
    )

    if isinstance(datas, (list, tuple)):
        data_inicio = datas[0]
        data_fim = datas[-1]
    else:
        data_inicio = datas
        data_fim = datas

    data_inicio = pd.to_datetime(data_inicio)
    data_fim = pd.to_datetime(data_fim)

    df = df[
        (df["data_limite_expedicao"] >= data_inicio) &
        (df["data_limite_expedicao"] <= data_fim)
    ]

    # ==========================
    # TOPO
    # ==========================
    col_l, col_c, col_r = st.columns([1.5, 3, 1.5])

    with col_l:
        if os.path.exists(IMAGE_PATH):
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
    # FILTRO DEMANDA
    # ==========================
    demanda_lista = ["— Nenhuma seleção —"] + sorted(df["demanda"].dropna().unique().tolist())

    st.sidebar.subheader("Filtros — Salão")
    demanda_salao = st.sidebar.selectbox("Demanda Salão:", demanda_lista)

    st.sidebar.subheader("Filtros — P.A.R")
    demanda_par = st.sidebar.selectbox("Demanda (P.A.R):", demanda_lista)

    df_salao = df[df["demanda"] == demanda_salao] if demanda_salao != "— Nenhuma seleção —" else df.iloc[0:0]
    df_par = df[df["demanda"] == demanda_par] if demanda_par != "— Nenhuma seleção —" else df.iloc[0:0]

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
    st.markdown("<h2 style='text-align:center;font-size:34px;font-weight:800;'>AUDIT</h2>", unsafe_allow_html=True)

    if df_salao.empty or "audit_status" not in df_salao.columns:
        st.info("Sem dados de AUDIT.")
    else:
        df_salao = df_salao.copy()

        df_salao["status_audit_tratado"] = (
            df_salao["audit_status"]
            .astype(str)
            .str.strip()
            .str.upper()
            .replace({
                "": "AUDIT INCOMPLETO",
                "NONE": "AUDIT INCOMPLETO",
                "NAN": "AUDIT INCOMPLETO",
                "AUDIT_COMPLETE": "AUDIT COMPLETO",
                "AUDIT_COMPLETE_WITH_VARIANCE": "AUDIT INCOMPLETO"
            })
        )

        df_salao["status_audit_tratado"] = df_salao["status_audit_tratado"].fillna("AUDIT INCOMPLETO")

        df_audit = df_salao.groupby("status_audit_tratado")[qtd_col].sum().reset_index()
        total = df_audit[qtd_col].sum()

        cols = st.columns(len(df_audit))

        for i, row in df_audit.iterrows():
            pct = (row[qtd_col] / total * 100) if total else 0

            card(
                cols[i],
                str(row["status_audit_tratado"]),
                row[qtd_col],
                "blue",
                subtitle=f"{pct:.1f}%",
                size="small"
            )
