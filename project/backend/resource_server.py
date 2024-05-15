from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
from sqlite3 import connect, Error
from secrets import token_urlsafe
from hashlib import sha256

app = Flask(__name__)
CORS(app) # This will enable all CORS requests

# GLOBAL VARIABLES #

STATUS_CODE = {
    'SUCCESS': 200,
    'BAD_REQUEST': 400,
    'UNAUTHORIZED': 401,
    'NOT_FOUND': 404,
    'INTERNAL_SERVER_ERROR': 500
}

DATABASE_PATH = r'.\database\db.sql'

# DATABASE #

def database_connection() -> connect:
    try:
        connection = connect(DATABASE_PATH)
        return connection
    except Error as error:
        print(error)
        return None

# AUTHENTICATION #

app.config['SECRET_KEY'] = token_urlsafe(32) # 32 bytes = 256 bits
jwt = JWTManager(app)

@app.route('/authenticate', methods=['POST'])
def authenticate() -> jsonify:
    login_data = request.get_json()
    username = login_data.get('username')
    password = login_data.get('password')

    if not username or not password:
        return jsonify({'error_message': 'Missing username or password'}), STATUS_CODE['BAD_REQUEST']
    
    connection = database_connection()
    if connection is None:
        return jsonify({'error_message': 'Connection Failed'}), STATUS_CODE['INTERNAL_SERVER_ERROR']

    cursor = connection.cursor()

    hashed_password = sha256(password.encode()).hexdigest()

    cursor.execute("SELECT utilizador_username,utilizador_password FROM utilizador WHERE utilizador_username = ? AND utilizador_password = ?", (username, hashed_password))
    user = cursor.fetchone()

    cursor.close()

    if user is None:
        return jsonify({'error_message': 'Invalid credentials'}), STATUS_CODE['UNAUTHORIZED']
    
    
    # Create the access token with expiration time of 15 minutes
    expiration_time = timedelta(minutes=15)
    access_token = create_access_token(identity=username, expires_delta=expiration_time)

    return jsonify({'token': access_token}), STATUS_CODE['SUCCESS']

# API #

@app.route('/api/create_user', methods=['POST'])
def create_user() -> jsonify:
    user_data = request.get_json()
    username = user_data.get('username')
    email = user_data.get('email')
    password = user_data.get('password')

    if not username or not password:
        return jsonify({'error_message': 'Missing username or password'}), STATUS_CODE['BAD_REQUEST']
    
    connection = database_connection()
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

@app.route('/api/list_users', methods=['GET'])
def list_users() -> jsonify:
    connection = database_connection()
    if connection is None:
        return jsonify({'error_message': 'Database connection failed'}), STATUS_CODE['INTERNAL_SERVER_ERROR']
    
    cursor = connection.cursor()
    cursor.execute("SELECT utilizador_username FROM utilizador")
    users = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify({'users': users}), STATUS_CODE['SUCCESS']

# PROTECTED ROUTES #

@app.route('/api/protected', methods=['GET'])
@jwt_required()
def protected() -> jsonify:
    current_user = get_jwt_identity()
    return jsonify({'logged_in_as': current_user}), STATUS_CODE['SUCCESS']

if __name__ == '__main__':
    app.run(debug=True, port=5020) # Different port than the client