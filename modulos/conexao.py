import mysql.connector
import os
from dotenv import load_dotenv

# Carrega as variáveis do .env
load_dotenv()

# ==========================
# CONFIGURAÇÃO DO BANCO
# ==========================
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = int(os.getenv("DB_PORT", 3306))  # caso não tenha, usa 3306

def conectar():
    """
    Retorna uma conexão ativa com o banco MySQL
    """
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )
    return conn
