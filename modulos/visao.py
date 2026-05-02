import streamlit as st
import pandas as pd
from PIL import Image
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
from modulos.conexao import get_connection
import os

IMAGE_PATH = os.path.join("imagens", "2.png")


# ==========================
# CARREGAR DADOS
# ==========================
@st.cache_data(ttl=300)
def carregar_dados():

    try:
        df = pd.read_sql("""
            SELECT 
                box,
                wave,
                status_olpn,
                qtde_pecas_item,
                data_limite_expedicao,
                audit_status
            FROM base_operacional
        """, get_connection())

        df_setores = pd.read_sql("""
            SELECT DISTINCT box, setor 
            FROM mapa_box_setor
        """, get_connection())

        df_demandas = pd.read_sql("""
            SELECT DISTINCT wave, demanda 
            FROM demanda
        """, get_connection())

    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame(), pd.DataFrame()



    # ❌ NÃO FECHAR CONEXÃO (cache_resource)

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

    # ==========================
    # FILTROS
    # ==========================
    if st.sidebar.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.subheader("Filtro por Setor")

    df, df_demandas = carregar_dados()

    if df.empty:
        st.warning("⏳ Sem dados disponíveis.")
        st.stop()

    setores = sorted(df["setor"].dropna().unique().tolist()) if "setor" in df.columns else []
    setores_sel = st.sidebar.multiselect("Setor:", setores,)

    if not setores_sel:
        st.warning("selecione pelo menos um setor")
        st.stop()

    if "setor" in df.columns:
        df = df[df["setor"].fillna("SEM_SETOR").isin(setores_sel)]

    if df.empty:
        st.warning("Nenhum dado após filtro de setor.")
        st.stop()

    df = df.dropna(subset=["data_limite_expedicao"])

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
        st.markdown("<h1 style='text-align:center;margin-bottom:0;'>SALÃO</h1>", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:-10px'></div>", unsafe_allow_html=True)

    # ==========================
    # CARD
    # ==========================
    def fmt(v):
        return f"{int(v):,}".replace(",", ".")

    def card(col, titulo, valor, cor, subtitle=None, size="medium"):
        sizes = {
            "small": ("22px", "52px", "6px"),
            "medium": ("30px", "72px", "10px")
        }

        t, v, p = sizes[size]

        col.markdown(f"""
        <div style="background:white;padding:{p};
        border-radius:18px;text-align:center;
        box-shadow:0 6px 18px rgba(0,0,0,0.18);
        margin-top:-5px;">
            <h3 style="font-size:{t};margin:0;">{titulo}</h3>
            <p style="font-size:{v};color:{cor};font-weight:800;margin:4px 0;">
            {fmt(valor)}</p>
            {f"<p style='font-size:20px;font-weight:600;margin:0;'>{subtitle}</p>" if subtitle else ""}
        </div>
        """, unsafe_allow_html=True)

    # ==========================
    # SALÃO
    # ==========================
    def resumo(df_local):
        return df_local.groupby("status_olpn")["qtde_pecas_item"].sum()

    res_salao = resumo(df_salao)

    status_colors = {
        "Created": "red",
        "Packed": "gold",
        "Loaded": "green",
        "Shipped": "black"
    }

    st.markdown(f"""
        <div style="
            font-size:24px;
            font-weight:900;
            margin-bottom:0px;
            color:black;
            text-align:left;
        ">
            Período: {data_inicio.strftime('%d/%m/%Y')} → {data_fim.strftime('%d/%m/%Y')}
        </div>
    """, unsafe_allow_html=True)

    cols = st.columns(5)

    for i, status in enumerate(status_colors):
        card(cols[i], status, res_salao.get(status, 0), status_colors[status])

    card(cols[4], "Total Geral", df_salao["qtde_pecas_item"].sum(), "black")

    # ==========================
    # P.A.R
    # ==========================
    st.markdown("<div style='margin-top:-15px'></div>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center;margin-bottom:0;'>P.A.R</h1>", unsafe_allow_html=True)

    res_par = resumo(df_par)
    cols = st.columns(5)

    for i, status in enumerate(status_colors):
        card(cols[i], status, res_par.get(status, 0), status_colors[status])

    card(cols[4], "Total Geral", df_par["qtde_pecas_item"].sum(), "black")

    # ==========================
    # AUDIT
    # ==========================
    st.markdown("<div style='margin-top:-15px'></div>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center;margin-bottom:0;'>AUDIT</h1>", unsafe_allow_html=True)

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

    df_group = df_audit.groupby("status_audit_tratado")["qtde_pecas_item"].sum().reset_index()

    total = df_group["qtde_pecas_item"].sum()

    cols = st.columns(len(df_group))

    for i, row in df_group.iterrows():
        pct = (row["qtde_pecas_item"] / total * 100) if total else 0

        card(
            cols[i],
            row["status_audit_tratado"],
            row["qtde_pecas_item"],
            "blue",
            subtitle=f"{pct:.1f}%",
            size="small"
        )
