from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlite3 import connect, Error
from secrets import token_urlsafe
from hashlib import sha256

app = Flask(__name__)
CORS(app) # This will enable all CORS requests

app.secret_key = token_urlsafe(32) # 32 bytes = 256 bits

# GLOBAL VARIABLES #

STATUS_CODE = {
    'SUCCESS': 200,
    'BAD_REQUEST': 400,
    'UNAUTHORIZED': 401,
    'NOT_FOUND': 404,
    'INTERNAL_SERVER_ERROR': 500
}


DATABASE_PATH = r'.\database\db.sql'


def create_connection() -> connect:
    try:
        conn = connect(DATABASE_PATH, check_same_thread=False)
        return conn
    except Error as e:
        print(e)
        return None

# API #

@app.route('/api/create_user', methods=['POST'])
def create_user() -> jsonify:
    user_data = request.get_json()
    username = user_data.get('username')
    email = user_data.get('email')
    password = user_data.get('password')

    if not username or not password:
        return jsonify({'error_message': 'Missing username or password'}), STATUS_CODE['BAD_REQUEST']
    
    connection = create_connection()
    if connection is None:
        return jsonify({'error_message': 'Database connection failed'}), STATUS_CODE['INTERNAL_SERVER_ERROR']
    
    hashed_password = sha256(password.encode()).hexdigest()
    
    cursor = connection.cursor()
    cursor.execute("INSERT INTO utilizador (utilizador_username, utilizador_email, utilizador_password) VALUES (?, ?, ?)", (username, email, hashed_password))
    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({'success_message': 'User created successfully'}), STATUS_CODE['SUCCESS']

@app.route('/api/delete_user/<username>', methods=['DELETE'])
def delete_user(username : str) -> jsonify:
    if not username:
        return jsonify({'error_message': 'Missing username'}), STATUS_CODE['BAD_REQUEST']
    
    connection = create_connection()
    if connection is None:
        return jsonify({'error_message': 'Database connection failed'}), STATUS_CODE['INTERNAL_SERVER_ERROR']
    
    cursor = connection.cursor()
    cursor.execute("DELETE FROM utilizador WHERE utilizador_username = ?", (username,))
    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({'success_message': 'User deleted successfully'}), STATUS_CODE['SUCCESS']

@app.route('/api/fetch_users', methods=['GET'])
def fetch_users() -> jsonify:
    connection = create_connection()
    if connection is None:
        return jsonify({'error_message': 'Database connection failed'}), STATUS_CODE['INTERNAL_SERVER_ERROR']
    
    cursor = connection.cursor()
    cursor.execute("SELECT utilizador_username FROM utilizador")
    users = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify({'users': users}), STATUS_CODE['SUCCESS']

# Obtain the address of the all 'clientes' from the database
@app.route('/api/fetch_client_addresses', methods=['GET'])
def fetch_client_addresses() -> jsonify:
    connection = create_connection()
    if connection is None:
        return jsonify({'error_message': 'Database connection failed'}), STATUS_CODE['INTERNAL_SERVER_ERROR']
    
    cursor = connection.cursor()
    cursor.execute("""
        SELECT 
            cliente.cliente_nome,
            morada.morada_localidade,
            freguesia.freguesia_nome,
            concelho.concelho_nome,
            distrito.distrito_nome,
            pais.pais_nome
        FROM 
            cliente
        JOIN 
            morada ON cliente.cliente_id = morada.fk_cliente
        JOIN 
            freguesia ON morada.fk_freguesia = freguesia.freguesia_id
        JOIN 
            concelho ON morada.fk_concelho = concelho.concelho_id
        JOIN 
            distrito ON morada.fk_distrito = distrito.distrito_id
        JOIN 
            pais ON morada.fk_pais = pais.pais_id;
    """)

    addresses_db = cursor.fetchall()

    # Add the addresses to a dictionary
    addresses = {}

    for address in addresses_db:
        client_address = {
            'localidade': address[1],
            'freguesia': address[2],
            'concelho': address[3],
            'distrito': address[4],
            'pais': address[5]
        }

        addresses.update({address[0]: client_address})

    cursor.close()

    return jsonify({'addresses': addresses}), STATUS_CODE['SUCCESS']

# Given the name of the 'colaboradores', obtain the contacts of the 'colaboradores' from the database
@app.route('/api/fetch_colaborador_contacts/<colaborador>', methods=['GET'])
def fetch_colaborador_contacts(colaborador : str) -> jsonify:
    connection = create_connection()
    if connection is None:
        return jsonify({'error_message': 'Database connection failed'}), STATUS_CODE['INTERNAL_SERVER_ERROR']
    
    cursor = connection.cursor()
    cursor.execute("""
        SELECT 
            colaborador.colaborador_nome,
            contactoColaborador.contactoColaborador_email,
            contactoColaborador.contactoColaborador_telefone,
            contactoColaborador.contactoColaborador_fax
        FROM 
            colaborador
        JOIN 
            contactoColaborador ON colaborador.fk_contactoColaborador = contactoColaborador.contactoColaborador_id
        WHERE 
            colaborador.colaborador_nome = ?;
    """, (colaborador,))

    contacts_db = cursor.fetchall()

    cursor.close()

    # Add the contacts to a dictionary
    contacts = {}

    for contact in contacts_db:
        colaborador_contact = {
            'email': contact[1],
            'telefone': contact[2],
            'fax': contact[3]
        }
        contacts.update({contact[0]: colaborador_contact})

    return jsonify({'contacts': contacts}), STATUS_CODE['SUCCESS']


# Given the name of the 'obra', obtain the address of the 'obra' from the database
@app.route('/api/fetch_obra_address/<obra>', methods=['GET'])
def fetch_obra_address(obra : str) -> jsonify:
    connection = create_connection()
    if connection is None:
        return jsonify({'error_message': 'Database connection failed'}), STATUS_CODE['INTERNAL_SERVER_ERROR']
    
    cursor = connection.cursor()
    cursor.execute("""
        SELECT 
            obra.nome
            obra.obra_rua
            obra.obra_localidade
            distrito.distrito_nome
            concelho.concelho_nome
            freguesia.freguesia_nome
                   
        FROM
            obra
        JOIN
            morada ON obra.fk_morada = morada.morada_id
        JOIN
            distrito ON morada.fk_distrito = distrito.distrito_id
        JOIN
            concelho ON morada.fk_concelho = concelho.concelho_id
        JOIN
            freguesia ON morada.fk_freguesia = freguesia.freguesia_id
        WHERE
            obra.nome = ?;
    """, (obra,))
    
    address_db = cursor.fetchall()

    cursor.close()

    # Add the address to a dictionary
    address = {}

    for addr in address_db:
        obra_address = {
            'rua': addr[1],
            'localidade': addr[2],
            'distrito': addr[3],
            'concelho': addr[4],
            'freguesia': addr[5]
        }
        address.update({addr[0]: obra_address})

    return jsonify({'address': address}), STATUS_CODE['SUCCESS']

# Given the name of the 'obra', obtain the 'produto' used in the 'obra' from the database
@app.route('/api/fetch_obra_produto/<obra>', methods=['GET'])
def fetch_obra_produto(obra : str) -> jsonify:
    connection = create_connection()
    if connection is None:
        return jsonify({'error_message': 'Database connection failed'}), STATUS_CODE['INTERNAL_SERVER_ERROR']
    
    cursor = connection.cursor()
    cursor.execute("""
        SELECT 
            obra.nome,
            produto.produto_nome,
            produto.produto_preco,
            produto.produto_quantidade
        FROM
            obra
        JOIN
            produtoObra ON obra.obra_id = produtoObra.fk_obra
        JOIN
            produto ON produtoObra.fk_produto = produto.produto_id
        WHERE
            obra.nome = ?;
    """, (obra,))
    
    produtos_db = cursor.fetchall()

    cursor.close()

    # Add the produtos to a dictionary
    produtos = {}

    for produto in produtos_db:
        obra_produto = {
            'nome': produto[1],
            'preco': produto[2],
            'quantidade': produto[3]
        }
        produtos.update({produto[0]: obra_produto})

    return jsonify({'produtos': produtos}), STATUS_CODE['SUCCESS']

# Obtain all the 'produto' in 'stock' from the database
@app.route('/api/fetch_stock', methods=['GET'])
def fetch_stock() -> jsonify:
    connection = create_connection()
    if connection is None:
        return jsonify({'error_message': 'Database connection failed'}), STATUS_CODE['INTERNAL_SERVER_ERROR']
    
    cursor = connection.cursor()
    cursor.execute("""
        SELECT
            produto.produto_nome,
            stock.stock_quantidade
            tabelaPrecos.tabelaPrecos_Unit
        FROM
            produto
        JOIN
            stock ON produto.produto_id = stock.fk_produto
        JOIN
            tabelaPrecos ON produto.produto_id = tabelaPrecos.fk_produto;
    """)

    stock_db = cursor.fetchall()

    cursor.close()

    # Add the stock to a dictionary
    stock = {}

    for produto in stock_db:
        produto_stock = {
            'quantidade': produto[1],
            'preco': produto[2]
        }
        stock.update({produto[0]: produto_stock})

    return jsonify({'stock': stock}), STATUS_CODE['SUCCESS']

# PROTECTED ROUTES #

@app.route('/api/protected', methods=['GET'])
@jwt_required()
def protected() -> jsonify:
    current_user = get_jwt_identity()
    return jsonify({'logged_in_as': current_user}), STATUS_CODE['SUCCESS']

if __name__ == '__main__':
    app.run(debug=True, port=5020) # Different port than the client