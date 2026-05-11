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
    Spacer
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
        df["descricao"] = (
            df["descricao"]
            .fillna("")
            .astype(str)
        )

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

        if "demanda" not in df.columns:
            df["demanda"] = None

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
        rightMargin=0.5 * cm,
        leftMargin=0.5 * cm,
        topMargin=0.5 * cm,
        bottomMargin=0.5 * cm
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

            data = [
                chunk.columns.tolist()
            ] + chunk.values.tolist()

            page_width = landscape(A4)[0]

            usable_width = page_width - 1.0 * cm

            weights = [
                1.0,
                0.9,
                1.6,
                1.4,
                7.2,
                1.8,
                1.3,
                1.4,
                1.2,
                2.0
            ]

            n_cols = len(chunk.columns)

            if n_cols > len(weights):
                weights += [2.2] * (
                    n_cols - len(weights)
                )

            weights = weights[:n_cols]

            total_weight = sum(weights)

            col_widths = [
                (w / total_weight) * usable_width
                for w in weights
            ]

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
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("ALIGN", (4, 1), (4, -1), "LEFT"),
                ("ALIGN", (5, 1), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),

            ]))

            elements.append(table)

            elements.append(Spacer(1, 4))

    if modo in ["COMPLETO", "PACKED"]:
        montar_tabela(df_packed, "PACKED")

    if modo == "COMPLETO":
        elements.append(Spacer(1, 20))

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

    # ==========================
    # CACHE OLPNS
    # ==========================
    if "olpns_cache" not in st.session_state:
        st.session_state.olpns_cache = []

    df = carregar_dados()

    if df.empty:
        st.warning("Sem dados disponíveis")
        return

    df = tratar_audit(df)

    st.sidebar.header("🔎 Filtros")

    # ==========================
    # DEMANDA
    # ==========================
    if "demanda" not in df.columns:
        df["demanda"] = "SEM DEMANDA"

    demandas = sorted(
        df["demanda"]
        .dropna()
        .unique()
        .tolist()
    )

    demanda_sel = st.sidebar.selectbox(
        "Demanda",
        ["Todas"] + demandas
    )

    if demanda_sel != "Todas":
        df = df[
            df["demanda"] == demanda_sel
        ]

    # ==========================
    # CONFERENTE
    # ==========================
    st.sidebar.subheader("Conferente")

    conferentes = sorted(
        df["conferente"]
        .dropna()
        .unique()
        .tolist()
    )

    select_all_conf = st.sidebar.checkbox(
        "Selecionar Todos",
        value=True
    )

    if select_all_conf:

        conferente_sel = st.sidebar.multiselect(
            "Conferente",
            conferentes,
            default=conferentes
        )

    else:

        conferente_sel = st.sidebar.multiselect(
            "Conferente",
            conferentes
        )

    if conferente_sel:

        df = df[
            df["conferente"]
            .isin(conferente_sel)
        ]

    else:

        df = df.iloc[0:0]

    # ==========================
    # BOX
    # ==========================
    boxes = sorted(
        df["box"]
        .dropna()
        .astype(str)
        .unique()
    )

    box_sel = st.sidebar.multiselect(
        "Box",
        boxes,
        default=boxes
    )

    df = df[
        df["box"]
        .astype(str)
        .isin(box_sel)
    ]

    # ==========================
    # ITEM
    # ==========================
    item_busca = st.sidebar.text_input(
        "Buscar Item",
        placeholder="Digite o item..."
    )

    # ==========================
    # STATUS PACKED
    # ==========================
    st.sidebar.subheader("Filtro PACKED")

    status_packed = st.sidebar.multiselect(
        "Status oLPN (Packed)",
        sorted(
            df["status_olpn"]
            .dropna()
            .unique()
        ),
        default=sorted(
            df["status_olpn"]
            .dropna()
            .unique()
        )
    )

    # ==========================
    # STATUS AUDIT
    # ==========================
    st.sidebar.subheader("Filtro AUDIT")

    status_olpn_audit = st.sidebar.multiselect(
        "Status oLPN (Audit)",
        sorted(
            df["status_olpn"]
            .dropna()
            .unique()
        ),
        default=sorted(
            df["status_olpn"]
            .dropna()
            .unique()
        )
    )

    status_audit = st.sidebar.multiselect(
        "Status Audit",
        sorted(
            df["audit_status"]
            .dropna()
            .unique()
        ),
        default=sorted(
            df["audit_status"]
            .dropna()
            .unique()
        )
    )

    # ==========================
    # BASE FINAL
    # ==========================
    df_base = df.copy()

    if item_busca:

        df_base = df_base[
            df_base["item"]
            .astype(str)
            .str.contains(
                item_busca,
                case=False,
                na=False
            )
        ]

    # ==========================
    # PACKED
    # ==========================
    df_packed = df_base[
        df_base["status_olpn"]
        .isin(status_packed)
    ][COLUNAS].copy()

    # ==========================
    # AUDIT
    # ==========================
    df_audit = df_base[
        (
            df_base["status_olpn"]
            .isin(status_olpn_audit)
        )
        &
        (
            df_base["audit_status"]
            .isin(status_audit)
        )
    ][COLUNAS_AUDIT].copy()

    df_packed["box_num"] = pd.to_numeric(
        df_packed["box"],
        errors="coerce"
    )

    df_audit["box_num"] = pd.to_numeric(
        df_audit["box"],
        errors="coerce"
    )

    df_packed = (
        df_packed
        .sort_values(
            by=["box_num", "olpn"]
        )
        .drop(columns=["box_num"])
    )

    df_audit = (
        df_audit
        .sort_values(
            by=["box_num", "olpn"]
        )
        .drop(columns=["box_num"])
    )

    # ==========================
    # NOME PDF
    # ==========================
    if len(conferente_sel) == 1:

        nome_base = limpar_nome_arquivo(
            conferente_sel[0]
        )

        titulo_pdf = conferente_sel[0]

    else:

        nome_base = "multiplos_conferentes"

        titulo_pdf = "MULTIPLOS CONFERENTES"

    # ==========================
    # TABS
    # ==========================
    aba1, aba2 = st.tabs([
        "📦 Packed",
        "🧾 Audit"
    ])

    # ==========================
    # ABA PACKED
    # ==========================
    with aba1:

        df_editor = df_packed.copy()

        df_editor.insert(0, "Selecionar", False)

        editor = st.data_editor(
            df_editor,
            use_container_width=True,
            hide_index=True,
            key="editor_packed"
        )

        olpns_selecionadas = (
            editor[
                editor["Selecionar"] == True
            ]["olpn"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        col_add, col_clear = st.columns(2)

        # ==========================
        # ADICIONAR AO CACHE
        # ==========================
        with col_add:

            if st.button("➕ Adicionar Selecionadas"):

                atuais = set(
                    st.session_state.olpns_cache
                )

                novas = set(olpns_selecionadas)

                st.session_state.olpns_cache = list(
                    atuais.union(novas)
                )

                st.success(
                    f"{len(novas)} oLPN(s) adicionadas!"
                )

        # ==========================
        # LIMPAR CACHE
        # ==========================
        with col_clear:

            if st.button("🗑️ Limpar Lista"):

                st.session_state.olpns_cache = []

                st.success("Lista limpa!")

        st.markdown("### 🖨️ oLPNs Acumuladas")

        texto_olpns = ", ".join(
            sorted(st.session_state.olpns_cache)
        )

        st.text_area(
            "Copiar para reimpressão",
            value=texto_olpns,
            height=150
        )

        # ==========================
        # DOWNLOAD EXCEL
        # ==========================
        if st.session_state.olpns_cache:

            df_export = pd.DataFrame({
                "olpn": sorted(
                    st.session_state.olpns_cache
                )
            })

            buffer_excel = io.BytesIO()

            with pd.ExcelWriter(
                buffer_excel,
                engine="openpyxl"
            ) as writer:

                df_export.to_excel(
                    writer,
                    index=False,
                    sheet_name="OLPNS"
                )

            st.download_button(
                "📥 Baixar Excel",
                data=buffer_excel.getvalue(),
                file_name="olpns_reimpressao.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # ==========================
    # ABA AUDIT
    # ==========================
    with aba2:

        st.dataframe(
            df_audit,
            use_container_width=True
        )

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    # ==========================
    # PDF PACKED
    # ==========================
    with col1:

        if st.button("📦 PACKED"):

            pdf = gerar_pdf(
                df_packed,
                df_audit,
                "PACKED",
                titulo_pdf
            )

            st.download_button(
                "Baixar PDF PACKED",
                pdf,
                f"{nome_base}_packed.pdf"
            )

    # ==========================
    # PDF AUDIT
    # ==========================
    with col2:

        if st.button("🧾 AUDIT"):

            pdf = gerar_pdf(
                df_packed,
                df_audit,
                "AUDIT",
                titulo_pdf
            )

            st.download_button(
                "Baixar PDF AUDIT",
                pdf,
                f"{nome_base}_audit.pdf"
            )

    # ==========================
    # PDF COMPLETO
    # ==========================
    with col3:

        if st.button("📄 COMPLETO"):

            pdf = gerar_pdf(
                df_packed,
                df_audit,
                "COMPLETO",
                titulo_pdf
            )

            st.download_button(
                "Baixar PDF COMPLETO",
                pdf,
                f"{nome_base}_completo.pdf"
            )
