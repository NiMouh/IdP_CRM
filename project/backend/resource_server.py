import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps
from sqlite3 import connect, Error
from secrets import token_urlsafe
from hashlib import sha256
import requests
import json
import jwt
from jwt.algorithms import RSAAlgorithm
from authorization_server import add_log

app = Flask(__name__)
CORS(app) # This will enable all CORS requests

app.secret_key = token_urlsafe(32) # 32 bytes = 256 bits

# GLOBAL VARIABLES #

JWKS_URL = 'http://127.0.0.1:5010/.well-known/jwks.json'

STATUS_CODE = {
    'SUCCESS': 200,
    'BAD_REQUEST': 400,
    'UNAUTHORIZED': 401,
    'NOT_FOUND': 404,
    'INTERNAL_SERVER_ERROR': 500
}

DATABASE_RELATIVE_PATH = 'database/db.sql'
DATABASE_PATH = os.path.join(os.path.dirname(__file__), DATABASE_RELATIVE_PATH)

def create_connection() -> connect:
    try:
        conn = connect(DATABASE_PATH, check_same_thread=False)
        return conn
    except Error as e:
        print(e)
        return None


# VERIFY TOKENS #

def get_public_key() -> bytes:
    response = requests.get(JWKS_URL)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch JWKS: {response.status_code}")

    jwks = response.json()
    if 'keys' not in jwks or len(jwks['keys']) == 0:
        raise Exception("No keys found in JWKS")

    key = jwks['keys'][0]
    public_key = RSAAlgorithm.from_jwk(json.dumps(key))
    return public_key

def verify_token(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')
        print('Token:', token)
        if not token:
            return jsonify({'error_message': 'Missing Authorization header'}), STATUS_CODE['UNAUTHORIZED']

        token = token.split(' ')[1]
        public_key = get_public_key()
        try:
            decoded_token = jwt.decode(token, public_key, audience='http://127.0.0.1:5020', algorithms=['RS256'])
            request.decoded_token = decoded_token
            print('Decoded Token:', decoded_token)
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({'error_message': 'Token has expired'}), STATUS_CODE['UNAUTHORIZED']
        except jwt.InvalidTokenError:
            return jsonify({'error_message': 'Invalid token'}), STATUS_CODE['UNAUTHORIZED']
    return wrapper

# API #

# TODO: Adicionar logs a cada todos os endpoints

# TODO: Adicionar o decorator verify token e verificar qual o nível de acesso do utilizador
@app.route('/api/ver_clientes', methods=['GET'])
@verify_token
def ver_clientes() -> jsonify:
    connection = create_connection()
    if connection is None:
        return jsonify({'error_message': 'Database connection failed'}), STATUS_CODE['INTERNAL_SERVER_ERROR']

    cursor = connection.cursor()
    cursor.execute('''
        SELECT 
        cliente_nome, 
        cliente_tipo 
        FROM 
        cliente;
    ''')
    db_clientes = cursor.fetchall()

    clientes = {}
    for cliente in db_clientes:
        clientes.update({cliente[0]: cliente[1]})

    cursor.close()
    connection.close()

    return jsonify(clientes), STATUS_CODE['SUCCESS']

@app.route('/api/contactos_clientes', methods=['GET'])
@verify_token
def dashboard() -> jsonify:
    connection = create_connection()
    if connection is None:
        return jsonify({'error_message': 'Database connection failed'}), STATUS_CODE['INTERNAL_SERVER_ERROR']
    
    cursor = connection.cursor()
    cursor.execute('''
        SELECT 
            cc.contactosCliente_email, 
            cc.contactosCliente_telefone, 
            cc.contactosCliente_fax, 
            c.cliente_nome
        FROM 
            contactosCliente cc
        JOIN
            cliente c
        ON 
            cc.fk_cliente_id = c.cliente_id;
    ''')
    db_contacts = cursor.fetchall()

    contacts = {}
    for contact in db_contacts:
        contact_data = {
            'email': contact[0],
            'telefone': contact[1],
            'fax': contact[2]
        }
        contacts.update({contact[3]: contact_data})

    cursor.close()
    connection.close()

    return jsonify(contacts), STATUS_CODE['SUCCESS']
    
@app.route('/api/moradas_clientes', methods=['GET'])
@verify_token
def moradas_clientes() -> jsonify:
    connection = create_connection()
    if connection is None:
        return jsonify({'error_message': 'Database connection failed'}), STATUS_CODE['INTERNAL_SERVER_ERROR']
    
    cursor = connection.cursor()
    cursor.execute('''
        SELECT 
            m.morada_rua, 
            m.morada_localidade, 
            m.morada_codigo_postal, 
            p.pais_nome,
            d.distrito_nome,
            c.concelho_nome,
            f.freguesia_nome,
            c.cliente_nome
        FROM 
            morada m
        JOIN
            pais p
        ON
            m.fk_pais = p.pais_id
        JOIN
            distrito d
        ON
            m.fk_distrito = d.distrito_id
        JOIN
            concelho c
        ON
            m.fk_concelho = c.concelho_id
        JOIN
            freguesia f
        ON
            m.fk_freguesia = f.freguesia_id
        JOIN
            cliente c
        ON 
            m.fk_cliente = c.cliente_id;
    ''')
    db_addresses = cursor.fetchall()

    addresses = {}
    for address in db_addresses:
        address_data = {
            'rua': address[0],
            'localidade': address[1],
            'codigo_postal': address[2],
            'pais': address[3],
            'distrito': address[4],
            'concelho': address[5],
            'freguesia': address[6]
        }
        addresses.update({address[7]: address_data})

    cursor.close()
    connection.close()

    return jsonify(addresses), STATUS_CODE['SUCCESS']

@app.route('/api/contactos_diretor_obra', methods=['GET'])
@verify_token
def contactos_diretor_obra() -> jsonify:
    connection = create_connection()
    if connection is None:
        return jsonify({'error_message': 'Database connection failed'}), STATUS_CODE['INTERNAL_SERVER_ERROR']
    
    cursor = connection.cursor()
    cursor.execute('''
        SELECT 
            cc.contactosCliente_email, 
            cc.contactosCliente_telefone, 
            cc.contactosCliente_fax, 
            c.cliente_nome
        FROM 
            contactosCliente cc
        JOIN
            cliente c
        ON
            cc.fk_cliente_id = c.cliente_id
        WHERE
            c.cliente_tipo = 'diretor de obra';
    ''')
    db_contactsDO = cursor.fetchall()

    contacts = {}
    for contact in db_contactsDO:
        contact_data = {
            'email': contact[0],
            'telefone': contact[1],
            'fax': contact[2]
        }
        contacts.update({contact[3]: contact_data})

    cursor.close()
    connection.close()

    return jsonify(contacts), STATUS_CODE['SUCCESS']

@app.route('/api/obra_estado', methods=['GET'])
@verify_token
def obra_estado() -> jsonify:
    connection = create_connection()
    if connection is None:
        return jsonify({'error_message': 'Database connection failed'}), STATUS_CODE['INTERNAL_SERVER_ERROR']
    
    cursor = connection.cursor()
    cursor.execute('''
        SELECT 
            o.obra_nome,
            e.estado_nome
        FROM 
            estado e
        JOIN
            obra o
        ON
            e.estado_id = o.fk_estado;
    ''')
    db_estados = cursor.fetchall()

    estados = {}
    for estado in db_estados:
        estados.update({estado[0]: estado[1]})

    cursor.close()
    connection.close()

    return jsonify(estados), STATUS_CODE['SUCCESS']

@app.route('/api/morada_obra', methods=['GET'])
@verify_token
def morada_obra() -> jsonify:
    connection = create_connection()
    if connection is None:
        return jsonify({'error_message': 'Database connection failed'}), STATUS_CODE['INTERNAL_SERVER_ERROR']
    
    cursor = connection.cursor()
    cursor.execute('''
        SELECT 
            o.obra_rua, 
            o.obra_localidade, 
            d.distrito_nome,
            c.concelho_nome,
            f.freguesia_nome,
            o.obra_nome
        FROM 
            obra o
        JOIN
            distrito d
        ON
            o.fk_distrito = d.distrito_id
        JOIN
            concelho c
        ON
            o.fk_concelho = c.concelho_id
        JOIN
            freguesia f
        ON
            o.fk_freguesia = f.freguesia_id;
    ''')
    db_addresses = cursor.fetchall()

    addresses = {}
    for address in db_addresses:
        address_data = {
            'rua': address[0],
            'localidade': address[1],
            'distrito': address[2],
            'concelho': address[3],
            'freguesia': address[4]
        }
        addresses.update({address[5]: address_data})

    cursor.close()
    connection.close()

    return jsonify(addresses), STATUS_CODE['SUCCESS']

@app.route('/api/material_obra', methods=['GET'])
@verify_token
def material_obra() -> jsonify:
    connection = create_connection()
    if connection is None:
        return jsonify({'error_message': 'Database connection failed'}), STATUS_CODE['INTERNAL_SERVER_ERROR']
    
    cursor = connection.cursor()
    cursor.execute('''
        SELECT 
            p.produtoNome,
            p.produtoQuantidade,
            tp.tabelaPrecos_Unit,
            o.obra_nome
        FROM 
            tabelaPrecos tp
        JOIN
            produto p
        ON
            tp.fk_produto_id = p.produto_id
        JOIN
            obra o
        ON
            p.fk_obra_id = o.obra_id;
    ''')
    db_material = cursor.fetchall()

    materials = {}
    for material in db_material:
        material_data = {
            'nome': material[0],
            'quantidade': material[1],
            'preco': material[2]
        }
        materials.update({material[3]: material_data})

    cursor.close()
    connection.close()

    return jsonify(materials), STATUS_CODE['SUCCESS']

@app.route('/api/tabela_preco', methods=['GET'])
@verify_token
def tabela_preco() -> jsonify:
    connection = create_connection()
    if connection is None:
        return jsonify({'error_message': 'Database connection failed'}), STATUS_CODE['INTERNAL_SERVER_ERROR']
    
    cursor = connection.cursor()
    cursor.execute('''
        SELECT 
            p.produtoNome,
            tp.tabelaPrecos_Unit
        FROM 
            tabelaPrecos tp
        JOIN
            produto p
        ON
            tp.fk_produto_id = p.produto_id;
    ''')
    db_prices = cursor.fetchall()

    prices = {}
    for price in db_prices:
        prices.update({price[0]: price[1]})

    cursor.close()
    connection.close()

    return jsonify(prices), STATUS_CODE['SUCCESS']

@app.route('/api/stock', methods=['GET'])
@verify_token
def stock() -> jsonify:
    connection = create_connection()
    if connection is None:
        return jsonify({'error_message': 'Database connection failed'}), STATUS_CODE['INTERNAL_SERVER_ERROR']
    
    cursor = connection.cursor()
    cursor.execute('''
        SELECT 
            p.produtoNome,
            s.stock_quantidade
        FROM 
            stock s
        JOIN
            produto p
        ON
            s.fk_produto_id = p.produto_id
        JOIN
            tabelaPrecos tp
        ON
            p.produto_id = tp.fk_produto_id;
    ''')
    db_stock = cursor.fetchall()

    stock = {}
    for produto in db_stock:
        stock.update({produto[0]: produto[1]})

    cursor.close()
    connection.close()

    return jsonify(stock), STATUS_CODE['SUCCESS']

@app.route('/api/stock', methods=['POST', 'DELETE'])
@verify_token
def edit_stock() -> jsonify:

    connection = create_connection()
    if connection is None:
        return jsonify({'error_message': 'Database connection failed'}), STATUS_CODE['INTERNAL_SERVER_ERROR']
    cursor = connection.cursor()

    if request.method == 'DELETE':
        print('DELETE')
        product_data = request.get_json()
        product = product_data.get('product')
        
        if not product:
            return jsonify({'error_message': 'Missing product'}), STATUS_CODE['BAD_REQUEST']
        
        cursor.execute('''
            DELETE FROM stock
            WHERE fk_produto_id = (SELECT produto_id FROM produto WHERE produtoNome = ?);
        ''', (product,))
        connection.commit()
    elif request.method == 'POST':
        stock_data = request.get_json()
        
        products : list = []
        quantities : list = []
        for item in stock_data:
            product = item.get('product')
            quantity = item.get('quantity')
            products.append(product)
            quantities.append(quantity)

        print('Product and quantity:', product, quantity)

        if not stock_data or not isinstance(stock_data, list):
            return jsonify({'error_message': 'Invalid data format'}), STATUS_CODE['BAD_REQUEST']

        for item in stock_data:
            product = item['product']
            quantity = item['quantity']
            
            if not product or not quantity:
                return jsonify({'error_message': 'Missing product or quantity'}), STATUS_CODE['BAD_REQUEST']
            
            cursor.execute('''
                UPDATE stock
                SET stock_quantidade = ?
                WHERE fk_produto_id = (SELECT produto_id FROM produto WHERE produtoNome = ?)
            ''', (quantity, product))
        connection.commit()

    cursor.close()
    connection.close()

    return jsonify({'success_message': 'Stock updated successfully'}), STATUS_CODE['SUCCESS']

@app.route('/api/create_user', methods=['POST'])
@verify_token
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

    stock = {}

    for produto in stock_db:
        produto_stock = {
            'quantidade': produto[1],
            'preco': produto[2]
        }
        stock.update({produto[0]: produto_stock})

    return jsonify({'stock': stock}), STATUS_CODE['SUCCESS']

@app.route('/api/fetch_price', methods=['GET'])
def fetch_price() -> jsonify:
    connection = create_connection()
    if connection is None:
        return jsonify({'error_message': 'Database connection failed'}), STATUS_CODE['INTERNAL_SERVER_ERROR']
    
    cursor = connection.cursor()
    cursor.execute("""
        SELECT
            produto.produto_nome,
            tabelaPrecos.tabelaPrecos_Unit
        FROM
            produto
        JOIN
            tabelaPrecos ON produto.produto_id = tabelaPrecos.fk_produto;
    """)
    price_db = cursor.fetchall()
    cursor.close()

    price = {}

    for produto in price_db:
        produto_price = {
            'preco': produto[1],
        }
        price.update({produto[0]: produto_price})

    return jsonify({'price': price}), STATUS_CODE['SUCCESS']

# PROTECTED ROUTES #

@app.route('/api/protected', methods=['GET'])
@jwt_required()
def protected() -> jsonify:
    current_user = get_jwt_identity()
    return jsonify({'logged_in_as': current_user}), STATUS_CODE['SUCCESS']

if __name__ == '__main__':
    app.run(debug=True, port=5020) # Different port than the client