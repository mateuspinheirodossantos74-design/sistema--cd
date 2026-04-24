import pandas as pd
import numpy as np
import mysql.connector

# Caminho do Excel
caminho_arquivo = r"C:\Users\User20\Documents\Base site.xlsx"

# Ler Excel
df = pd.read_excel(caminho_arquivo)

# Remover colunas inválidas
df = df.loc[:, ~df.columns.isna()]
df = df.dropna(axis=1, how='all')

# Padronizar nomes das colunas
df.columns = [
    str(col).strip().lower().replace(" ", "_").replace(".", "")
    for col in df.columns
]

# 🔥 Tratar TODOS os tipos de nulos
df = df.replace({np.nan: None})
df = df.replace(["nan", "NaN", "None"], None)

# 🔍 DEBUG
print("\nColunas do Excel:")
print(df.columns.tolist())

# 🔥 Mapeamento
mapa_colunas = {
    "filial": "filial",
    "data_do_pedido": "data_pedido",
    "tipo_de_pedido": "tipo_pedido",
    "wave": "wave",
    "data_locação_pedido": "data_locacao_pedido",
    "data_locacao_pedido": "data_locacao_pedido",
    "shipment": "shipment",
    "filial_destino": "filial_destino",
    "pedido": "pedido",
    "status_pedido": "status_pedido",
    "pedido_de_venda": "pedido_venda",
    "olpn": "olpn",
    "último_update_olpn": "ultimo_update_olpn",
    "ultimo_update_olpn": "ultimo_update_olpn",
    "tote": "tote",
    "tarefa": "tarefa",
    "tarefa_status": "tarefa_status",
    "grupo_de_tarefa": "grupo_tarefa",
    "item": "item",
    "descrição": "descricao",
    "descricao": "descricao",
    "local_de_picking": "local_picking",
    "qtde_peças_item": "qtde_pecas_item",
    "qtde_pecas_item": "qtde_pecas_item",
    "volume": "volume",
    "status_olpn": "status_olpn",
    "numero_da_gaiola": "numero_gaiola",
    "box": "box",
    "marcação_de_ead": "marcacao_ead",
    "marcacao_de_ead": "marcacao_ead",
    "data_prevista_entrega": "data_prevista_entrega",
    "data_limite_expedição": "data_limite_expedicao",
    "data_limite_expedicao": "data_limite_expedicao",
    "inventory_type_id": "inventory_type_id",
    "cod_setor_item": "cod_setor_item",
    "desc_setor_item": "desc_setor_item",
    "audit_status": "audit_status",
    "setor": "setor",
    "conferentes": "conferentes",
    "audit": "audit",
    "demanda": "demanda",
    "status_box": "status_box",
    "fechamento": "fechamento",
    "grupo2": "grupo2",
    "grupo_2": "grupo2",
    "wave2": "wave2",
    "departamento": "departamento",
    "des_setor": "des_setor",
    "dep": "dep",
    "pedido2": "pedido2",
    "pedido3": "pedido3"
}

df = df.rename(columns=mapa_colunas)

print("\nColunas após mapeamento:")
print(df.columns.tolist())

# 🔥 Colunas do banco
colunas_banco = [
    "filial", "data_pedido", "tipo_pedido", "wave", "data_locacao_pedido",
    "shipment", "filial_destino", "pedido", "status_pedido", "pedido_venda",
    "olpn", "ultimo_update_olpn", "tote", "tarefa", "tarefa_status",
    "grupo_tarefa", "item", "descricao", "local_picking", "qtde_pecas_item",
    "volume", "status_olpn", "numero_gaiola", "box", "marcacao_ead",
    "data_prevista_entrega", "data_limite_expedicao", "inventory_type_id",
    "cod_setor_item", "desc_setor_item", "audit_status", "setor",
    "conferentes", "audit", "demanda", "status_box", "fechamento",
    "grupo2", "wave2", "departamento", "des_setor", "dep", "pedido2", "pedido3"
]

# Criar colunas faltantes
for col in colunas_banco:
    if col not in df.columns:
        df[col] = None

# Garantir ordem
df = df[colunas_banco]

print(f"\nTotal de linhas: {len(df)}")

# Conexão
conn = mysql.connector.connect(

cursor = conn.cursor()

# 🔥 LIMPAR TABELA
cursor.execute("TRUNCATE TABLE base_operacional")
conn.commit()
print("\nTabela limpa!")

# Insert
query = """
INSERT INTO base_operacional (
    filial, data_pedido, tipo_pedido, wave, data_locacao_pedido,
    shipment, filial_destino, pedido, status_pedido, pedido_venda,
    olpn, ultimo_update_olpn, tote, tarefa, tarefa_status,
    grupo_tarefa, item, descricao, local_picking, qtde_pecas_item,
    volume, status_olpn, numero_gaiola, box, marcacao_ead,
    data_prevista_entrega, data_limite_expedicao, inventory_type_id,
    cod_setor_item, desc_setor_item, audit_status, setor,
    conferentes, audit, demanda, status_box, fechamento,
    grupo2, wave2, departamento, des_setor, dep, pedido2, pedido3
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

# 🔥 PREPARAR DADOS
print("\nPreparando dados...")
valores = [
    tuple(None if pd.isna(x) else x for x in row)
    for _, row in df.iterrows()
]

print("Inserindo em lotes...")

# 🔥 INSERÇÃO EM LOTES
batch_size = 1000

for i in range(0, len(valores), batch_size):
    lote = valores[i:i + batch_size]
    cursor.executemany(query, lote)
    conn.commit()
    print(f"{i + len(lote)} registros inseridos...")

print("\n✅ Dados inseridos com sucesso!")

cursor.close()
conn.close()
