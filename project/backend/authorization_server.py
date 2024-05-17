from hashlib import sha256
from flask import Flask, json, request, jsonify, redirect, render_template
from secrets import token_urlsafe
from datetime import timedelta,datetime
from sqlite3 import connect, Error
import logging
import jwt
import os


app = Flask(__name__, template_folder="templates")
app.secret_key = token_urlsafe(32) # 32 bytes = 256 bits

STATUS_CODE = {
    'SUCCESS': 200,
    'BAD_REQUEST': 400,
    'UNAUTHORIZED': 401,
    'NOT_FOUND': 404,
    'INTERNAL_SERVER_ERROR': 500
}

DATABASE_RELATIVE_PATH = r'./database/db.sql'
DATABASE_PATH = os.path.abspath(DATABASE_RELATIVE_PATH)


def create_connection() -> connect:
    try:
        conn = connect(DATABASE_PATH, check_same_thread=False)
        return conn
    except Error as e:
        print(e)
        return None

def fetch_users() -> dict:
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT utilizador_nome,utilizador_password FROM utilizador")
    users = { username: password for username, password in cursor.fetchall() }
    cursor.close()
    return users

def fetch_clients() -> dict:
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT 
                        client_application_client_id,client_application_secret 
                    FROM 
                        client_application''')
    clients = { client_id: client_secret for client_id, client_secret in cursor.fetchall() }
    cursor.close()
    return clients

def fetch_authorization_codes() -> dict:
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT 
            authorization_code.authorization_code_code,
            client_application.client_application_client_id,
            utilizador.utilizador_nome
        FROM 
            authorization_code
        JOIN 
            client_application ON authorization_code.fk_client_application_id = client_application.client_application_id
        JOIN 
            utilizador ON authorization_code.fk_utilizador_id = utilizador.utilizador_id;
    ''')

    authorization_codes = { code: (client_id, username) for code, client_id, username in cursor.fetchall() }

    cursor.close()

    return authorization_codes

def add_authorization_code(authorization_code: str, client_id: str, username: str) -> None:
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT 
                utilizador_id
            FROM 
                utilizador
            WHERE 
                utilizador_nome = ?;
        ''', (username,))
        
        user_result = cursor.fetchone()
        if user_result is None:
            raise ValueError(f"No user found with username: {username}")
        user_id = user_result[0]
        
        cursor.execute('''
            SELECT 
                client_application_id
            FROM 
                client_application
            WHERE 
                client_application_client_id = ?;
        ''', (client_id,))
        
        client_result = cursor.fetchone()
        if client_result is None:
            raise ValueError(f"No client application found with client ID: {client_id}")
        client_id = client_result[0]
        
        cursor.execute('''
            INSERT INTO 
                authorization_code (authorization_code_code, fk_client_application_id, fk_utilizador_id)
            VALUES 
                (?, ?, ?);
        ''', (authorization_code, client_id, user_id))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

def remove_authorization_code(authorization_code: str) -> None:
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT 
                authorization_code_id
            FROM 
                authorization_code
            WHERE 
                authorization_code_code = ?;
        ''', (authorization_code,))
        
        result = cursor.fetchone()
        if result is None:
            raise ValueError(f"No authorization code found with code: {authorization_code}")
        
        cursor.execute('''
            DELETE FROM 
                authorization_code
            WHERE 
                authorization_code_code = ?;
        ''', (authorization_code,))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

def make_nonce() -> str:
    return token_urlsafe(22)

@app.route('/authorize', methods=['GET', 'POST'])
def authorize(): # STEP 2 - Authorization Code Request
    if request.method == 'GET':
        CLIENTS = fetch_clients()

        client_id_received = request.args.get('client_id')
        client_secret_received = request.args.get('client_secret')

        if CLIENTS.get(client_id_received) != client_secret_received:
            logging.error('Invalid client credentials received during authorization request')
            return render_template('error.html', error_message='Invalid client credentials'), STATUS_CODE['UNAUTHORIZED']

        return render_template('login.html', state=request.args.get('state'))
    
    elif request.method == 'POST':
        USERS = fetch_users()

        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            # logging.error('Missing credentials received during authorization request')
            return render_template('login.html', state=request.args.get('state'), error_message='Missing credentials')
        
        hashed_password = sha256(password.encode()).hexdigest()
        
        if username not in USERS or USERS[username] != hashed_password:
            # logging.error('Invalid credentials received during authorization request')
            return render_template('login.html', state=request.args.get('state'), error_message='Invalid credentials')
        
        authorization_code = make_nonce()

        add_authorization_code(authorization_code, request.args.get('client_id'), username)
        
        redirect_uri = request.args.get('redirect_uri')
        # logging.info(f'Authorization code generated for user: {username}')
        return redirect(f'{redirect_uri}?code={authorization_code}&state={request.args.get("state")}')
    
@app.route('/access_token', methods=['POST'])
def access_token() -> jsonify: # STEP 4 - Access Token Grant
    CLIENTS = fetch_clients()

    client_id_received = request.form.get('client_id')
    client_secret_received = request.form.get('client_secret')

    if CLIENTS.get(client_id_received) != client_secret_received:
        # logging.error('Invalid client credentials received during access token request')
        return jsonify({'error_message': 'Invalid client credentials'}), STATUS_CODE['UNAUTHORIZED']

    authorization_code = request.form['code']
    authorization_codes = fetch_authorization_codes()
    if not authorization_code or authorization_code not in authorization_codes:
        # logging.error('Invalid authorization code received during access token request')
        return jsonify({'error_message': 'Invalid authorization code'}), STATUS_CODE['BAD_REQUEST']

    username = authorization_codes[authorization_code][1]
    
    remove_authorization_code(authorization_code)

    token = generate_token(username)

    # logging.info(f'Access token generated for user: {username}')
    return jsonify({'access_token': token, 'token_type': 'Bearer'}), STATUS_CODE['SUCCESS']


def generate_token(username : str) -> str:

    time = (int) (datetime.now().timestamp() + timedelta(minutes=5).total_seconds())

    payload = {
        'username': username,
        'exp': time,
        'iss': 'http://127.0.0.1:5010', # Authorization Server
        'aud': 'http://127.0.0.1:5020' # Resource Server
    }

    return jwt.encode(payload, app.secret_key, algorithm='HS256')
    

if __name__ == '__main__':
    logging.basicConfig(filename='authorization_server_file.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
    app.run(debug=True, port=5010) # Different port than the client