import mysql.connector

# Conexão
conn = mysql.connector.connect(
    host="gondola.proxy.rlwy.net",
    user="root",
    password="NWyoLjEbDJydymKDvQHxQhzNwdJkAMuH",
    database="railway",
    port=25644
)

cursor = conn.cursor()

print("Limpando tabela...")

cursor.execute("TRUNCATE TABLE base_operacional")
conn.commit()

print("✅ Tabela limpa com sucesso!")

cursor.close()
conn.close()
