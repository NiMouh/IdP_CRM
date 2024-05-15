import sqlite3
from hashlib import sha256

DATABASE_PATH = 'db.sql'

# Connect to the database
conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()

# Drop the table if it exists
cursor.execute("DROP TABLE IF EXISTS nivel_acesso;")
cursor.execute("DROP TABLE IF EXISTS contactoColaborador;")
cursor.execute("DROP TABLE IF EXISTS estado;")
cursor.execute("DROP TABLE IF EXISTS pais;")
cursor.execute("DROP TABLE IF EXISTS utilizador;")
cursor.execute("DROP TABLE IF EXISTS cliente;")
cursor.execute("DROP TABLE IF EXISTS colaborador;")
cursor.execute("DROP TABLE IF EXISTS concelho;")
cursor.execute("DROP TABLE IF EXISTS distrito;")
cursor.execute("DROP TABLE IF EXISTS freguesia;")
cursor.execute("DROP TABLE IF EXISTS morada;")
cursor.execute("DROP TABLE IF EXISTS obra;")
cursor.execute("DROP TABLE IF EXISTS lista_produtos;")
cursor.execute("DROP TABLE IF EXISTS escalaoDesconto;")
cursor.execute("DROP TABLE IF EXISTS tabelaPrecos;")
cursor.execute("DROP TABLE IF EXISTS contactosCliente;")
cursor.execute("DROP TABLE IF EXISTS stock;")

# Create the table

cursor.execute('''
    CREATE TABLE IF NOT EXISTS tabelaPrecos (    
            tabelaPrecos_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tabelaPrecos_ProdutoNome VARCHAR(50) NOT NULL,
            tabelaPrecos_Unit FLOAT
    );
''')

cursor.execute('''        
    CREATE TABLE IF NOT EXISTS nivel_acesso (
        nivel_acesso_id INTEGER PRIMARY KEY AUTOINCREMENT,
        nivel_acesso_nome VARCHAR(50) NOT NULL,
        nivel_acesso_nivel INTEGER NOT NULL
    );
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS escalaoDesconto (
        escalaoDesconto_id INTEGER PRIMARY KEY AUTOINCREMENT,
        escalaoDesconto_nome VARCHAR(50) NOT NULL,
        escalaoDesconto_desconto FLOAT
    );
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS contactoColaborador (
        contactoColaborador_id INTEGER PRIMARY KEY AUTOINCREMENT,
        contactoColaborador_email VARCHAR(50) NOT NULL,
        contactoColaborador_telefone VARCHAR(9) NOT NULL,
        contactoColaborador_fax VARCHAR(9) NOT NULL
    );
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS contactosCliente (
        contactosCliente_id INTEGER PRIMARY KEY AUTOINCREMENT,
        contactosCliente_email VARCHAR(50) NOT NULL,
        contactosCliente_telefone VARCHAR(9) NOT NULL,
        contactosCliente_fax VARCHAR(9) NOT NULL,
        fk_cliente_id INTEGER,
        FOREIGN KEY (fk_cliente_id) REFERENCES cliente(cliente_id)
    );
''')

cursor.execute('''           
    CREATE TABLE IF NOT EXISTS estado (
        estado_id INTEGER PRIMARY KEY AUTOINCREMENT,
        estado_nome VARCHAR(50) NOT NULL,
        estado_ordem INTEGER NOT NULL
    );
''')

cursor.execute('''           
    CREATE TABLE IF NOT EXISTS pais (
        pais_id INTEGER PRIMARY KEY AUTOINCREMENT,
        pais_nome VARCHAR(50) NOT NULL
    );
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS concelho (
        concelho_id INTEGER PRIMARY KEY AUTOINCREMENT,
        concelho_nome VARCHAR(50) NOT NULL,
        fk_distrito INTEGER,
        FOREIGN KEY (fk_distrito) REFERENCES distrito(distrito_id)
    );
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS distrito (
        distrito_id INTEGER PRIMARY KEY AUTOINCREMENT,
        distrito_nome VARCHAR(50) NOT NULL
    );
''')

cursor.execute('''           
    CREATE TABLE IF NOT EXISTS freguesia (
        freguesia_id INTEGER PRIMARY KEY AUTOINCREMENT,
        freguesia_nome VARCHAR(50) NOT NULL,
        fk_concelho INTEGER,
        FOREIGN KEY (fk_concelho) REFERENCES concelho(concelho_id)
    );
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS utilizador (
        utilizador_id INTEGER PRIMARY KEY AUTOINCREMENT,
        utilizador_nome VARCHAR(50) NOT NULL,
        utilizador_password VARCHAR(50) NOT NULL,
        utilizador_data_de_criacao DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        utilizador_ultimo_login DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        fk_nivel_acesso INTEGER,
        FOREIGN KEY (fk_nivel_acesso) REFERENCES nivel_acesso(nivel_acesso_id)
    );
''')

cursor.execute('''               
    CREATE TABLE IF NOT EXISTS cliente (
        cliente_id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_nome VARCHAR(50) NOT NULL,
        cliente_data_de_criacao DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        cliente_zona INTEGER NOT NULL,
        fk_escalaoDesconto INTEGER,
        fk_utilizador INTEGER,
        FOREIGN KEY (fk_escalaoDesconto) REFERENCES escalaoDesconto(escalaoDesconto_id),
        FOREIGN KEY (fk_utilizador) REFERENCES utilizador(utilizador_id)
    );
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS colaborador (
        colaborador_id INTEGER PRIMARY KEY AUTOINCREMENT,
        colaborador_nome VARCHAR(50) NOT NULL,
        colaborador_data_de_criacao DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        fk_contactoColaborador INTEGER,
        fk_cliente INTEGER,
        FOREIGN KEY (fk_contactoColaborador) REFERENCES contactoColaborador(contactoColaborador_id),
        FOREIGN KEY (fk_cliente) REFERENCES cliente(cliente_id)
    );
''')

cursor.execute('''           
    CREATE TABLE IF NOT EXISTS morada (
        morada_id INTEGER PRIMARY KEY AUTOINCREMENT,
        morada_codigo_postal VARCHAR(50) NOT NULL,
        morada_rua VARCHAR(50) NOT NULL,
        morada_localidade VARCHAR(50) NOT NULL,
        fk_pais INTEGER,
        fk_distrito INTEGER,
        fk_concelho INTEGER,
        fk_freguesia INTEGER,
        fk_cliente INTEGER,
        FOREIGN KEY (fk_pais) REFERENCES pais(pais_id),
        FOREIGN KEY (fk_distrito) REFERENCES distrito(distrito_id),
        FOREIGN KEY (fk_concelho) REFERENCES concelho(concelho_id),
        FOREIGN KEY (fk_freguesia) REFERENCES freguesia(freguesia_id),
        FOREIGN KEY (fk_cliente) REFERENCES cliente(cliente_id)
    );
''')

cursor.execute('''           
    CREATE TABLE IF NOT EXISTS obra (
        obra_id INTEGER PRIMARY KEY AUTOINCREMENT,
        obra_nome VARCHAR(50) NOT NULL,
        obra_rua VARCHAR(50) NOT NULL,
        obra_localidade VARCHAR(50) NOT NULL,
        obra_data_inicio DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        fk_cliente INTEGER,
        fk_estado INTEGER,
        fk_distrito INTEGER,
        fk_concelho INTEGER,
        fk_freguesia INTEGER,
        FOREIGN KEY (fk_cliente) REFERENCES cliente(cliente_id),
        FOREIGN KEY (fk_estado) REFERENCES estado(estado_id),
        FOREIGN KEY (fk_distrito) REFERENCES distrito(distrito_id),
        FOREIGN KEY (fk_concelho) REFERENCES concelho(concelho_id),
        FOREIGN KEY (fk_freguesia) REFERENCES freguesia(freguesia_id)
    );
''')             

cursor.execute('''
    CREATE TABLE IF NOT EXISTS lista_produtos (
        produto_id INTEGER PRIMARY KEY AUTOINCREMENT,
        produtoCodigo INTEGER,
        produtoQuantidade INTEGER,
        fk_obra_id INTEGER,
        produtopreco FLOAT,
        produtoPrecoTotal FLOAT,
        FOREIGN KEY (fk_obra_id) REFERENCES obra(obra_id)
    );
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock (
        stock_id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_quantidade INTEGER,
        fk_produto_id INTEGER,
        FOREIGN KEY (fk_produto_id) REFERENCES tabelaPrecos(tabelaPrecos_id)
    );
''')

# Insert data into the table
cursor.execute('''
    INSERT INTO tabelaPrecos (tabelaPrecos_ProdutoNome, tabelaPrecos_Unit)
    VALUES ('Produto1', 10.0),
     ('Produto2', 20.0),
     ('Produto3', 30.0),
     ('Produto4', 40.0),
     ('Produto5', 50.0);
''')

cursor.execute('''
    INSERT INTO escalaoDesconto (escalaoDesconto_nome, escalaoDesconto_desconto)
    VALUES ('Escalao1', 0.1),
     ('Escalao2', 0.2),
     ('Escalao3', 0.3),
     ('Escalao4', 0.4),
     ('Escalao5', 0.5);
''')

cursor.execute('''
    INSERT INTO nivel_acesso (nivel_acesso_nome, nivel_acesso_nivel)
    VALUES ('Vendedor', 2), ('admin', 1);
''')

cursor.execute('''
    INSERT INTO contactoColaborador (contactoColaborador_email, contactoColaborador_telefone, contactoColaborador_fax)
    VALUES ('colaborador1@email.pt', '912345333', '912345334'), ('colaborador2@email.pt', '912345555', '912345556');
''')

cursor.execute('''
    INSERT INTO contactosCliente (contactosCliente_email, contactosCliente_telefone, contactosCliente_fax)
    VALUES ('cliente1@email.pt', '912345111', '912345112'),('cliente2@email.pt', '912345222', '912345223');
''')

cursor.execute('''
    INSERT INTO estado (estado_nome, estado_ordem)
    VALUES ('Pendente', 1),
      ('Em curso', 2),
      ('Concluída', 3);
''')
               
cursor.execute('''
    INSERT INTO pais (pais_nome)
    VALUES ('Portugal'),
      ('Espanha'),
      ('França'),
      ('Alemanha'),
      ('Itália');
''')

cursor.execute('''  
    INSERT INTO distrito (distrito_nome)
    VALUES ('Aveiro'),
      ('Beja'),
      ('Braga'),
      ('Bragança'),
      ('Castelo Branco'),
      ('Coimbra'),
      ('Évora'),
      ('Faro'),
      ('Guarda'),
      ('Leiria'),
      ('Lisboa'),
      ('Portalegre'),
      ('Porto'),
      ('Santarém'),
      ('Setúbal'),
      ('Viana do Castelo'),
      ('Vila Real'),
      ('Viseu');
''')

cursor.execute('''
    INSERT INTO concelho (concelho_nome, fk_distrito)
    VALUES ('Aveiro','Aveiro'),
      ('Águeda','Aveiro'),
      ('Anadia','Aveiro'),
      ('Arouca','Aveiro'),
      ('Castelo de Paiva','Aveiro'),
      ('Espinho','Aveiro'),
      ('Estarreja','Aveiro'),
      ('Porto','Porto'),
      ('Vila Nova de Gaia','Porto'),
      ('Matosinhos','Porto'),
      ('Maia','Porto'),
      ('Gondomar','Porto'),
      ('Valongo','Porto'),
      ('Coimbra','Coimbra'),    
      ('Arganil','Coimbra'),
      ('Cantanhede','Coimbra'),
      ('Condeixa-a-Nova','Coimbra'),
      ('Figueira da Foz','Coimbra'),
      ('Góis','Coimbra'),
      ('Lousã','Coimbra'),
      ('Mira','Coimbra');
''')

cursor.execute('''
    INSERT INTO freguesia (freguesia_nome, fk_concelho)
    VALUES ('Aguada de Cima','Águeda'),
      ('Borralha','Águeda'),
      ('Castanheira do Vouga','Águeda'),
      ('Recardães','Águeda'),
      ('Valongo do Vouga','Águeda'),
      ('Aguada de Cima','Águeda'),
      ('Borralha','Águeda'),
      ('Castanheira do Vouga','Águeda'),
      ('Recardães','Águeda'),
      ('Matosinhos e Leça da Palmeira','Matosinhos'),
      ('São Mamede de Infesta e Senhora da Hora','Matosinhos'),
      ('Custóias','Matosinhos'),
      ('Alvares','Góis'),
      ('Góis','Porto');
''')

cursor.execute('''
    INSERT INTO morada (morada_codigo_postal, morada_rua, morada_localidade, fk_pais, fk_distrito, fk_concelho, fk_freguesia, fk_cliente)
    VALUES ('3750-123', 'Rua do Campo', 'Aguada de Cima', '1', '1', '1', '1', 1), ('3750-124', 'Rua do Campo', 'Borralha', '3', '3', '4', '2', 1);
''')

cursor.execute('''
    Insert into obra (obra_nome, obra_rua, obra_localidade, fk_cliente, fk_estado, fk_distrito, fk_concelho, fk_freguesia)
    VALUES ('Obra1', 'Rua do Campo', 'Aguada de Cima', 1, 1, 1, 1, 1), ('Obra2', 'Rua do Campo', 'Borralha', 1, 2, 3, 4, 2);
''')
password_ana = sha256('ana'.encode()).hexdigest()
password_simao = sha256('simao'.encode()).hexdigest() 
cursor.execute('''
    INSERT INTO utilizador (utilizador_nome, utilizador_password)
    VALUES ('ana', ?), ('simao', ?);
''' , (password_ana, password_simao))

cursor.execute('''
    INSERT INTO lista_produtos (produtoCodigo, produtoQuantidade, fk_obra_id, produtopreco, produtoPrecoTotal)
    VALUES (1, 10, 1, 10.0, 100.0), 
      (2, 20, 1, 20.0, 400.0),
      (3, 30, 1, 30.0, 900.0),
      (4, 40, 1, 40.0, 1600.0),
      (5, 50, 1, 50.0, 2500.0);
''')

cursor.execute('''
    INSERT INTO stock (stock_quantidade, fk_produto_id)
    VALUES (10, 1),
      (20, 2),
      (30, 3),
      (40, 4),
      (50, 5);
''')

# Show tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

tables = cursor.fetchall()
for table in tables:
    print(table)

# Print utilizador table
cursor.execute("SELECT * FROM utilizador;")
print(cursor.fetchall())

# Commit the changes and close the connection
conn.commit()
conn.close()