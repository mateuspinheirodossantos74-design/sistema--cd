import mysql.connector

def deletar_usuario(usuario):
    
    cursor = conn.cursor()
    
    # Usar o nome correto da tabela
    cursor.execute("DELETE FROM usuarios WHERE usuario = %s", (usuario,))
    conn.commit()
    
    cursor.close()
    conn.close()
    print(f"Usuário {usuario} deletado com sucesso!")

# Exemplo: deletar usuário antigo
deletar_usuario("mateus")
