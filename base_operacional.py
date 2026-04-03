import mysql.connector


cursor = conn.cursor()

# Criar tabela
cursor.execute("""
CREATE TABLE IF NOT EXISTS base_operacional (
    id INT PRIMARY KEY AUTO_INCREMENT,
    
    filial VARCHAR(50),
    data_pedido DATE,
    tipo_pedido VARCHAR(50),
    wave VARCHAR(50),
    data_locacao_pedido DATE,
    shipment VARCHAR(50),
    filial_destino VARCHAR(50),
    pedido VARCHAR(50),
    status_pedido VARCHAR(50),
    pedido_venda VARCHAR(50),
    olpn VARCHAR(50),
    ultimo_update_olpn DATETIME,
    tote VARCHAR(50),
    tarefa VARCHAR(50),
    tarefa_status VARCHAR(50),
    grupo_tarefa VARCHAR(50),
    item VARCHAR(50),
    descricao VARCHAR(255),
    local_picking VARCHAR(100),
    qtde_pecas_item INT,
    volume FLOAT,
    status_olpn VARCHAR(50),
    numero_gaiola VARCHAR(50),
    box VARCHAR(50),
    marcacao_ead VARCHAR(50),
    data_prevista_entrega DATE,
    data_limite_expedicao DATE,
    inventory_type_id VARCHAR(50),
    cod_setor_item VARCHAR(50),
    desc_setor_item VARCHAR(100),
    audit_status VARCHAR(50),
    setor VARCHAR(50),
    conferentes VARCHAR(100),
    audit VARCHAR(50),
    demanda VARCHAR(50),
    status_box VARCHAR(50),
    fechamento VARCHAR(50),
    grupo2 VARCHAR(50),
    wave2 VARCHAR(50),
    departamento VARCHAR(100),
    des_setor VARCHAR(100),
    dep VARCHAR(50),
    pedido2 VARCHAR(50),
    pedido3 VARCHAR(50)
);
""")

print("Tabela 'base_operacional' criada com sucesso!")

cursor.close()
conn.close()
