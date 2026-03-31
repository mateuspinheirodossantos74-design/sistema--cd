import mysql.connector
import bcrypt

# ===============================
# CONEXÃO RAILWAY
# ===============================
conn = mysql.connector.connect(
    host="gondola.proxy.rlwy.net",
    user="root",
    password="NWyoLjEbDJydymKDvQHxQhzNwdJkAMuH",
    database="railway",
    port=25644
)

cursor = conn.cursor()

# ===============================
# DADOS DO USUÁRIO
# ===============================
nome = "Mateus Pinheiro"
usuario = "2960007532"
senha = "cd@1200"
nivel_acesso = "admin"

# ===============================
# GERAR HASH
# ===============================
senha_hash = bcrypt.hashpw(
    senha.encode(),
    bcrypt.gensalt()
).decode()

# ===============================
# INSERT CORRETO
# ===============================
query = """
INSERT INTO colaboradores 
(nome, usuario, senha_hash, nivel_acesso, primeiro_acesso, ativo)
VALUES (%s, %s, %s, %s, TRUE, TRUE)
"""

values = (nome, usuario, senha_hash, nivel_acesso)

cursor.execute(query, values)
conn.commit()

print("✅ Usuário admin criado com sucesso!")

cursor.close()
conn.close()
