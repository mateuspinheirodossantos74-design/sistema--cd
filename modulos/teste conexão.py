from conexao import conectar


try:
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES;")
    tabelas = cursor.fetchall()
    print("Conexão OK! Tabelas no banco:")
    for t in tabelas:
        print(t)
    cursor.close()
    conn.close()
except Exception as e:
    print("Erro na conexão:", e)
