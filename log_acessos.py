import mysql.connector

# Conexão com o banco
conn = mysql.connector.connect(
    host="gondola.proxy.rlwy.net",
    user="root",
    password="NWyoLjEbDJydymKDvQHxQhzNwdJkAMuH",
    database="railway",
    port=25644
)
cursor = conn.cursor()

# Criação da tabela log_acessos
cursor.execute("""
CREATE TABLE IF NOT EXISTS log_acessos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    usuario VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP
);
""")

print("Tabela 'log_acessos' criada com sucesso!")

cursor.close()
conn.close()
