import streamlit as st
import os
import base64
import bcrypt
import re
from modulos.conexao import conectar

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SENHA_PADRAO = "cd@1200"
CAMINHO_IMAGEM = os.path.join(BASE_DIR, "..", "imagens", "fundo.jpg")

# ==========================
# POLÍTICA DE SENHA
# ==========================
def validar_politica_senha(senha):
    if len(senha) < 10:
        return False, "Senha deve ter no mínimo 10 caracteres"
    if not re.search(r"\d", senha):
        return False, "Senha precisa ter número"
    if not re.search(r"[!@#$%&*]", senha):
        return False, "Senha precisa ter caractere especial"
    return True, ""

# ==========================
# LOG DE ACESSO
# ==========================
def registrar_log(usuario, status):
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO log_acessos (usuario,status) VALUES (%s,%s)",
            (usuario, status)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except:
        pass

# ==========================
# BACKGROUND + ESTILO
# ==========================
def adicionar_background():
    if os.path.exists(CAMINHO_IMAGEM):
        with open(CAMINHO_IMAGEM, "rb") as img:
            encoded = base64.b64encode(img.read()).decode()

        st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpeg;base64,{encoded}");
            background-size: cover;
        }}

        .stApp::before {{
            content:"";
            position:fixed;
            width:100%;
            height:100%;
            background:rgba(0,0,0,0.5);
        }}

        .login-container {{
            position:relative;
            z-index:1;
            width:400px;
            margin:auto;
            margin-top:120px;
        }}

        /* 🔥 TABS */
        .stTabs [data-baseweb="tab"] {{
            color: white;
            font-size: 18px;
            font-weight: bold;
        }}

        .stTabs [aria-selected="true"] {{
            color: #ffffff;
            border-bottom: 3px solid white;
        }}

        /* 🔥 LABELS (Usuário / Senha) */
        label {{
            color: white !important;
            font-weight: bold;
        }}

        </style>
        """, unsafe_allow_html=True)

# ==========================
# VALIDAR LOGIN
# ==========================
def validar_login(usuario, senha):
    try:
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT nome, senha_hash, primeiro_acesso, nivel_acesso
            FROM colaboradores
            WHERE usuario=%s AND ativo=TRUE
        """, (usuario,))

        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if not result:
            registrar_log(usuario, "erro")
            return "erro"

        nome, senha_hash, primeiro_acesso, nivel = result

        if not bcrypt.checkpw(senha.encode(), senha_hash.encode()):
            registrar_log(usuario, "erro")
            return "erro"

        registrar_log(usuario, "sucesso")

        st.session_state.usuario = usuario
        st.session_state.nome_usuario = nome
        st.session_state.nivel = nivel

        if primeiro_acesso:
            st.session_state.trocar_senha_obrigatorio = True
            return "primeiro_acesso"

        st.session_state.logado = True
        return "sucesso"

    except Exception as e:
        st.error(f"Erro no login: {e}")
        return "erro"

# ==========================
# TROCAR SENHA
# ==========================
def trocar_senha(usuario, senha_atual, nova):
    try:
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT senha_hash FROM colaboradores WHERE usuario=%s",
            (usuario,)
        )
        result = cursor.fetchone()
        if not result:
            cursor.close()
            conn.close()
            return "Usuário não encontrado"

        senha_hash = result[0]
        if not bcrypt.checkpw(senha_atual.encode(), senha_hash.encode()):
            cursor.close()
            conn.close()
            return "Senha atual incorreta"

        valido, msg = validar_politica_senha(nova)
        if not valido:
            cursor.close()
            conn.close()
            return msg

        nova_hash = bcrypt.hashpw(nova.encode(), bcrypt.gensalt()).decode()

        cursor.execute("""
            UPDATE colaboradores
            SET senha_hash=%s, primeiro_acesso=FALSE
            WHERE usuario=%s
        """, (nova_hash, usuario))

        conn.commit()
        cursor.close()
        conn.close()

        return "ok"

    except Exception as e:
        return f"Erro ao trocar senha: {e}"

# ==========================
# RENDER
# ==========================
def render():
    if "logado" not in st.session_state:
        st.session_state.logado = False

    if "trocar_senha_obrigatorio" not in st.session_state:
        st.session_state.trocar_senha_obrigatorio = False

    adicionar_background()
    st.markdown('<div class="login-container">', unsafe_allow_html=True)

    # PRIMEIRO ACESSO
    if st.session_state.trocar_senha_obrigatorio:
        st.error("🔒 Primeiro acesso - você precisa trocar sua senha")

        senha_atual = st.text_input("Senha atual", type="password")
        nova = st.text_input("Nova senha", type="password")

        if st.button("Alterar senha"):
            resultado = trocar_senha(
                st.session_state.usuario,
                senha_atual,
                nova
            )
            if resultado == "ok":
                st.success("Senha alterada com sucesso!")
                st.session_state.trocar_senha_obrigatorio = False
                st.session_state.logado = True
                st.rerun()
            else:
                st.error(resultado)

    else:
        abas = st.tabs(["🔐 Login", "🔑 Trocar senha"])

        # LOGIN
        with abas[0]:
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")

            if st.button("Entrar"):
                if not usuario or not senha:
                    st.warning("Preencha usuário e senha")
                    return

                resultado = validar_login(usuario, senha)
                if resultado == "sucesso":
                    st.success(f"Bem-vindo {st.session_state.nome_usuario}")
                    st.rerun()
                elif resultado == "primeiro_acesso":
                    st.warning("Primeiro acesso detectado")
                else:
                    st.error("Usuário ou senha inválidos")

        # TROCAR SENHA
        with abas[1]:
            usuario = st.text_input("Usuário troca")
            senha_atual = st.text_input("Senha atual", type="password")
            nova = st.text_input("Nova senha", type="password")

            if st.button("Alterar senha"):
                resultado = trocar_senha(usuario, senha_atual, nova)
                if resultado == "ok":
                    st.success("Senha alterada")
                else:
                    st.error(resultado)

    st.markdown('</div>', unsafe_allow_html=True)
