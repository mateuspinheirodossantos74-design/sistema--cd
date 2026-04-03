import mysql.connector
import os

def conectar():
    """
    Retorna uma conexão ativa com o banco MySQL
    """

    host = os.environ.get("DB_HOST")
    user = os.environ.get("DB_USER")
    password = os.environ.get("DB_PASSWORD")
    database = os.environ.get("DB_NAME")
    port = int(os.environ.get("DB_PORT", 3306))

    print("HOST USADO:", host)  # DEBUG

    conn = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        port=port
    )

    return conn
