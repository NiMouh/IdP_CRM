import os
from flask import Flask, jsonify, request, render_template
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
from datetime import datetime

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

SUCCESS_LOG = 'ACCESS_INFO'
ERROR_LOG = 'ACCESS_ERROR'

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

# LOGS #

def add_log(log_type : str, log_date : datetime, log_message : str, ip : str, access_level : str, segmentation : str) -> None:

    if log_type not in [SUCCESS_LOG, ERROR_LOG] or not log_date or not log_message or not ip or not access_level or not segmentation:
        raise ValueError("Invalid log parameters")

    log_date_str = log_date.strftime('%Y-%m-%d %H:%M:%S')

    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO 
                log (log_tipo, log_data, log_mensagem, log_ip, log_nivel_acesso, log_segmentacao)
            VALUES 
                (?, ?, ?, ?, ?, ?, ?);
        ''', (log_type, log_date_str, log_message, ip, access_level, segmentation))
        print("Log added")
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

# API #

@app.route('/api/ver_clientes', methods=['GET'])
@verify_token
def show_clients() -> jsonify:
    connection = create_connection()
    if connection is None:
        return render_template('500.html'), STATUS_CODE['INTERNAL_SERVER_ERROR']

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

    add_log(SUCCESS_LOG, datetime.now(), 'Clients fetched successfully', request.remote_addr, 'vendedor', 'clients')
    return jsonify(clientes), STATUS_CODE['SUCCESS']

@app.route('/api/contactos_clientes', methods=['GET'])
@verify_token
def dashboard() -> jsonify:
    connection = create_connection()
    if connection is None:
        add_log(ERROR_LOG, datetime.now(), 'Failed to connect to database', request.remote_addr, 'vendedor', 'contacts')
        return render_template('500.html'), STATUS_CODE['INTERNAL_SERVER_ERROR']
    
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

    add_log(SUCCESS_LOG, datetime.now(), 'Contacts fetched successfully', request.remote_addr, 'vendedor', 'contacts')
    return jsonify(contacts), STATUS_CODE['SUCCESS']
    
@app.route('/api/moradas_clientes', methods=['GET'])
@verify_token
def clients_addresses() -> jsonify:
    connection = create_connection()
    if connection is None:
        add_log(ERROR_LOG, datetime.now(), 'Failed to connect to database', request.remote_addr, 'vendedor', 'addresses')
        return render_template('500.html'), STATUS_CODE['INTERNAL_SERVER_ERROR']
    
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

    add_log(SUCCESS_LOG, datetime.now(), 'Addresses fetched successfully', request.remote_addr, 'vendedor', 'addresses')
    return jsonify(addresses), STATUS_CODE['SUCCESS']

@app.route('/api/contactos_diretor_obra', methods=['GET'])
@verify_token
def contactos_diretor_obra() -> jsonify:
    connection = create_connection()
    if connection is None:
        add_log(ERROR_LOG, datetime.now(), 'Failed to connect to database', request.remote_addr, 'diretor_de_obra', 'contacts')
        return render_template('500.html'), STATUS_CODE['INTERNAL_SERVER_ERROR']
    
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

    add_log(SUCCESS_LOG, datetime.now(), 'Contacts fetched successfully', request.remote_addr, 'diretor_de_obra', 'contacts')
    return jsonify(contacts), STATUS_CODE['SUCCESS']

@app.route('/api/obra_estado', methods=['GET'])
@verify_token
def obra_estado() -> jsonify:
    connection = create_connection()
    if connection is None:
        add_log(ERROR_LOG, datetime.now(), 'Failed to connect to database', request.remote_addr, 'vendedor', 'states')
        return render_template('500.html'), STATUS_CODE['INTERNAL_SERVER_ERROR']
    
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

    add_log(SUCCESS_LOG, datetime.now(), 'States fetched successfully', request.remote_addr, 'vendedor', 'states')
    return jsonify(estados), STATUS_CODE['SUCCESS']

@app.route('/api/morada_obra', methods=['GET'])
@verify_token
def morada_obra() -> jsonify:
    connection = create_connection()
    if connection is None:
        add_log(ERROR_LOG, datetime.now(), 'Failed to connect to database', request.remote_addr, 'vendedor', 'addresses')
        return render_template('500.html'), STATUS_CODE['INTERNAL_SERVER_ERROR']
    
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

    add_log(SUCCESS_LOG, datetime.now(), 'Addresses fetched successfully', request.remote_addr, 'vendedor', 'addresses')
    return jsonify(addresses), STATUS_CODE['SUCCESS']

@app.route('/api/material_obra', methods=['GET'])
@verify_token
def material_obra() -> jsonify:
    connection = create_connection()
    if connection is None:
        add_log(ERROR_LOG, datetime.now(), 'Failed to connect to database', request.remote_addr, 'vendedor', 'materials')
        return render_template('500.html'), STATUS_CODE['INTERNAL_SERVER_ERROR']
    
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

    add_log(SUCCESS_LOG, datetime.now(), 'Materials fetched successfully', request.remote_addr, 'vendedor', 'materials')
    return jsonify(materials), STATUS_CODE['SUCCESS']

@app.route('/api/tabela_preco', methods=['GET'])
@verify_token
def tabela_preco() -> jsonify:
    connection = create_connection()
    if connection is None:
        add_log(ERROR_LOG, datetime.now(), 'Failed to connect to database', request.remote_addr, 'vendedor', 'prices')
        return render_template('500.html'), STATUS_CODE['INTERNAL_SERVER_ERROR']
    
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
        add_log(ERROR_LOG, datetime.now(), 'Failed to connect to database', request.remote_addr, 'vendedor', 'stock')
        return render_template('500.html'), STATUS_CODE['INTERNAL_SERVER_ERROR']
    
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

    add_log(SUCCESS_LOG, datetime.now(), 'Stock fetched successfully', request.remote_addr, 'vendedor', 'stock')
    return jsonify(stock), STATUS_CODE['SUCCESS']

@app.route('/api/stock', methods=['POST', 'DELETE'])
@verify_token
def edit_stock() -> jsonify:

    connection = create_connection()
    if connection is None:
        add_log(ERROR_LOG, datetime.now(), 'Failed to connect to database', request.remote_addr, 'vendedor', 'stock')
        return render_template('500.html'), STATUS_CODE['INTERNAL_SERVER_ERROR']
    cursor = connection.cursor()

    if request.method == 'DELETE':
        product_data = request.get_json()
        product = product_data.get('product')
        
        if not product:
            add_log(ERROR_LOG, datetime.now(), 'Invalid product data', request.remote_addr, 'vendedor', 'stock')
            return render_template('400.html'), STATUS_CODE['BAD_REQUEST']
        
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

        if not stock_data or not isinstance(stock_data, list):
            add_log(ERROR_LOG, datetime.now(), 'Invalid stock data', request.remote_addr, 'vendedor', 'stock')
            return render_template('400.html'), STATUS_CODE['BAD_REQUEST']

        for item in stock_data:
            product = item['product']
            quantity = item['quantity']
            
            if not product or not quantity:
                add_log(ERROR_LOG, datetime.now(), 'Invalid stock data', request.remote_addr, 'vendedor', 'stock')
                return render_template('400.html'), STATUS_CODE['BAD_REQUEST']
            
            cursor.execute('''
                UPDATE stock
                SET stock_quantidade = ?
                WHERE fk_produto_id = (SELECT produto_id FROM produto WHERE produtoNome = ?)
            ''', (quantity, product))
        connection.commit()

    cursor.close()
    connection.close()

    add_log(SUCCESS_LOG, datetime.now(), 'Stock updated successfully', request.remote_addr, 'vendedor', 'stock')
    return jsonify({'success_message': 'Stock updated successfully'}), STATUS_CODE['SUCCESS']

if __name__ == '__main__':
    app.run(debug=True, port=5020) # Different port than the client