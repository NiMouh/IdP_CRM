import sqlite3
from hashlib import sha256
import os

DATABASE_RELATIVE_PATH = 'db.sql'
DATABASE_PATH = os.path.join(os.path.dirname(__file__), DATABASE_RELATIVE_PATH)

if os.path.exists(DATABASE_PATH):
    os.remove(DATABASE_PATH)

# Connect to the database
conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()

# Drop the table if it exists
tables_to_drop = [
    "log", "nivel_acesso", "contactoColaborador", "estado", "pais",
    "utilizador", "cliente", "colaborador", "concelho", "distrito",
    "freguesia", "morada", "obra", "produto", "escalaoDesconto",
    "tabelaPrecos", "contactosCliente", "stock", "client_application",
    "authorization_code", "challenge", "question", "response"
]

for table in tables_to_drop:
    cursor.execute(f"DROP TABLE IF EXISTS {table};")

# Create the table

cursor.execute('''
    CREATE TABLE IF NOT EXISTS log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        log_tipo VARCHAR(50) NOT NULL,
        log_data DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        log_mensagem TEXT NOT NULL,
        log_username VARCHAR(50) NOT NULL,
        log_ip VARCHAR(50) NOT NULL,
        log_nivel_acesso VARCHAR(50) NOT NULL,
        log_segmentacao VARCHAR(50) NOT NULL
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
        utilizador_email VARCHAR(50) NOT NULL,
        utilizador_password VARCHAR(50) NOT NULL,
        utilizador_salt VARCHAR(10) NOT NULL,
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
        fk_colaborador INTEGER,
        FOREIGN KEY (fk_escalaoDesconto) REFERENCES escalaoDesconto(escalaoDesconto_id),
        FOREIGN KEY (fk_colaborador) REFERENCES colaborador(colaborador_id)
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
    CREATE TABLE IF NOT EXISTS produto (
        produto_id INTEGER PRIMARY KEY AUTOINCREMENT,
        produtoCodigo INTEGER NOT NULL,
        produtoNome VARCHAR(50) NOT NULL,
        fk_obra_id INTEGER,
        FOREIGN KEY (fk_obra_id) REFERENCES obra(obra_id)
    );
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS tabelaPrecos (    
            tabelaPrecos_id INTEGER PRIMARY KEY AUTOINCREMENT,
            fk_produto_id INTEGER,
            tabelaPrecos_Unit FLOAT,
            FOREIGN KEY (fk_produto_id) REFERENCES produto(produto_id)
    );
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock (
        stock_id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_quantidade INTEGER,
        fk_produto_id INTEGER,
        fk_tabelaPrecos_id INTEGER,
        FOREIGN KEY (fk_produto_id) REFERENCES produto(produto_id)
        FOREIGN KEY (fk_tabelaPrecos_id) REFERENCES tabelaPrecos(tabelaPrecos_id)
    );
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS client_application (
        client_application_id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_application_client_id VARCHAR(50) NOT NULL, 
        client_application_secret VARCHAR(50) NOT NULL,
        client_application_redirect_uri VARCHAR(50) NOT NULL
    );          
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS authorization_code (
        authorization_code_id INTEGER PRIMARY KEY AUTOINCREMENT,
        authorization_code_code VARCHAR(50) NOT NULL,
        fk_client_application_id INTEGER,
        fk_utilizador_id INTEGER,
        FOREIGN KEY (fk_client_application_id) REFERENCES client_application(client_application_id),
        FOREIGN KEY (fk_utilizador_id) REFERENCES utilizador(utilizador_id)
    );
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS challenge (
        challenge_id INTEGER PRIMARY KEY AUTOINCREMENT,
        challenge_nonce VARCHAR(100) NOT NULL,
        fk_utilizador_id INTEGER,
        FOREIGN KEY (fk_utilizador_id) REFERENCES utilizador(utilizador_id)
    );
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS question (
        question_id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_question VARCHAR(100) NOT NULL
    );
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS response (
        response_id INTEGER PRIMARY KEY AUTOINCREMENT,
        response_answer VARCHAR(100) NOT NULL,
        fk_question_id INTEGER,
        fk_utilizador_id INTEGER,
        FOREIGN KEY (fk_question_id) REFERENCES question(question_id),
        FOREIGN KEY (fk_utilizador_id) REFERENCES utilizador(utilizador_id)
    );
''')
# Insert data into the table
cursor.execute('''
    INSERT INTO tabelaPrecos (tabelaPrecos_Unit, fk_produto_id)
    VALUES (10, 1),
        (20, 2),
        (30, 3),
        (40, 4),
        (50, 5);
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
    INSERT INTO cliente (cliente_nome, cliente_zona, fk_escalaoDesconto, fk_colaborador)
    VALUES ('Client1', 1, 1, 1),
        ('Client2', 2, 2, 1);
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
    VALUES ('3750-123', 'Rua do Campo', 'Aguada de Cima', '1', '1', '1', '1', 1), ('3750-124', 'Rua do Campo', 'Borralha', '3', '3', '4', '2', 2);
''')

cursor.execute('''
    Insert into obra (obra_nome, obra_rua, obra_localidade, fk_cliente, fk_estado, fk_distrito, fk_concelho, fk_freguesia)
    VALUES ('Obra1', 'Rua do Campo', 'Aguada de Cima', 1, 1, 1, 1, 1), ('Obra2', 'Rua do Campo', 'Borralha', 1, 2, 3, 4, 2);
''')
salt = os.urandom(4).hex()
password_ana = sha256('ana'.encode() + salt.encode()).hexdigest()
password_simao = sha256('simao'.encode() + salt.encode()).hexdigest()
cursor.execute('''
    INSERT INTO utilizador (utilizador_nome, utilizador_password, utilizador_salt, fk_nivel_acesso, utilizador_email)
    VALUES ('ana', ?, ?, 1, 'raquelvidal99@hotmail.com'), ('simao', ?, ?, 2, 'simaoaugusto11@hotmail.com');
''' , (password_ana, salt, password_simao, salt))

cursor.execute('''
    INSERT INTO produto (produtoCodigo, produtoNome, fk_obra_id)
    VALUES (1, 'Produto1', 1),
      (2, 'Produto2', 2),
      (3, 'Produto3', 3),
      (4, 'Produto4', 4),
      (5, 'Produto5', 5);
''')

cursor.execute('''
    INSERT INTO stock (stock_quantidade, fk_produto_id, fk_tabelaPrecos_id)
    VALUES (10, 1, 1),
      (20, 2, 2),
      (30, 3, 3),
      (40, 4, 4),
      (50, 5, 5);
''')

cursor.execute('''
    INSERT INTO colaborador (colaborador_nome, fk_contactoColaborador, fk_cliente)
    VALUES ('Colaborador1', 1, 1), ('Colaborador2', 2, 2);
''')

cursor.execute('''
    Insert into client_application (client_application_client_id, client_application_secret, client_application_redirect_uri)
    VALUES ('client_id', '123456', 'http://127.0.0.1:5000/authorize');
''')

cursor.execute('''
    Insert into question (question_question)
    VALUES ('What is your favourite color?'), ('What is your favourite animal?');
''')

cursor.execute('''
    Insert into response (response_answer, fk_question_id, fk_utilizador_id)
    VALUES ('blue', 1, 1), ('red', 1, 2), ('dog', 2, 1), ('cat', 2, 2);
''')
# Show tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
cursor.execute('''SELECT 
                        u.utilizador_nome, u.utilizador_password, n.nivel_acesso_nome
                   FROM 
                        utilizador u
                   JOIN 
                        nivel_acesso n
                   ON
                        u.fk_nivel_acesso = n.nivel_acesso_id
''')

tables = cursor.fetchall()
for table in tables:
    print(table)

# Print utilizador table
cursor.execute("SELECT * FROM utilizador;")
print(cursor.fetchall())

cursor.execute('''
    SELECT 
        r.response_answer
    FROM
        response r
    JOIN
        utilizador u
    ON
        r.fk_utilizador_id = u.utilizador_id
    JOIN
        question q
    ON
        r.fk_question_id = q.question_id
    WHERE
        u.utilizador_nome = ? AND q.question_question = ?;
''', ('ana', 'What is your favourite color?'))
print(cursor.fetchone())


cursor.execute('''
    SELECT 
            q.question_question
        FROM
            question q
        ORDER BY
            RANDOM()
        LIMIT 1;
''')
print(cursor.fetchone())

# Commit the changes and close the connection
conn.commit()
conn.close()