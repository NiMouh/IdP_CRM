import sqlite3
from hashlib import sha256

DATABASE_PATH = 'db.sql'

# Connect to the database
conn = sqlite3.connect(DATABASE_PATH)
cursor = conn.cursor()

# Create the table

cursor.execute('''        
    CREATE TABLE IF NOT EXISTS nivel_acesso (
        nivel_acesso_id INTEGER PRIMARY KEY AUTOINCREMENT,
        nivel_acesso_nome VARCHAR(50) NOT NULL,
        nivel_acesso_nivel INTEGER NOT NULL
    );
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS contacto (
        contacto_id INTEGER PRIMARY KEY AUTOINCREMENT,
        contacto_email VARCHAR(50) NOT NULL,
        contacto_telefone VARCHAR(9) NOT NULL,
        contacto_fax VARCHAR(9) NOT NULL
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
    CREATE TABLE IF NOT EXISTS utilizador (
        utilizador_id INTEGER PRIMARY KEY AUTOINCREMENT,
        utilizador_username VARCHAR(50) NOT NULL,
        utilizador_email VARCHAR(50) NOT NULL,
        utilizador_password VARCHAR(50) NOT NULL,
        utilizador_data_de_criacao DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        utilizador_ultimo_login DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
    );
''')

cursor.execute('''               
    CREATE TABLE IF NOT EXISTS cliente (
        cliente_id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_nome VARCHAR(50) NOT NULL,
        cliente_data_de_criacao DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        cliente_zona INTEGER NOT NULL
    );
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS colaborador (
        colaborador_id INTEGER PRIMARY KEY AUTOINCREMENT,
        colaborador_nome VARCHAR(50) NOT NULL,
        colaborador_data_de_criacao DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
    );
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS concelho (
        concelho_id INTEGER PRIMARY KEY AUTOINCREMENT,
        concelho_nome VARCHAR(50) NOT NULL
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
        freguesia_nome VARCHAR(50) NOT NULL
    );
''')

cursor.execute('''           
    CREATE TABLE IF NOT EXISTS morada (
        morada_id INTEGER PRIMARY KEY AUTOINCREMENT,
        morada_codigo_postal VARCHAR(50) NOT NULL,
        morada_rua VARCHAR(50) NOT NULL,
        morada_localidade VARCHAR(50) NOT NULL,
        pais_id INTEGER,
        distrito_id INTEGER,
        concelho_id INTEGER,
        freguesia_id INTEGER,
        FOREIGN KEY (pais_id) REFERENCES pais(pais_id),
        FOREIGN KEY (distrito_id) REFERENCES distrito(distrito_id),
        FOREIGN KEY (concelho_id) REFERENCES concelho(concelho_id),
        FOREIGN KEY (freguesia_id) REFERENCES freguesia(freguesia_id)
    );
''')

cursor.execute('''           
    CREATE TABLE IF NOT EXISTS obra (
        obra_id INTEGER PRIMARY KEY AUTOINCREMENT,
        obra_nome VARCHAR(50) NOT NULL,
        obra_rua VARCHAR(50) NOT NULL,
        obra_localidade VARCHAR(50) NOT NULL,
        obra_data_inicio DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        cliente_id INTEGER,
        estado_id INTEGER,
        distrito_id INTEGER,
        concelho_id INTEGER,
        freguesia_id INTEGER,
        FOREIGN KEY (cliente_id) REFERENCES cliente(cliente_id),
        FOREIGN KEY (estado_id) REFERENCES estado(estado_id),
        FOREIGN KEY (distrito_id) REFERENCES distrito(distrito_id),
        FOREIGN KEY (concelho_id) REFERENCES concelho(concelho_id),
        FOREIGN KEY (freguesia_id) REFERENCES freguesia(freguesia_id)
    );
''')


# Insert data into the table (Hash the password)
cursor.execute('''
    INSERT INTO utilizador (utilizador_username, utilizador_email, utilizador_password)
    VALUES (?, ?, ?);
''', ('simao', 'simao@ua.pt', sha256('simao'.encode()).hexdigest()))

cursor.execute('''
    INSERT INTO nivel_acesso (nivel_acesso_nome, nivel_acesso_nivel)
    VALUES ('admin', 1);
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