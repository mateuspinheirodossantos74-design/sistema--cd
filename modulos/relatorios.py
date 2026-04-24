import streamlit as st
import pandas as pd
import io
import re

from modulos.conexao import get_connection

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import cm


# ==========================
# CONFIG
# ==========================
PDF_LIMIT = 80


# ==========================
# AUXILIAR
# ==========================
def limpar_nome_arquivo(nome):
    if not nome:
        return "relatorio"

    nome = str(nome).strip()
    nome = re.sub(r"[^\w\s-]", "", nome)
    nome = nome.replace(" ", "_")

    return nome


# ==========================
# PREPARAÇÃO PDF
# ==========================
def preparar_df_pdf(df):
    df = df.copy()

    if "descricao" in df.columns:
        df["descricao"] = df["descricao"].fillna("").astype(str)

    return df


# ==========================
# CARREGAR DADOS
# ==========================
@st.cache_data(ttl=300)
def carregar_dados():
    try:
        conn = get_connection()

        query = """
        SELECT
            bo.tipo_pedido,
            bo.filial_destino,
            bo.olpn,
            bo.item,
            bo.descricao,
            bo.local_picking,
            bo.qtde_pecas_item,
            bo.status_olpn,
            bo.box,
            bo.wave,
            c.conferente,
            bo.audit_status
        FROM base_operacional bo
        LEFT JOIN conferentes c
            ON bo.box = c.box
        """

        df = pd.read_sql(query, conn)

        df_demanda = pd.read_sql(
            "SELECT wave, demanda FROM demanda",
            conn
        )

        conn.close()

        df["wave"] = (
            df["wave"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        df_demanda["wave"] = (
            df_demanda["wave"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        df = df.merge(
            df_demanda,
            on="wave",
            how="left"
        )

        df["tipo_pedido"] = (
            df["tipo_pedido"]
            .astype(str)
            .str.split(" - ")
            .str[0]
        )

        return df

    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()


# ==========================
# COLUNAS
# ==========================
COLUNAS = [
    "tipo_pedido",
    "filial_destino",
    "olpn",
    "item",
    "descricao",
    "local_picking",
    "qtde_pecas_item",
    "status_olpn",
    "box",
    "conferente"
]

COLUNAS_AUDIT = COLUNAS + ["audit_status"]

MAPA_COLUNAS = {
    "tipo_pedido": "Tipo",
    "filial_destino": "Filial",
    "olpn": "oLPN",
    "item": "Item",
    "descricao": "Descrição",
    "local_picking": "Local",
    "qtde_pecas_item": "Qtde",
    "status_olpn": "Status",
    "box": "Box",
    "conferente": "Conferente",
    "audit_status": "Audit"
}


# ==========================
# AUDIT
# ==========================
def tratar_audit(df):
    df["audit_status"] = (
        df["audit_status"]
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

    return df


# ==========================
# PDF
# ==========================
def gerar_pdf(df_packed, df_audit, modo, conferente):

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1.0 * cm,
        leftMargin=1.0 * cm,
        topMargin=0.8 * cm,
        bottomMargin=0.8 * cm
    )

    styles = getSampleStyleSheet()
    elements = []

    def montar_tabela(df, titulo):

        df = df.rename(columns=MAPA_COLUNAS).copy()
        df = preparar_df_pdf(df)

        total_linhas = len(df)

        for start in range(0, total_linhas, PDF_LIMIT):

            chunk = df.iloc[start:start + PDF_LIMIT]

            elements.append(
                Paragraph(
                    f"{titulo} - {conferente}".upper(),
                    styles["Heading2"]
                )
            )

            elements.append(Spacer(1, 6))

            data = [chunk.columns.tolist()] + chunk.values.tolist()

            # ==========================
            # 🔧 AJUSTE CORRETO (SEM MISTURAR COLUNAS)
            # ==========================
            n_cols = len(chunk.columns)

            base_widths = [
                1.2 * cm,
                1.6 * cm,
                2.6 * cm,
                2.0 * cm,
                7.8 * cm,
                2.2 * cm,
                1.4 * cm,
                2.2 * cm,
                1.4 * cm,
                3.0 * cm,   # conferente maior (CORREÇÃO PRINCIPAL)
            ]

            if n_cols > len(base_widths):
                base_widths += [2.2 * cm] * (n_cols - len(base_widths))

            col_widths = base_widths[:n_cols]

            table = Table(
                data,
                repeatRows=1,
                colWidths=col_widths
            )

            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.black),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

                ("GRID", (0, 0), (-1, -1), 0.35, colors.black),

                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),

                ("FONTSIZE", (0, 0), (-1, -1), 8),

                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

                # 🔥 CORREÇÃO IMPORTANTE DE ALINHAMENTO
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),

                ("ALIGN", (0, 1), (3, -1), "CENTER"),
                ("ALIGN", (4, 1), (4, -1), "LEFT"),
                ("ALIGN", (5, 1), (9, -1), "CENTER"),

                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))

            elements.append(table)
            elements.append(Spacer(1, 10))

            if start + PDF_LIMIT < total_linhas:
                elements.append(PageBreak())

    if modo in ["COMPLETO", "PACKED"]:
        montar_tabela(df_packed, "PACKED")

    if modo == "COMPLETO":
        elements.append(PageBreak())

    if modo in ["COMPLETO", "AUDIT"]:
        montar_tabela(df_audit, "AUDIT")

    doc.build(elements)
    buffer.seek(0)

    return buffer


# ==========================
# RENDER
# ==========================
def render():
    st.title("📄 Relatório de Pendências por Conferente")

    df = carregar_dados()

    if df.empty:
        st.warning("Sem dados disponíveis")
        return

    df = tratar_audit(df)

    st.sidebar.header("🔎 Filtros")

    conferente_sel = st.sidebar.selectbox(
        "Conferente",
        sorted(df["conferente"].dropna().unique())
    )

    df = df[df["conferente"] == conferente_sel]

    demandas = sorted(df["demanda"].dropna().unique().tolist())

    demanda_sel = st.sidebar.selectbox(
        "Demanda",
        ["Todas"] + demandas
    )

    if demanda_sel != "Todas":
        df = df[df["demanda"] == demanda_sel]

    status_packed = st.sidebar.multiselect(
        "Status oLPN",
        sorted(df["status_olpn"].dropna().unique()),
        default=sorted(df["status_olpn"].dropna().unique())
    )

    status_audit = st.sidebar.multiselect(
        "Status Audit",
        sorted(df["audit_status"].dropna().unique()),
        default=sorted(df["audit_status"].dropna().unique())
    )

    df_base = df.copy()

    df_packed = df_base[df_base["status_olpn"].isin(status_packed)][COLUNAS].copy()
    df_audit = df_base[df_base["audit_status"].isin(status_audit)][COLUNAS_AUDIT].copy()

    df_packed["box_num"] = pd.to_numeric(df_packed["box"], errors="coerce")
    df_audit["box_num"] = pd.to_numeric(df_audit["box"], errors="coerce")

    df_packed = df_packed.sort_values(by=["box_num", "olpn"]).drop(columns=["box_num"])
    df_audit = df_audit.sort_values(by=["box_num", "olpn"]).drop(columns=["box_num"])

    nome_base = limpar_nome_arquivo(conferente_sel)

    aba1, aba2 = st.tabs(["📦 Packed", "🧾 Audit"])

    with aba1:
        st.dataframe(df_packed, use_container_width=True)

        st.markdown(f"""
        **📊 Resumo PACKED**
        - Total de registros: {len(df_packed)}
        - Total de peças: {df_packed['qtde_pecas_item'].sum():,.0f}
        - 🔢 Contador final: {len(df_packed)}
        """)

    with aba2:
        st.dataframe(df_audit, use_container_width=True)

        st.markdown(f"""
        **📊 Resumo AUDIT**
        - Total de registros: {len(df_audit)}
        - Total de peças: {df_audit['qtde_pecas_item'].sum():,.0f}
        - 🔢 Contador final: {len(df_audit)}
        """)

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📦 PACKED"):
            pdf = gerar_pdf(df_packed, df_audit, "PACKED", conferente_sel)

            st.download_button(
                "Baixar PDF PACKED",
                pdf,
                f"{nome_base}_packed.pdf"
            )

    with col2:
        if st.button("🧾 AUDIT"):
            pdf = gerar_pdf(df_packed, df_audit, "AUDIT", conferente_sel)

            st.download_button(
                "Baixar PDF AUDIT",
                pdf,
                f"{nome_base}_audit.pdf"
            )

    with col3:
        if st.button("📄 COMPLETO"):
            pdf = gerar_pdf(df_packed, df_audit, "COMPLETO", conferente_sel)

            st.download_button(
                "Baixar PDF COMPLETO",
                pdf,
                f"{nome_base}_completo.pdf"
            )
