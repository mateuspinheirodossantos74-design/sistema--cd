import mysql.connector

conn = mysql.connector.connect(
    host="gondola.proxy.rlwy.net",
    user="root",
    password="NWyoLjEbDJydymKDvQHxQhzNwdJkAMuH",
    database="railway",
    port=25644
)
cursor = conn.cursor()

# Adicionar a coluna 'primeiro_acesso' com valor padrão 1
cursor.execute("""
ALTER TABLE usuarios
ADD COLUMN primeiro_acesso TINYINT(1) NOT NULL DEFAULT 1;
""")

print("Coluna 'primeiro_acesso' adicionada com sucesso!")

cursor.close()
conn.close()
