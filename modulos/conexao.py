import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="gondola.proxy.rlwy.net",
        user="root",
        password="NWyoLjEbDJydymKDvQHxQhzNwdJkAMuH",
        database="railway",
        port=25644,
        autocommit=True
    )
