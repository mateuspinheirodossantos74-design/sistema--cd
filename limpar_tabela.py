

cursor = conn.cursor()

print("Limpando tabela...")

cursor.execute("TRUNCATE TABLE base_operacional")
conn.commit()

print("✅ Tabela limpa com sucesso!")

cursor.close()
conn.close()
