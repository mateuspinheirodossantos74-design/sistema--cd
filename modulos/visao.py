import streamlit as st
import pandas as pd
from PIL import Image
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
from modulos.conexao import conectar
import os

IMAGE_PATH = os.path.join("imagens", "2.png")


# ==========================
# CARREGAR DADOS (BLINDADO)
# ==========================
@st.cache_data(ttl=300)
def carregar_dados():

    conn = conectar()

    df = pd.read_sql("SELECT * FROM base_operacional", conn)
    df_setores = pd.read_sql("SELECT DISTINCT box, setor FROM mapa_box_setor", conn)
    df_demandas = pd.read_sql("SELECT DISTINCT wave, demanda FROM demanda", conn)

    conn.close()

    for col in ["box", "wave"]:
        if col not in df.columns:
            df[col] = None

    df["box"] = df["box"].astype(str).str.strip().str.upper()
    df["wave"] = df["wave"].astype(str).str.strip().str.upper()

    if not df_setores.empty:
        df_setores["box"] = df_setores["box"].astype(str).str.strip().str.upper()
        df = df.merge(df_setores, on="box", how="left")
    else:
        df["setor"] = None

    if not df_demandas.empty:
        df_demandas["wave"] = df_demandas["wave"].astype(str).str.strip().str.upper()
        df = df.merge(df_demandas, on="wave", how="left")
    else:
        df["demanda"] = None

    if "data_limite_expedicao" in df.columns:
        df["data_limite_expedicao"] = pd.to_datetime(df["data_limite_expedicao"], errors="coerce")

    return df, df_demandas


# ==========================
# RENDER
# ==========================
def render():

    st_autorefresh(interval=600000, key="auto_refresh_visao")

    components.html("""
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
    """, height=80)

    df, df_demandas = carregar_dados()

    if df.empty:
        st.warning("⏳ Sem dados disponíveis.")
        st.stop()

    if st.sidebar.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.rerun()

    # ==========================
    # FILTRO SETOR
    # ==========================
    st.sidebar.subheader("Filtro por Setor")

    setores = sorted(df["setor"].dropna().unique().tolist()) if "setor" in df.columns else []
    setores_sel = st.sidebar.multiselect("Setor:", setores, default=setores)

    if setores_sel and "setor" in df.columns:
        df = df[df["setor"].fillna("SEM_SETOR").isin(setores_sel)]

    if df.empty:
        st.warning("Nenhum dado após filtro de setor.")
        st.stop()

    # ==========================
    # FILTRO DATA
    # ==========================
    df = df.dropna(subset=["data_limite_expedicao"])

    if df.empty:
        st.warning("Sem datas válidas.")
        st.stop()

    data_min = df["data_limite_expedicao"].min().date()
    data_max = df["data_limite_expedicao"].max().date()

    datas = st.sidebar.date_input(
        "Data Limite Expedição:",
        value=(data_min, data_max),
        min_value=data_min,
        max_value=data_max
    )

    data_inicio, data_fim = datas if isinstance(datas, (list, tuple)) else (datas, datas)

    data_inicio = pd.to_datetime(data_inicio)
    data_fim = pd.to_datetime(data_fim)

    df = df[
        (df["data_limite_expedicao"] >= data_inicio) &
        (df["data_limite_expedicao"] <= data_fim)
    ]

    if df.empty:
        st.warning("Nenhum dado após filtro de data.")
        st.stop()

    # ==========================
    # DEMANDA
    # ==========================
    demanda_lista = ["— Nenhuma seleção —"] + sorted(
        df_demandas["demanda"].dropna().unique().tolist()
    ) if "demanda" in df_demandas.columns else ["— Nenhuma seleção —"]

    st.sidebar.subheader("Filtros — Salão")
    demanda_salao = st.sidebar.selectbox("Demanda Salão:", demanda_lista)

    st.sidebar.subheader("Filtros — P.A.R")
    demanda_par = st.sidebar.selectbox("Demanda (P.A.R):", demanda_lista)

    df_salao = df[df["demanda"] == demanda_salao] if demanda_salao != "— Nenhuma seleção —" else df.iloc[0:0]
    df_par = df[df["demanda"] == demanda_par] if demanda_par != "— Nenhuma seleção —" else df.iloc[0:0]

    # ==========================
    # TOPO
    # ==========================
    col_l, col_c, col_r = st.columns([1.5, 3, 1.5])

    with col_l:
        if os.path.exists(IMAGE_PATH):
            st.image(Image.open(IMAGE_PATH), width=220)

    with col_c:
        st.subheader("📦 SALÃO")

    st.divider()

    # ==========================
    # FUNÇÕES
    # ==========================
    status_col = "status_olpn"
    qtd_col = "qtde_pecas_item"

    def fmt(v):
        return f"{int(v):,}".replace(",", ".")

    # 🔥 CARD (AGORA COM TÍTULO CENTRALIZADO)
    def card(col, titulo, valor, cor, subtitle=None, size="medium"):
        sizes = {
            "small": ("22px", "52px", "6px"),
            "medium": ("30px", "72px", "14px")
        }

        t, v, p = sizes[size]

        col.markdown(f"""
        <div style="background:white;padding:{p};
        border-radius:18px;text-align:center;
        box-shadow:0 6px 18px rgba(0,0,0,0.18);">

            <h3 style="
                font-size:{t};
                margin:0;
                text-align:center;
                width:100%;
                font-weight:800;
            ">{titulo}</h3>

            <p style="font-size:{v};color:{cor};
            font-weight:800;margin:6px 0;">
            {fmt(valor)}</p>

            {f"<p style='font-size:22px;font-weight:600;'>{subtitle}</p>" if subtitle else ""}
        </div>
        """, unsafe_allow_html=True)

    # ==========================
    # SALÃO
    # ==========================
    def resumo(df_local):
        return df_local.groupby(status_col)[qtd_col].sum()

    res_salao = resumo(df_salao)
    cols = st.columns(5)

    status_colors = {
        "Created": "red",
        "Packed": "gold",
        "Loaded": "green",
        "Shipped": "black"
    }

    for i, status in enumerate(status_colors):
        card(cols[i], status, res_salao.get(status, 0), status_colors[status])

    card(cols[4], "Total Geral", df_salao[qtd_col].sum(), "black")

    # ==========================
    # P.A.R
    # ==========================
    st.subheader("📦 P.A.R")
    st.divider()

    res_par = resumo(df_par)
    cols = st.columns(5)

    for i, status in enumerate(status_colors):
        card(cols[i], status, res_par.get(status, 0), status_colors[status])

    card(cols[4], "Total Geral", df_par[qtd_col].sum(), "black")

    # ==========================
    # AUDIT
    # ==========================
    st.subheader("📊 AUDIT")
    st.divider()

    if df_salao.empty or "audit_status" not in df_salao.columns:
        st.info("Sem dados de AUDIT.")
        return

    df_audit = df_salao.copy()

    df_audit["status_audit_tratado"] = (
        df_audit["audit_status"]
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
        .fillna("AUDIT INCOMPLETO")
    )

    df_group = df_audit.groupby("status_audit_tratado")[qtd_col].sum().reset_index()

    total = df_group[qtd_col].sum()

    cols = st.columns(len(df_group))

    for i, row in df_group.iterrows():
        pct = (row[qtd_col] / total * 100) if total else 0

        card(
            cols[i],
            row["status_audit_tratado"],
            row[qtd_col],
            "blue",
            subtitle=f"{pct:.1f}%",
            size="small"
        )
