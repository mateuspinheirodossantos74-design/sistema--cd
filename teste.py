import mysql.connector
import bcrypt

conn = mysql.connector.connect(
    host="gondola.proxy.rlwy.net",
    user="root",
    password="NWyoLjEbDJydymKDvQHxQhzNwdJkAMuH",
    database="railway",
    port=25644
)

cursor = conn.cursor()

senha = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()

cursor.execute("""
INSERT INTO colaboradores (nome, usuario, senha_hash, nivel_acesso, primeiro_acesso, ativo)
VALUES (%s,%s,%s,%s,%s,%s)
""", ("Administrador", "admin", senha, "admin", False, True))

conn.commit()

print("Admin criado!")

cursor.close()
conn.close()
