import mysql.connector

# CONFIGURAÇÃO DO BANCO
HOST = "gondola.proxy.rlwy.net"
USER = "root"
PASSWORD = "NWyoLjEbDJydymKDvQHxQhzNwdJkAMuH"
DATABASE = "railway"
PORT = 25644

def conectar():
    """
    Retorna uma conexão ativa com o banco MySQL
    """
    conn = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=DATABASE,
        port=PORT
    )
    return conn
