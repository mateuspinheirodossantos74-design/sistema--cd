import mysql.connector

# ===============================
# CONFIGURAÇÃO DE CONEXÃO RAILWAY
# ===============================
RAILWAY_HOST = "gondola.proxy.rlwy.net"
RAILWAY_USER = "root"
RAILWAY_PASSWORD = "NWyoLjEbDJydymKDvQHxQhzNwdJkAMuH"
RAILWAY_DB = "railway"
RAILWAY_PORT = 25644

try:
    # Conectar ao banco
    conn = mysql.connector.connect(
        host=RAILWAY_HOST,
        user=RAILWAY_USER,
        password=RAILWAY_PASSWORD,
        database=RAILWAY_DB,
        port=RAILWAY_PORT
    )

    print("✅ Conexão realizada com sucesso!")

    # Criar cursor e testar uma query simples
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES;")
    tabelas = cursor.fetchall()
    print("Tabelas no banco:", tabelas)

except mysql.connector.Error as err:
    print("❌ Erro ao conectar:", err)

finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals() and conn.is_connected():
        conn.close()
        print("Conexão fechada")
