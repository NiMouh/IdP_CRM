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
    
    connection = database_connection()
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
    connection = database_connection()
    if connection is None:
        return jsonify({'error_message': 'Database connection failed'}), STATUS_CODE['INTERNAL_SERVER_ERROR']
    
    cursor = connection.cursor()
    cursor.execute("SELECT utilizador_username FROM utilizador")
    users = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify({'users': users}), STATUS_CODE['SUCCESS']

# TODO: Obtain the address of the all 'clientes' from the database

# TODO: Given the name of the 'colaboradores', obtain the contacts of the 'colaboradores' from the database

# TODO: Given the name of the 'obra', obtain the address of the 'obra' from the database

# TODO: Given the name of the 'obra', obtain the 'material' used in the 'obra' from the database

# TODO: Obtain all the 'material' in stock from the database

# TODO: Given the name 

# PROTECTED ROUTES #

@app.route('/api/protected', methods=['GET'])
@jwt_required()
def protected() -> jsonify:
    current_user = get_jwt_identity()
    return jsonify({'logged_in_as': current_user}), STATUS_CODE['SUCCESS']

if __name__ == '__main__':
    app.run(debug=True, port=5020) # Different port than the client