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

    try:
        conn = conectar()

        df = pd.read_sql("SELECT * FROM base_operacional", conn)
        df_setores = pd.read_sql("SELECT DISTINCT box, setor FROM mapa_box_setor", conn)
        df_demandas = pd.read_sql("SELECT DISTINCT wave, demanda FROM demanda", conn)

        conn.close()

    except Exception as e:
        st.error(f"Erro ao conectar no banco: {e}")
        return pd.DataFrame()

    # ==========================
    # NORMALIZAÇÃO SEGURA
    # ==========================
    for col in ["box"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    for col in ["box"]:
        if col in df_setores.columns:
            df_setores[col] = df_setores[col].astype(str).str.strip()

    for col in ["wave"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    for col in ["wave"]:
        if col in df_demandas.columns:
            df_demandas[col] = df_demandas[col].astype(str).str.strip()

    # ==========================
    # MERGE SEGURO
    # ==========================
    if not df_setores.empty:
        df = df.merge(df_setores, on="box", how="left")

    if not df_demandas.empty:
        df = df.merge(df_demandas, on="wave", how="left")

    # ==========================
    # GARANTIA DE COLUNAS (SEM QUEBRAR)
    # ==========================
    if "setor" not in df.columns:
        df["setor"] = "SEM_SETOR"

    if "demanda" not in df.columns:
        df["demanda"] = "SEM_DEMANDA"

    # ==========================
    # DATAS SEGURAS
    # ==========================
    if "data_limite_expedicao" in df.columns:
        df["data_limite_expedicao"] = pd.to_datetime(
            df["data_limite_expedicao"],
            errors="coerce"
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

    # ==========================
    # PROTEÇÃO BASE
    # ==========================
    if df is None or df.empty:
        st.warning("⏳ Banco de dados indisponível ou vazio.")
        st.stop()

    if st.sidebar.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.rerun()

    # ==========================
    # FILTRO SETOR (SEGURO)
    # ==========================
    st.sidebar.subheader("Filtro por Setor")

    setores = sorted(df["setor"].dropna().unique().tolist()) if "setor" in df.columns else []
    setores_sel = st.sidebar.multiselect("Setor:", setores, default=setores)

    if setores_sel:
        df = df[df["setor"].isin(setores_sel)]

    if df.empty:
        st.warning("Nenhum dado após filtro de setor.")
        st.stop()

    # ==========================
    # FILTRO DATA (SEGURO)
    # ==========================
    df = df.dropna(subset=["data_limite_expedicao"]) if "data_limite_expedicao" in df.columns else df

    if not df.empty and "data_limite_expedicao" in df.columns:

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
            data_inicio = data_fim = datas

        data_inicio = pd.to_datetime(data_inicio)
        data_fim = pd.to_datetime(data_fim)

        df = df[
            (df["data_limite_expedicao"] >= data_inicio) &
            (df["data_limite_expedicao"] <= data_fim)
        ]

    # ==========================
    # BASE SEGURA (NÃO ALTERA LÓGICA)
    # ==========================
    base_df = df.copy()

    # ==========================
    # DEMANDAS (SEM MUDAR LÓGICA)
    # ==========================
    st.sidebar.subheader("Filtros — Salão")
    st.sidebar.subheader("Filtros — P.A.R")

    demanda_lista = ["— Nenhuma seleção —"] + sorted(base_df["demanda"].dropna().unique().tolist()) if "demanda" in base_df.columns else ["— Nenhuma seleção —"]

    demanda_salao = st.sidebar.selectbox("Demanda Salão:", demanda_lista)
    demanda_par = st.sidebar.selectbox("Demanda (P.A.R):", demanda_lista)

    if demanda_salao != "— Nenhuma seleção —":
        df_salao = base_df[base_df["demanda"] == demanda_salao]
    else:
        df_salao = base_df.copy()

    if demanda_par != "— Nenhuma seleção —":
        df_par = base_df[base_df["demanda"] == demanda_par]
    else:
        df_par = base_df.copy()

    # ==========================
    # PROTEÇÃO FINAL DF
    # ==========================
    def safe_sum(df, col):
        return df[col].sum() if col in df.columns else 0

    status_col = "status_olpn"
    qtd_col = "qtde_pecas_item"

    def resumo_status(dataframe):
        if status_col not in dataframe.columns or qtd_col not in dataframe.columns:
            return pd.Series(dtype="int64")
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
    # SALÃO
    # ==========================
    res_salao = resumo_status(df_salao)
    cols = st.columns(5)

    for i, status in enumerate(status_colors):
        card(cols[i], status, res_salao.get(status, 0), status_colors[status])

    card(cols[4], "Total Geral", safe_sum(df_salao, qtd_col), "black")

    # ==========================
    # P.A.R
    # ==========================
    st.markdown("<h2 style='text-align:center;font-size:34px;font-weight:800;'>P.A.R</h2>", unsafe_allow_html=True)

    res_par = resumo_status(df_par)
    cols = st.columns(5)

    for i, status in enumerate(status_colors):
        card(cols[i], status, res_par.get(status, 0), status_colors[status])

    card(cols[4], "Total Geral", safe_sum(df_par, qtd_col), "black")

    # ==========================
    # AUDIT (BLINDADO)
    # ==========================
    st.markdown("<h2 style='text-align:center;font-size:34px;font-weight:800;'>AUDIT</h2>", unsafe_allow_html=True)

    audit_base = df_salao.copy()

    if "audit_status" not in audit_base.columns:
        st.info("Sem dados de AUDIT.")
        return

    audit_base["status_audit_tratado"] = (
        audit_base["audit_status"]
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
    ).fillna("AUDIT INCOMPLETO")

    df_audit = audit_base.groupby("status_audit_tratado")[qtd_col].sum().reset_index() if qtd_col in audit_base.columns else pd.DataFrame()

    total = df_audit[qtd_col].sum() if not df_audit.empty else 0

    cols = st.columns(len(df_audit) if len(df_audit) > 0 else 1)

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
