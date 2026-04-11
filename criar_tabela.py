import mysql.connector



cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS colaboradores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    usuario VARCHAR(50) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    nivel_acesso VARCHAR(50) NOT NULL,
    primeiro_acesso BOOLEAN DEFAULT TRUE,
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

print("Tabela colaboradores criada!")

cursor.close()
conn.close()

