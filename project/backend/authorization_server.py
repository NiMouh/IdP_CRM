from hashlib import sha256
from flask import Flask, request, jsonify, redirect, render_template
from secrets import token_urlsafe
from datetime import timedelta,datetime
from sqlite3 import connect, Error
from Crypto.PublicKey import RSA
from pyotp import TOTP
import qrcode
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import jwt
import os
from io import BytesIO
import base64

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

PRIVATE_KEY_PATH = os.path.abspath('./keys/private_key.pem')
PUBLIC_KEY_PATH = os.path.abspath('./keys/public_key.pem')

SENDER_EMAIL = 'crmiaa0@gmail.com'
SENDER_PASSWORD = 'jfuaslvbkfjpiqxn'

SUCCESS_LOG = 'INFO'
ERROR_LOG = 'ERROR'

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
                        u.utilizador_nome, u.utilizador_password, u.utilizador_salt, n.nivel_acesso_nivel, u.utilizador_email
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
        users[user[0]] = {'password': user[1], 'salt': user[2], 'access_level': user[3], 'email': user[4]}
 
    cursor.close()
    return users

def fetch_clients() -> dict:
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT 
                        client_application_client_id,client_application_secret, client_application_redirect_uri 
                    FROM 
                        client_application''')
    client_db = cursor.fetchall()
    clients = {}
    for client in client_db:
        clients[client[0]] = {'secret': client[1], 'redirect_uri': client[2]}
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

def add_log(log_type : str, log_date : datetime, log_message : str, username : str, ip : str, access_level : str, segmentation : str) -> None:

    log_date_str = log_date.strftime('%Y-%m-%d %H:%M:%S')

    conn = create_connection()
    print("Connection created")
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO 
                log (log_tipo, log_data, log_mensagem, log_username, log_ip, log_nivel_acesso, log_segmentacao)
            VALUES 
                (?, ?, ?, ?, ?, ?, ?);
        ''', (log_type, log_date_str, log_message, username, ip, access_level, segmentation))
        print("Log added")
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

def fetch_logs() -> list:

    conn = create_connection()

    if conn is None:
        return []

    cursor = conn.cursor()
    cursor.execute('''
        SELECT log_tipo, log_data, log_mensagem, log_username, log_ip, log_nivel_acesso, log_segmentacao
        FROM log
        ORDER BY log_data DESC
    ''')
    logs = cursor.fetchall()

    cursor.close()

    return logs

# AUTHENTICATION STUFF #

# TOTP #

def generate_otp(seed: str, email_address: str) -> bool:
    try:
        totp_code, uri = create_totp(seed, email_address)
        image_buffer = generate_qr_code(uri)
        message = create_email(email_address, totp_code, image_buffer)
        send_email(message)
        return True
    except Exception as e:
        print(f'Failed to generate OTP: {e}')
        return False

def create_totp(seed: str, email_address: str):
    totp = TOTP(seed)
    totp_code = totp.now()
    uri = totp.provisioning_uri(name=email_address, issuer_name='CRM IAA')
    return totp_code, uri

def generate_qr_code(uri: str) -> BytesIO:
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(uri)
    qr.make(fit=True)
    
    # Store the QR code image in a bytes buffer
    image_buffer = BytesIO()
    image = qr.make_image(fill='black', back_color='white')
    image.save(image_buffer)
    image_buffer.seek(0)  # Rewind the buffer
    return image_buffer

def create_email(recipient_email: str, totp_code: str, img_buffer: BytesIO) -> MIMEMultipart:
    message = MIMEMultipart()
    message['From'] = SENDER_EMAIL
    message['To'] = recipient_email
    message['Subject'] = '2FA - CRM IAA'

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eaeaea; border-radius: 10px;">
            <h2 style="color: #0056b3; text-align: center;">Verification Code</h2>
            <p>Dear User,</p>
            <p>We are pleased to provide you with your OTP code. Please use the code below to complete your verification process:</p>
            <div style="text-align: center; font-size: 24px; font-weight: bold; margin: 20px 0;">{totp_code}</div>
            <p>Alternatively, you can scan the QR code below using an authenticator app such as Google Authenticator, Authy, or any other compatible app:</p>
            <div style="text-align: center; margin: 20px 0;">
                <img src="cid:qrcode.png" alt="QR Code" style="border: 1px solid #eaeaea; padding: 10px; border-radius: 10px;"/>
            </div>
            <p>Thank you for using our service. If you have any questions, feel free to contact our support team.</p>
            <p>Best regards,</p>
            <p style="font-weight: bold;">CRM IAA</p>
            <hr style="border-top: 1px solid #eaeaea;"/>
            <p style="font-size: 12px; color: #999;">This is an automated message, please do not reply. If you need assistance, contact support at support@yourcompany.com.</p>
        </div>
    </body>
    </html>
    """

    message.attach(MIMEText(html_content, 'html'))

    image = MIMEImage(img_buffer.getvalue(), name='qrcode.png')
    image.add_header('Content-ID', '<qrcode.png>')
    message.attach(image)

    return message

def send_email(msg: MIMEMultipart): 
    server = smtplib.SMTP('smtp.gmail.com', 587)  # Example using Gmail SMTP server
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.send_message(msg)
    server.quit()

# RISK EVALUATION #

def risk_based_authentication(ip : str, username : str) -> int:

    counter : int = 0

    is_outside_working_hours = datetime.now().hour >= 18 or datetime.now().hour <= 7
    if is_outside_working_hours:
        counter += 1
    
    connection = create_connection()
    cursor = connection.cursor()

    # If the IP is new, increase the counter
    cursor.execute('''
        SELECT DISTINCT
            log_ip
        FROM
            log
        where
            log_tipo = ? and log_ip = ? and log_username = ?;
    ''', (SUCCESS_LOG, ip, username))

    ip_search_result = cursor.fetchone()
    if ip_search_result is None:
        counter += 1
    else:
        counter = counter

    # If there's less than 5 successful logins in the last 30 days, increase the counter
    cursor.execute('''
        SELECT
            COUNT(*)
        FROM
            log
        WHERE
            log_tipo = ? AND log_username = ? AND log_data >= datetime('now', '-30 days'); 
    ''', (SUCCESS_LOG, username))

    successful_logins = cursor.fetchone()
    if successful_logins[0] < 5:
        counter += 1
    else:
        counter = counter
 
    # If there's more than 3 failed login attempts in the last 5 minutes, increase the counter
    cursor.execute('''
        SELECT
            COUNT(*)
        FROM
            log
        WHERE
            log_tipo = ? AND log_username = ? AND log_data >= datetime('now', '-5 minutes');
    ''', (ERROR_LOG, username))

    failed_logins = cursor.fetchone()
    if failed_logins[0] > 3:
        counter += 1
    else:
        counter = counter
        
    return counter

# SESSION MANAGEMENT #

def make_nonce() -> str:
    return token_urlsafe(22)

@app.route('/2fa', methods=['GET', 'POST'])
def two_factor_authentication():
    if request.method == 'GET':
        CLIENTS = fetch_clients()
        client_id_received = request.args.get('client_id')

        if client_id_received not in CLIENTS:
            print('Caiu aqui')
            return render_template('error.html', error_message='Invalid client credentials'), STATUS_CODE['UNAUTHORIZED']
        
        return render_template('otp.html', client_id=client_id_received, redirect_uri=request.args.get('redirect_uri'), state=request.args.get('state'), username=request.args.get('username'), error_message=None)

    elif request.method == 'POST':
        CLIENTS = fetch_clients()
        client_id_received = request.form.get('client_id')
        username = request.form.get('username')
        otp = ''.join(request.form.getlist('otp'))

        if client_id_received not in CLIENTS:
            return render_template('error.html', error_message='Invalid client credentials'), STATUS_CODE['UNAUTHORIZED']
        
        USERS = fetch_users()
        seed = USERS[username]['salt'].encode()
        seedBase32 = base64.b32encode(seed).decode('utf-8')
        totp = TOTP(seedBase32)

        if not totp.verify(otp):
            return render_template('otp.html', client_id=client_id_received, redirect_uri=request.form.get('redirect_uri'), state=request.form.get('state'), username=username, error_message='Invalid code')
        
        authorization_code = make_nonce()
        add_authorization_code(authorization_code, client_id_received, username)
        return redirect(f'{request.form.get("redirect_uri")}?code={authorization_code}&state={request.form.get("state")}')

@app.route('/resend_otp/<string:username>', methods=['POST'])
def resend_otp(username: str):
    USERS = fetch_users()
    seed = USERS[username]['salt'].encode()
    seedBase32 = base64.b32encode(seed).decode('utf-8')
    email_address = USERS[username]['email']
    generate_otp(seedBase32, email_address)
    return redirect('/2fa')

@app.route('/authorize', methods=['GET', 'POST'])
def authorize(): # STEP 2 - Authorization Code Request
    if request.method == 'GET':
        CLIENTS = fetch_clients()

        client_id_received = request.args.get('client_id')
        client_secret_received = request.args.get('client_secret')

        if client_id_received not in CLIENTS or CLIENTS[client_id_received]['secret'] != client_secret_received:
            return render_template('error.html', error_message='Invalid client credentials'), STATUS_CODE['UNAUTHORIZED']

        return render_template('login.html', state=request.args.get('state'))
    
    elif request.method == 'POST':
        USERS = fetch_users()
        CLIENTS = fetch_clients()

        request_ip = request.remote_addr
        client_id_received, client_secret_received, redirect_uri = request.args.get('client_id'), request.args.get('client_secret'), request.args.get('redirect_uri')
        
        if client_id_received not in CLIENTS or CLIENTS[client_id_received]['secret'] != client_secret_received or CLIENTS[client_id_received]['redirect_uri'] != redirect_uri:
            add_log(ERROR_LOG, datetime.now(), 'Invalid client credentials', 'None', request_ip, 'None', 'Authorization')
            return render_template('error.html', error_message='Invalid client credentials'), STATUS_CODE['UNAUTHORIZED']

        username, password = request.form['username'], request.form['password']

        if not username or not password:
            add_log(ERROR_LOG, datetime.now(), 'Missing credentials', 'None', request_ip, 'None', 'Authorization')
            return render_template('login.html', state=request.args.get('state'), error_message='Missing credentials')
        
        if username not in USERS:
            add_log(ERROR_LOG, datetime.now(), 'Invalid credentials', username, request_ip, 'None', 'Authorization')
            return render_template('login.html', state=request.args.get('state'), error_message='Invalid credentials')
        
        hashed_password = sha256(password.encode() + USERS[username]['salt'].encode()).hexdigest()
        if USERS[username]['password'] != hashed_password:
            add_log(ERROR_LOG, datetime.now(), 'Invalid credentials', username, request_ip, 'None', 'Authorization')
            return render_template('login.html', state=request.args.get('state'), error_message='Invalid credentials')
        
        risk_score = risk_based_authentication(request_ip, username)
        if risk_score >= 0:
            seed = USERS[username]['salt']
            seedBase32 = base64.b32encode(seed.encode()).decode('utf-8')
            email_address = USERS[username]['email']
            print(f'email_address: {email_address}')
            generate_otp(seedBase32, email_address)
            return redirect(f'/2fa?client_id={client_id_received}&redirect_uri={redirect_uri}&state={request.args.get("state")}&username={username}')
        
        authorization_code = make_nonce()

        add_authorization_code(authorization_code, request.args.get('client_id'), username)

        add_log(SUCCESS_LOG, datetime.now(), 'Access granted', username, request_ip, USERS[username]['access_level'], 'Authorization')
        return redirect(f'{redirect_uri}?code={authorization_code}&state={request.args.get("state")}')
    
@app.route('/access_token', methods=['POST'])
def access_token() -> jsonify: # STEP 4 - Access Token Grant
    CLIENTS = fetch_clients()

    client_id_received = request.form.get('client_id')
    client_secret_received = request.form.get('client_secret')

    if client_id_received not in CLIENTS or CLIENTS[client_id_received]['secret'] != client_secret_received:
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

    return jsonify({'access_token': f'{token}'}), STATUS_CODE['SUCCESS']

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

@app.route('/.well-known/jwks.json', methods=['GET'])
def jwks() -> jsonify:
    if not os.path.exists(PUBLIC_KEY_PATH):
        return jsonify({'error_message': 'Public key not found'}), STATUS_CODE['NOT_FOUND']

    try:
        with open(PUBLIC_KEY_PATH, 'rb') as file:
            public_key_pem = file.read()

        public_key = RSA.import_key(public_key_pem)

        n = base64.urlsafe_b64encode(public_key.n.to_bytes((public_key.n.bit_length() + 7) // 8, 'big')).decode('utf-8').rstrip('=')
        e = base64.urlsafe_b64encode(public_key.e.to_bytes((public_key.e.bit_length() + 7) // 8, 'big')).decode('utf-8').rstrip('=')

        jwks = {
            "keys": [
                {
                    "kty": "RSA",
                    "kid": "authorization-server-key",
                    "use": "sig",
                    "alg": "RS256",
                    "n": n,
                    "e": e
                }
            ]
        }

        return jsonify(jwks), STATUS_CODE['SUCCESS']

    except Exception as e:
        return jsonify({'error_message': str(e)}), STATUS_CODE['NOT_FOUND']

if __name__ == '__main__':
    app.run(debug=True, port=5010) # Different port than the client