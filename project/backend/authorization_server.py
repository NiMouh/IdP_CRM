from hashlib import sha256
from flask import Flask, request, jsonify, redirect, render_template
from secrets import token_urlsafe
from datetime import timedelta,datetime
from sqlite3 import connect, Error
import logging
import jwt
import os
import base64

app = Flask(__name__, template_folder="templates")
app.secret_key = token_urlsafe(32) # 32 bytes = 256 bits

# Logging configuration
logging.basicConfig(
    filename='authorization_server_file.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
app.logger.addHandler(console_handler)

# Disable logs from flask
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.disabled = True

STATUS_CODE = {
    'SUCCESS': 200,
    'BAD_REQUEST': 400,
    'UNAUTHORIZED': 401,
    'NOT_FOUND': 404,
    'INTERNAL_SERVER_ERROR': 500
}

DATABASE_RELATIVE_PATH = r'./database/db.sql'
DATABASE_PATH = os.path.abspath(DATABASE_RELATIVE_PATH)

PRIVATE_KEY_PATH = os.path.abspath('./keys/private_key.pem')
PUBLIC_KEY_PATH = os.path.abspath('./keys/public_key.pem')

# DATABASE STUFF #

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
    cursor.execute('''SELECT 
                        u.utilizador_nome, u.utilizador_password, n.nivel_acesso_nome
                   FROM 
                        utilizador u
                   JOIN 
                        nivel_acesso n
                   ON
                        u.fk_nivel_acesso = n.nivel_acesso_id

    ''')
    user_db = cursor.fetchall()
    users = {}
    for user in user_db:
        users[user[0]] = {'password': user[1], 'access_level': user[2]}
 
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

    authorization_codes_db = cursor.fetchall()
    authorization_codes = {}
    for authorization_code in authorization_codes_db:
        authorization_codes[authorization_code[0]] = { 'client_id': authorization_code[1], 'username': authorization_code[2] }

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

def fetch_level_access(username : str) -> str:
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT 
                        nivel_acesso_nivel
                    FROM
                        nivel_acesso
                    JOIN
                        utilizador
                    ON
                        nivel_acesso.nivel_acesso_id = utilizador.fk_nivel_acesso
                    WHERE
                        utilizador_nome = ?;
    ''', (username,))
    access_level = cursor.fetchone()

    cursor.close()

    return access_level

# AUTHENTICATION STUFF #

def make_nonce() -> str:
    return token_urlsafe(22)

def generate_token(username : str) -> str:

    time = (int) (datetime.now().timestamp() + timedelta(minutes=5).total_seconds())

    payload = {
        'username': username,
        'exp': time,
        'iss': 'http://127.0.0.1:5010', # Authorization Server
        'aud': 'http://127.0.0.1:5020' # Resource Server
    }

    with open(PRIVATE_KEY_PATH, 'r') as file:
        private_key = file.read()
        return jwt.encode(payload, private_key, algorithm='RS256') 

def risk_based_authentication() -> int:

    counter : int = 0

    if datetime.now().hour >= 18 or datetime.now().hour <= 7: # Outside working hours
        counter += 1

    # Read the logs
    with open('authorization_server_file.log', 'r') as file:
        logs = file.readlines()
        # TODO: If the IP is new, increase the counter
        # TODO: If there's less than 5 successful logins in the last 30 days, increase the counter
        # TODO: If there's more than 3 failed login attempts in the last 5 minutes, increase the counter
    
    return counter
        

@app.route('/authorize', methods=['GET', 'POST'])
def authorize(): # STEP 2 - Authorization Code Request
    if request.method == 'GET':
        CLIENTS = fetch_clients()

        client_id_received = request.args.get('client_id')
        client_secret_received = request.args.get('client_secret')

        if CLIENTS.get(client_id_received) != client_secret_received:
            #logging.error('Invalid client credentials received during authorization request')
            return render_template('error.html', error_message='Invalid client credentials'), STATUS_CODE['UNAUTHORIZED']

        return render_template('login.html', state=request.args.get('state'))
    
    elif request.method == 'POST':
        USERS = fetch_users()

        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            app.logger.error(f"Missing credentials received during authorization request for user: {username} from IP: {request.remote_addr}, access level: {USERS[username]['access_level']}")
            return render_template('login.html', state=request.args.get('state'), error_message='Missing credentials')
        
        if username not in USERS:
            app.logger.error(f"Invalid credentials received during authorization request for user: {username} from IP: {request.remote_addr}, access level: None")            
            return render_template('login.html', state=request.args.get('state'), error_message='Invalid credentials')
        
        hashed_password = sha256(password.encode()).hexdigest()

        if USERS[username]['password'] != hashed_password:
            app.logger.info(f"Invalid credentials received during authorization request for user: {username} from IP: {request.remote_addr}, access level: {USERS[username]['access_level']}")
            return render_template('login.html', state=request.args.get('state'), error_message='Invalid credentials')
        
        authorization_code = make_nonce()

        add_authorization_code(authorization_code, request.args.get('client_id'), username)
        
        redirect_uri = request.args.get('redirect_uri')
        app.logger.info(f"Login successful for user: {username} from IP: {request.remote_addr}, access level: {USERS[username]['access_level']}")
        return redirect(f'{redirect_uri}?code={authorization_code}&state={request.args.get("state")}')
    
@app.route('/access_token', methods=['POST'])
def access_token() -> jsonify: # STEP 4 - Access Token Grant
    CLIENTS = fetch_clients()

    client_id_received = request.form.get('client_id')
    client_secret_received = request.form.get('client_secret')

    if CLIENTS.get(client_id_received) != client_secret_received:
        return jsonify({'error_message': 'Invalid client credentials'}), STATUS_CODE['UNAUTHORIZED']

    authorization_code = request.form['code']
    authorization_codes = fetch_authorization_codes()
    if not authorization_code or authorization_code not in authorization_codes:
        return jsonify({'error_message': 'Invalid authorization code'}), STATUS_CODE['BAD_REQUEST']
    
    if authorization_codes[authorization_code]['client_id'] != client_id_received:
        return jsonify({'error_message': 'Invalid source client'}), STATUS_CODE['UNAUTHORIZED']

    username = authorization_codes[authorization_code]['username']
    
    remove_authorization_code(authorization_code)

    token = generate_token(username)

    return jsonify({'access_token': f'Bearer {token}'}), STATUS_CODE['SUCCESS']

# JWKS endpoint #
@app.route('/.well-known/jwks.json', methods=['GET'])
def jwks():

    if not os.path.exists(PUBLIC_KEY_PATH):
        return jsonify({'error_message': 'Public key not found'}), STATUS_CODE['NOT_FOUND']

    # Read the public key in binary mode
    public_key_pem = None
    with open(PUBLIC_KEY_PATH, 'rb') as file:
        public_key_pem = file.read()
    
        if public_key_pem is None:
            return jsonify({'error_message': 'Public key not found'}), STATUS_CODE['NOT_FOUND']
    
    # Decode the public key from PEM format
    public_key_der = base64.b64decode(public_key_pem.split(b'\n')[1])

    # Extract modulus (n) and exponent (e) from the RSA public key
    modulus = base64.urlsafe_b64encode(public_key_der[:256]).decode('utf-8')
    exponent = base64.urlsafe_b64encode(public_key_der[256:]).decode('utf-8')

    # Construct the JWKS JSON object with modulus and exponent
    jwks = {
        "keys": [
            {
                "kty": "RSA",
                "kid": "authorization-server-key",
                "use": "sig",
                "alg": "RS256",
                "n": modulus,
                "e": exponent
            }
        ]
    }

    return jsonify(jwks), STATUS_CODE['SUCCESS']

if __name__ == '__main__':
    app.run(port=5010) # Different port than the client