import streamlit as st
import re
from datetime import datetime, timedelta
from difflib import get_close_matches
from modulos.conexao import conectar


# ==========================
# EXECUTAR QUERY
# ==========================
def executar_query(query, params=None):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(query, params or ())
    result = cursor.fetchall()

    conn.close()
    return result


# ==========================
# CACHE DE VALORES
# ==========================
@st.cache_data(ttl=300)
def get_valores(coluna):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(f"SELECT DISTINCT {coluna} FROM base_operacional")
    valores = [r[0] for r in cursor.fetchall() if r[0]]
    conn.close()
    return valores


# ==========================
# INTERPRETADOR DE PERGUNTA
# ==========================
def interpretar(pergunta):
    pergunta = pergunta.lower()

    filtros = {
        "where": [],
        "params": [],
        "status": None
    }

    hoje = datetime.today().date()

    # DATA
    if "hoje" in pergunta:
        filtros["where"].append("DATE(data_limite_expedicao) = %s")
        filtros["params"].append(hoje)

    if "amanhã" in pergunta or "amanha" in pergunta:
        filtros["where"].append("DATE(data_limite_expedicao) = %s")
        filtros["params"].append(hoje + timedelta(days=1))

    match_dia = re.search(r"dia (\d{1,2})", pergunta)
    if match_dia:
        filtros["where"].append("DAY(data_limite_expedicao) = %s")
        filtros["params"].append(int(match_dia.group(1)))

    # WAVE
    match_wave = re.search(r"w\d+", pergunta)
    if match_wave:
        filtros["where"].append("wave = %s")
        filtros["params"].append(match_wave.group(0).upper())

    # SETOR
    setores = get_valores("setor")
    setor_match = get_close_matches(pergunta, setores, n=1, cutoff=0.4)
    if setor_match:
        filtros["where"].append("setor = %s")
        filtros["params"].append(setor_match[0])

    # DEMANDA
    demandas = get_valores("demanda")
    for d in demandas:
        if all(p in pergunta for p in d.lower().split()):
            filtros["where"].append("demanda = %s")
            filtros["params"].append(d)
            break

    # INTENÇÃO
    mapa = {
        "falta": "Created",
        "coletar": "Created",
        "separar": "Created",
        "separado": "Packed",
        "conferido": "Loaded",
        "expedido": "Shipped"
    }

    for palavra, status in mapa.items():
        if palavra in pergunta:
            filtros["status"] = status
            break

    return filtros


# ==========================
# GERAR RESPOSTA
# ==========================
def responder(pergunta):
    filtros = interpretar(pergunta)

    where_sql = " AND ".join(filtros["where"])
    where_sql = f"WHERE {where_sql}" if where_sql else ""

    params = filtros["params"]

    # ==========================
    # CONSULTA PRINCIPAL
    # ==========================
    if filtros["status"]:
        query = f"""
        SELECT 
            SUM(qtde_pecas_item) as total
        FROM base_operacional
        {where_sql}
        {"AND" if where_sql else "WHERE"} status_olpn = %s
        """

        result = executar_query(query, params + [filtros["status"]])
        total = result[0]["total"] if result else 0

        return f"""
📊 Resultado encontrado:

👉 Status: {filtros['status']}
👉 Quantidade: {int(total or 0):,}

Se quiser, posso detalhar mais 👀
""".replace(",", ".")

    # ==========================
    # RESUMO GERAL
    # ==========================
    query = f"""
    SELECT 
        status_olpn,
        SUM(qtde_pecas_item) as total
    FROM base_operacional
    {where_sql}
    GROUP BY status_olpn
    """

    result = executar_query(query, params)

    if not result:
        return "Não encontrei dados com esses filtros 😕"

    texto = "📊 Situação atual:\n\n"

    total_geral = 0

    for row in result:
        valor = int(row["total"] or 0)
        total_geral += valor
        texto += f"• {row['status_olpn']}: {valor:,}\n".replace(",", ".")

    texto += f"\n📦 Total geral: {total_geral:,}".replace(",", ".")

    return texto


# ==========================
# INTERFACE
# ==========================
def render():
    st.title("🤖 Assistente Inteligente do CD (modo avançado)")

    if "chat" not in st.session_state:
        st.session_state.chat = []

    pergunta = st.chat_input("Digite sua pergunta...")

    if pergunta:
        resposta = responder(pergunta)

        st.session_state.chat.append(("user", pergunta))
        st.session_state.chat.append(("bot", resposta))

    for tipo, msg in st.session_state.chat:
        if tipo == "user":
            st.chat_message("user").write(msg)
        else:
            st.chat_message("assistant").write(msg)
