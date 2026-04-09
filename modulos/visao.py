import streamlit as st
import pandas as pd
from PIL import Image
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
from modulos.conexao import conectar
import os

IMAGE_PATH = os.path.join("imagens", "2.png")

# ==========================
# UTILITÁRIOS DE SEGURANÇA
# ==========================
def ensure_col(df, col, default=""):
    if col not in df.columns:
        df[col] = default
    return df


def safe_group_sum(df, group_col, sum_col):
    if group_col not in df.columns or sum_col not in df.columns:
        return pd.Series(dtype="int64")
    return df.groupby(group_col)[sum_col].sum()


def safe_sum(df, col):
    return df[col].sum() if col in df.columns else 0


# ==========================
# CARREGAMENTO OTIMIZADO
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
        st.error(f"Erro no banco: {e}")
        return pd.DataFrame()

    # ==========================
    # NORMALIZAÇÃO LEVE (PERFORMANCE)
    # ==========================
    df["box"] = df.get("box", "").astype(str).str.strip()
    df["wave"] = df.get("wave", "").astype(str).str.strip()

    df_setores["box"] = df_setores.get("box", "").astype(str).str.strip()
    df_demandas["wave"] = df_demandas.get("wave", "").astype(str).str.strip()

    # ==========================
    # MERGE OTIMIZADO (MENOS CÓPIAS)
    # ==========================
    df = df.merge(df_setores, on="box", how="left", copy=False)
    df = df.merge(df_demandas, on="wave", how="left", copy=False)

    # ==========================
    # GARANTIA DE COLUNAS CRÍTICAS
    # ==========================
    df = ensure_col(df, "setor", "SEM_SETOR")
    df = ensure_col(df, "demanda", "SEM_DEMANDA")

    if "data_limite_expedicao" in df.columns:
        df["data_limite_expedicao"] = pd.to_datetime(df["data_limite_expedicao"], errors="coerce")

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
            setInterval(() => {
                document.getElementById("clock").innerHTML =
                    new Date().toLocaleTimeString('pt-BR');
            }, 1000);
        </script>
        """,
        height=80
    )

    df = carregar_dados()

    if df.empty:
        st.warning("Banco vazio ou indisponível.")
        st.stop()

    # ==========================
    # FILTRO SETOR (ROBUSTO)
    # ==========================
    st.sidebar.subheader("Filtro por Setor")

    setores = df["setor"].dropna().unique().tolist()
    setores.sort()

    setores_sel = st.sidebar.multiselect("Setor:", setores, default=setores)

    if setores_sel:
        df = df[df["setor"].isin(setores_sel)]

    if df.empty:
        st.warning("Sem dados após filtro de setor.")
        st.stop()

    # ==========================
    # FILTRO DATA (OTIMIZADO)
    # ==========================
    if "data_limite_expedicao" in df.columns:
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

        df = df[
            (df["data_limite_expedicao"] >= pd.to_datetime(data_inicio)) &
            (df["data_limite_expedicao"] <= pd.to_datetime(data_fim))
        ]

    base = df  # referência única (evita cópias inúteis)

    # ==========================
    # DEMANDA (MESMA LÓGICA)
    # ==========================
    st.sidebar.subheader("Filtros — Salão / P.A.R")

    demandas = ["— Nenhuma seleção —"] + sorted(base["demanda"].dropna().unique().tolist())

    demanda_salao = st.sidebar.selectbox("Demanda Salão:", demandas)
    demanda_par = st.sidebar.selectbox("Demanda P.A.R:", demandas)

    df_salao = base if demanda_salao == "— Nenhuma seleção —" else base[base["demanda"] == demanda_salao]
    df_par = base if demanda_par == "— Nenhuma seleção —" else base[base["demanda"] == demanda_par]

    # ==========================
    # FUNÇÕES CORE
    # ==========================
    status_col = "status_olpn"
    qtd_col = "qtde_pecas_item"

    def fmt(v):
        return f"{int(v):,}".replace(",", ".")

    def card(col, titulo, valor, cor, subtitle=None, size="medium"):
        sizes = {"small": ("22px", "52px", "6px"), "medium": ("30px", "72px", "14px")}
        t, v, p = sizes[size]

        col.markdown(
            f"""
            <div style="background:white;padding:{p};
            border-radius:18px;text-align:center;
            box-shadow:0 6px 18px rgba(0,0,0,0.18);">
                <h3 style="font-size:{t};margin:0;">{titulo}</h3>
                <p style="font-size:{v};color:{cor};font-weight:800;margin:6px 0;">
                    {fmt(valor)}
                </p>
                {f"<p style='font-size:18px;font-weight:600;'>{subtitle}</p>" if subtitle else ""}
            </div>
            """,
            unsafe_allow_html=True
        )

    # ==========================
    # SALÃO
    # ==========================
    res_salao = safe_group_sum(df_salao, status_col, qtd_col)
    cols = st.columns(5)

    for i, status in enumerate(["Created", "Packed", "Loaded", "Shipped"]):
        card(cols[i], status, res_salao.get(status, 0), "black")

    card(cols[4], "Total", safe_sum(df_salao, qtd_col), "black")

    # ==========================
    # P.A.R
    # ==========================
    st.markdown("## P.A.R")

    res_par = safe_group_sum(df_par, status_col, qtd_col)
    cols = st.columns(5)

    for i, status in enumerate(["Created", "Packed", "Loaded", "Shipped"]):
        card(cols[i], status, res_par.get(status, 0), "black")

    card(cols[4], "Total", safe_sum(df_par, qtd_col), "black")

    # ==========================
    # AUDIT ULTRA ESTÁVEL
    # ==========================
    st.markdown("## AUDIT")

    if "audit_status" not in df_salao.columns:
        st.info("Sem AUDIT.")
        return

    audit = df_salao.copy()

    audit["audit_status"] = audit["audit_status"].astype(str).str.upper().str.strip()

    audit_map = {
        "AUDIT_COMPLETE": "COMPLETO",
        "AUDIT_COMPLETE_WITH_VARIANCE": "INCOMPLETO",
        "": "INCOMPLETO",
        "NAN": "INCOMPLETO",
        "NONE": "INCOMPLETO"
    }

    audit["audit_status_tratado"] = audit["audit_status"].replace(audit_map).fillna("INCOMPLETO")

    df_audit = safe_group_sum(audit, "audit_status_tratado", qtd_col).reset_index()

    total = df_audit[qtd_col].sum() if not df_audit.empty else 0

    cols = st.columns(max(len(df_audit), 1))

    for i, row in df_audit.iterrows():
        pct = (row[qtd_col] / total * 100) if total else 0

        card(
            cols[i],
            row["audit_status_tratado"],
            row[qtd_col],
            "black",
            subtitle=f"{pct:.1f}%",
            size="small"
        )
