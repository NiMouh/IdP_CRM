from hashlib import sha256
import random
import string
from flask import Flask, request, jsonify, redirect, render_template, session
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
from twilio.rest import Client
import re

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

RESOURCE_SERVER_URL = 'http://127.0.0.1:5020'
AUTHORIZATION_SERVER_URL = 'http://127.0.0.1:5010'

PRIVATE_KEY_PATH = os.path.abspath('./keys/private_key.pem')
PUBLIC_KEY_PATH = os.path.abspath('./keys/public_key.pem')

# For the OTP service
SENDER_EMAIL = 'crmiaa0@gmail.com'
SENDER_PASSWORD = 'jfuaslvbkfjpiqxn'
TOTP_INTERVAL_SECONDS = 90

# For the Challenge-Response service
SENDER_SMS_ACCOUNT_SID = 'AC89f729d31cdda7a33b7d03a22f4f7577'
SENDER_SMS_AUTH_TOKEN = '1883fa4946a1feacf7f83db0785e97c5'
SENDER_SMS_NUMBER = '+13365305137'

# For the logs
SUCCESS_LOG = 'AUTHENTICATION_INFO'
ERROR_LOG = 'AUTHENTICATION_ERROR'

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
                        u.utilizador_nome, u.utilizador_password, u.utilizador_salt, n.nivel_acesso_nome, u.utilizador_email, u.utilizador_telemovel
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
        users[user[0]] = {'password': user[1], 'salt': user[2], 'access_level': user[3], 'email': user[4], 'telemovel': user[5]}
 
    cursor.close()
    return users

def fetch_user(username : str) -> dict:
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT 
                        u.utilizador_nome, u.utilizador_salt, n.nivel_acesso_nivel, u.utilizador_email, u.utilizador_telemovel
                   FROM 
                        utilizador u
                   JOIN 
                        nivel_acesso n
                   ON
                        u.fk_nivel_acesso = n.nivel_acesso_id
                   WHERE
                        u.utilizador_nome = ?;
    ''', (username,))
    user_db = cursor.fetchone()
    user = {
        'username': user_db[0],
        'salt': user_db[1],
        'access_level': user_db[2],
        'email': user_db[3],
        'telemovel': user_db[4]
    }
    cursor.close()
    return user

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

    return access_level[0]

def fetch_all_access_levels() -> dict:
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT nivel_acesso_nome, nivel_acesso_nivel FROM nivel_acesso')
    access_levels_db = cursor.fetchall()
    access_levels = {}
    for name, level in access_levels_db:
        level = str(level)
        if level not in access_levels:
            access_levels[level] = set()
        access_levels[level].add(name)
    cursor.close()
    return access_levels

def fetch_risk_thresholds() -> dict:
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT risco_nome, risco_valor FROM risco')
    risk_thresholds_db = cursor.fetchall()
    risk_thresholds = {}
    for name, value in risk_thresholds_db:
        risk_thresholds[name] = value
    cursor.close()
    return risk_thresholds

def add_log(log_type : str, log_date : datetime, log_message : str, username : str, ip : str, access_level : str, segmentation : str) -> None:

    if log_type not in [SUCCESS_LOG, ERROR_LOG] or not log_date or not log_message or not ip or not access_level or not segmentation:
        raise ValueError("Invalid log parameters")

    log_date_str = log_date.strftime('%Y-%m-%d %H:%M:%S')

    conn = create_connection()
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

# Challenge-Response w/ OTP #

def generate_challenge() -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

def send_sms(to: str, message: str):
    if not re.match(r'^\+351\d{9}$', to):
        raise ValueError(f'Invalid phone number format: {to}')
    
    client = Client(SENDER_SMS_ACCOUNT_SID, SENDER_SMS_AUTH_TOKEN)
    try:
        message = client.messages.create(
            body=message,
            from_=SENDER_SMS_NUMBER,
            to=to
        )
    except Exception as e:
        print(f"Failed to send SMS: {e}")
        raise

def generate_sms_code(to : str) -> str:
    code = ''.join(random.choices(string.digits, k=6))
    send_sms(to, f'Your verification code is {code}')
    return code

def start_challenge(username: str, phone : str) -> str:
    challenge = generate_challenge()
    code = generate_sms_code(phone)
    save_challenge_code(challenge, code, username)
    return challenge

def save_challenge_code(challenge_code : str, authentication_code : str, username : str) -> None:

    if not challenge_code or not authentication_code:
        raise ValueError('Challenge code and authentication code must be provided')
    
    challenge_response = sha256(challenge_code.encode() + authentication_code.encode()).hexdigest()

    try:
        connection = connect(DATABASE_PATH)
        cursor = connection.cursor()
        cursor.execute('INSERT INTO challenge(challenge_response, fk_utilizador_id) VALUES (?, (SELECT utilizador_id FROM utilizador WHERE utilizador_nome = ?))', (challenge_response, username))
        connection.commit()
    except Error as e:
        print(e)

def fetch_challenge_code(username : str) -> str:

    if not username:
        raise ValueError('Username must be provided')
    
    try:
        connection = connect(DATABASE_PATH)
        cursor = connection.cursor()
        cursor.execute('''
            SELECT challenge_response FROM challenge
            JOIN utilizador ON utilizador.utilizador_id = challenge.fk_utilizador_id
            WHERE utilizador.utilizador_nome = ?
            ORDER BY challenge_data DESC
        ''', (username,))
        challenge_code = cursor.fetchone()

        if challenge_code is None:
            return None

        return challenge_code[0]
    except Error as e:
        print(e)
        return None

def remove_challenge_code(username : str) -> None:
    if not username:
        raise ValueError('Username must be provided')
    
    try:
        connection = connect(DATABASE_PATH)
        cursor = connection.cursor()
        cursor.execute('''
            DELETE FROM challenge
            WHERE fk_utilizador_id = (
                SELECT utilizador_id FROM utilizador
                WHERE utilizador_nome = ?
            )
        ''', (username,))
        connection.commit()
    except Error as e:
        print(e)

def sms_is_verified(challenge : str, response : str, username : str) -> bool:

    db_challenge_response = fetch_challenge_code(username)
    if not db_challenge_response:
        return False
    
    challenge_response = sha256(challenge.encode() + response.encode()).hexdigest()
    
    return challenge_response == db_challenge_response

@app.route('/challenge', methods=['GET', 'POST'])
def sms():
    if request.method == 'GET':
        client_id_received = request.args.get('client_id')

        CLIENTS = fetch_clients()
        if client_id_received not in CLIENTS:
            return render_template('error.html', error_message='Invalid client credentials'), STATUS_CODE['UNAUTHORIZED']
        
        return render_template('challenge.html', client_id=client_id_received, redirect_uri=request.args.get('redirect_uri'), state=request.args.get('state'), username=request.args.get('username'), challenge=request.args.get('challenge'), error_message=None)
    if request.method == 'POST':
        client_id_received = request.form.get('client_id')
        username = request.form.get('username')
        challenge = request.form.get('challenge')
        response = request.form.get('response')
        redirect_uri = request.form.get('redirect_uri')
        state = request.form.get('state')

        CLIENTS = fetch_clients()
        if client_id_received not in CLIENTS:
            return render_template('error.html', error_message='Invalid client credentials'), STATUS_CODE['UNAUTHORIZED']

        if not challenge or not username or not response:
            return render_template('error.html', error_message='Invalid request'), STATUS_CODE['BAD_REQUEST']
        
        USER = fetch_user(username)
        if not sms_is_verified(challenge, response, username):
            remove_challenge_code(username)
            challenge = start_challenge(username, USER['telemovel'])
            return render_template('challenge.html', client_id=client_id_received, redirect_uri=redirect_uri, state=state, username=username, challenge=challenge, error_message='Invalid code')
        
        remove_challenge_code(username)

        seed = USER['salt']
        seed_base32 = base64.b32encode(seed.encode()).decode('utf-8').rstrip('=')
        email_address = USER['email']
        if not generate_otp(seed_base32, email_address):
            return render_template('error.html', error_message='Failed to generate OTP'), STATUS_CODE['INTERNAL_SERVER_ERROR']
        return redirect(f'/2fa?client_id={client_id_received}&redirect_uri={redirect_uri}&state={state}&username={username}')

# Time-Based One-Time Password #

@app.route('/2fa', methods=['GET', 'POST'])
def two_factor_authentication():
    if request.method == 'GET':
        CLIENTS = fetch_clients()
        client_id_received = request.args.get('client_id')

        if client_id_received not in CLIENTS:
            return render_template('error.html', error_message='Invalid client credentials'), STATUS_CODE['UNAUTHORIZED']
        
        return render_template('otp.html', client_id=client_id_received, redirect_uri=request.args.get('redirect_uri'), state=request.args.get('state'), username=request.args.get('username'), error_message=None)

    elif request.method == 'POST':
        CLIENTS = fetch_clients()
        client_id_received = request.form.get('client_id')
        username = request.form.get('username')
        otp = ''.join(request.form.getlist('otp'))

        if not otp or len(otp) != 6:
            return render_template('otp.html', client_id=client_id_received, redirect_uri=request.form.get('redirect_uri'), state=request.form.get('state'), username=username, error_message='Incomplete code')

        if not username:
            return render_template('error.html', error_message='Invalid request'), STATUS_CODE['BAD_REQUEST']

        if client_id_received not in CLIENTS:
            return render_template('error.html', error_message='Invalid client credentials'), STATUS_CODE['UNAUTHORIZED']
        
        if otp_verified(username, otp):
            authorization_code = make_nonce()
            add_authorization_code(authorization_code, client_id_received, username)
            add_log(SUCCESS_LOG, datetime.now(), 'Access granted', username, request.remote_addr, fetch_level_access(username), 'Authorization')
            return redirect(f'{request.form.get("redirect_uri")}?code={authorization_code}&state={request.form.get("state")}')
        else:
            return render_template('otp.html', client_id=client_id_received, redirect_uri=request.form.get('redirect_uri'), state=request.form.get('state'), username=username, error_message='Invalid code')

@app.route('/resend_otp/<string:username>', methods=['POST'])
def resend_otp(username: str):
    if not username:
        return render_template('error.html', error_message='Invalid request'), STATUS_CODE['BAD_REQUEST']

    USER = fetch_user(username)
    seed = USER['salt']
    seed_base32 = base64.b32encode(seed.encode()).decode('utf-8').rstrip('=')
    email_address = USER['email']
    generate_otp(seed_base32, email_address)
    return redirect('/2fa')

def otp_verified(username : str, otp : str) -> bool:
    USER = fetch_user(username)
    seed = USER['salt']
    seed_base32 = base64.b32encode(seed.encode()).decode('utf-8').rstrip('=')
    totp = TOTP(seed_base32, interval=TOTP_INTERVAL_SECONDS)

    return totp.verify(otp)

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
    totp = TOTP(seed, interval=TOTP_INTERVAL_SECONDS)
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

    recipient_name = recipient_email.split('@')[0] # name of the user

    html_content = f"""
    <html>
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
    </head>
    <style>
        img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #eaeaea;
            border-radius: 10px;
        }}

        .code-container {{
            display: flex;
            justify-content: center;
        }}

    </style>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eaeaea; border-radius: 10px;">
            <h2 style="color: #0056b3; text-align: center;">Verification Code</h2>
            <p>Dear {recipient_name},</p>
            <p>We are pleased to provide you with your OTP code. Please use the code below to complete your verification process:</p>
            <div style="text-align: center; font-size: 24px; font-weight: bold; margin: 20px 0;">{totp_code}</div>
            <p>Alternatively, you can scan the QR code below using an authenticator app such as <b>Google Authenticator</b>, <b>Authy</b>, or any other compatible app:</p>
            <div class="code-container">
                <img src="cid:qrcode.png" alt="QR Code"/>
            </div>
            <p>Thank you for using our service. If you have any questions, feel free to contact our support team.</p>
            <p>Best regards,</p>
            <p style="font-weight: bold;">CRM IAA</p>
            <hr style="border-top: 1px solid #eaeaea;"/>
            <p style="font-size: 12px; color: #999;">This is an automated message, please do not reply. If you need assistance, contact support at support@crmiaa.com.</p>
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
 
    # If there's equal or more than 3 failed login attempts in the last 5 minutes, increase the counter
    cursor.execute('''
        SELECT
            COUNT(*)
        FROM
            log
        WHERE
            log_tipo = ? AND log_username = ? AND log_data >= datetime('now', '-5 minutes');
    ''', (ERROR_LOG, username))

    failed_logins = cursor.fetchone()
    if failed_logins[0] >= 3:
        counter += 1
    else:
        counter = counter
        
    return counter

# SESSION MANAGEMENT #

def make_nonce() -> str:
    return token_urlsafe(22)

def password_is_verified(password : str, salt : str, hashed_password : str) -> bool:
    return sha256(password.encode() + salt.encode()).hexdigest() == hashed_password

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
        ACCESS_LEVELS = fetch_all_access_levels()
        RISK_THRESHOLDS = fetch_risk_thresholds()

        request_ip = request.remote_addr
        client_id_received, client_secret_received, redirect_uri = request.args.get('client_id'), request.args.get('client_secret'), request.args.get('redirect_uri')
        state = request.args.get('state')

        if client_id_received not in CLIENTS or CLIENTS[client_id_received]['secret'] != client_secret_received or CLIENTS[client_id_received]['redirect_uri'] != redirect_uri:
            add_log(ERROR_LOG, datetime.now(), 'Invalid client credentials', 'None', request_ip, 'None', 'Authorization')
            return render_template('error.html', error_message='Invalid client credentials'), STATUS_CODE['UNAUTHORIZED']

        username, password = request.form['username'], request.form['password']

        if not username or not password:
            add_log(ERROR_LOG, datetime.now(), 'Missing credentials', 'None', request_ip, 'None', 'Authorization')
            return render_template('login.html', state=state, error_message='Missing credentials')
        
        if username not in USERS:
            add_log(ERROR_LOG, datetime.now(), 'Invalid credentials', username, request_ip, 'None', 'Authorization')
            return render_template('login.html', state=state, error_message='Invalid credentials')
        
        if not password_is_verified(password, USERS[username]['salt'], USERS[username]['password']):
            add_log(ERROR_LOG, datetime.now(), 'Invalid credentials', username, request_ip, 'None', 'Authorization')
            return render_template('login.html', state=state, error_message='Invalid credentials')
        
        risk_score = risk_based_authentication(request_ip, username)

        print("Risk Score: ", risk_score)

        seed = USERS[username]['salt']
        seed_base32 = base64.b32encode(seed.encode()).decode('utf-8').rstrip('=')
        email_address = USERS[username]['email']
        
        print("Access Level: ", USERS[username]['access_level'])

        print("Risk Thresholds: ", RISK_THRESHOLDS)

        # FIXME: Implement the logic for the different access levels
        if USERS[username]['access_level'] in ACCESS_LEVELS['1']:
            print("Access Level 1")
            if risk_score >= RISK_THRESHOLDS['low'] and risk_score < RISK_THRESHOLDS['medium']:
                print("Risk Level: Low - MFA not required")
            elif risk_score >= RISK_THRESHOLDS['medium']:
                print("Risk Level: Medium - OTP required")
                if not generate_otp(seed_base32, email_address):
                    return render_template('error.html', error_message='Failed to generate OTP'), STATUS_CODE['INTERNAL_SERVER_ERROR']
                return redirect(f'/2fa?client_id={client_id_received}&redirect_uri={redirect_uri}&state={state}&username={username}')
        elif USERS[username]['access_level'] in ACCESS_LEVELS['2']:
            print("Access Level 2")
            if risk_score == RISK_THRESHOLDS['low']:
                print("Risk Level: Low - MFA not required")
            elif risk_score > RISK_THRESHOLDS['low'] and risk_score < RISK_THRESHOLDS['medium']:
                print("Risk Level: Medium - OTP required")
                if not generate_otp(seed_base32, email_address):
                    return render_template('error.html', error_message='Failed to generate OTP'), STATUS_CODE['INTERNAL_SERVER_ERROR']
                return redirect(f'/2fa?client_id={client_id_received}&redirect_uri={redirect_uri}&state={state}&username={username}')
            elif risk_score >= RISK_THRESHOLDS['medium']:
                print("Risk Level: High - Challenge and OTP required")
                challenge = start_challenge(username, USERS[username]['telemovel'])
                if not challenge:
                    return render_template('error.html', error_message='Failed to start challenge'), STATUS_CODE['INTERNAL_SERVER_ERROR']
                return redirect(f'/challenge?client_id={client_id_received}&redirect_uri={redirect_uri}&state={state}&username={username}&challenge={challenge}')
        elif USERS[username]['access_level'] in ACCESS_LEVELS['3']:
            print("Access Level 3")
            if risk_score >= RISK_THRESHOLDS['low'] and risk_score < RISK_THRESHOLDS['medium']:
                print("Risk Level: Medium - OTP required")
                if not generate_otp(seed_base32, email_address):
                    return render_template('error.html', error_message='Failed to generate OTP'), STATUS_CODE['INTERNAL_SERVER_ERROR']
                return redirect(f'/2fa?client_id={client_id_received}&redirect_uri={redirect_uri}&state={state}&username={username}')
            elif risk_score >= RISK_THRESHOLDS['medium'] and risk_score < RISK_THRESHOLDS['high']:
                print("Risk Level: High - Challenge AND OTP required")
                challenge = start_challenge(username, USERS[username]['telemovel'])
                if not challenge:
                    return render_template('error.html', error_message='Failed to start challenge'), STATUS_CODE['INTERNAL_SERVER_ERROR']
                return redirect(f'/challenge?client_id={client_id_received}&redirect_uri={redirect_uri}&state={state}&username={username}&challenge={challenge}')
            elif risk_score >= RISK_THRESHOLDS['high']:
                print("Risk Level: Very High - Smartcard required") # FIXME: Implement Smartcard
                return render_template('error.html', error_message='Smartcard required'), STATUS_CODE['UNAUTHORIZED']
        else:
            print("Access Level not found")
            return render_template('error.html', error_message='Access level not found'), STATUS_CODE['INTERNAL_SERVER_ERROR']
        
        authorization_code = make_nonce()
        add_authorization_code(authorization_code, client_id_received, username)
        add_log(SUCCESS_LOG, datetime.now(), 'Access granted', username, request_ip, USERS[username]['access_level'], 'Authorization')
        return redirect(f'{redirect_uri}?code={authorization_code}&state={state}')

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
    refresh_token = generate_refresh_token(username, client_id_received)

    return jsonify({'access_token': f'{token}', 'refresh_token': f'{refresh_token}', 'username' : f'{username}'}), STATUS_CODE['SUCCESS']

# TOKEN GENERATION #
def generate_token(username : str) -> str:

    now = datetime.now()
    access_exp = now + timedelta(minutes=1)
    
    payload_access = {
        'username': username,
        'exp': access_exp.timestamp(),
        'iss': AUTHORIZATION_SERVER_URL,
        'aud': RESOURCE_SERVER_URL,
        'type': 'access'
    }

    private_key = None
    with open(PRIVATE_KEY_PATH, 'r') as file:
        private_key = file.read()

    access_token = jwt.encode(payload_access, private_key, algorithm='RS256')

    return access_token

def generate_refresh_token(username : str, client_id : str) -> str:

    now = datetime.now()
    refresh_exp = now + timedelta(hours=2)

    payload_refresh = {
        'username': username,
        'exp': refresh_exp.timestamp(),
        'iss': AUTHORIZATION_SERVER_URL,
        'aud': RESOURCE_SERVER_URL,
        'type': 'refresh'
    }

    private_key = None
    with open(PRIVATE_KEY_PATH, 'r') as file:
        private_key = file.read()

    refresh_token = jwt.encode(payload_refresh, private_key, algorithm='RS256')

    store_tokens(username, refresh_token, client_id)

    return refresh_token

@app.route('/refresh', methods=['POST'])
def refresh_token() -> jsonify:

    client_id_received = request.form.get('client_id')

    CLIENTS = fetch_clients()
    if client_id_received not in CLIENTS:
        return jsonify({'error_message': 'Invalid client credentials'}), STATUS_CODE['UNAUTHORIZED']

    refresh_token = request.form.get('refresh_token')
    if not refresh_token:
        return jsonify({'error_message': 'Invalid refresh token'}), STATUS_CODE['BAD_REQUEST']
    
    try:
        with open(PUBLIC_KEY_PATH, 'r') as file:
            public_key_pem = file.read()

        payload = jwt.decode(refresh_token, public_key_pem, audience=RESOURCE_SERVER_URL, algorithms=['RS256'])

        if payload['type'] != 'refresh':
            raise jwt.InvalidTokenError('Invalid token type')
        
        username = payload['username']

        connection = create_connection()
        cursor = connection.cursor()

        cursor.execute('''
            SELECT 
                token_refresh
            FROM 
                token
            JOIN 
                utilizador ON token.fk_utilizador_id = utilizador.utilizador_id
            WHERE 
                utilizador.utilizador_nome = ? and token_refresh = ?;
        ''', (username, refresh_token))

        token_record = cursor.fetchone()

        cursor.close()
        connection.close()
        if not token_record:
            return jsonify({'error_message': 'Invalid refresh token'}), STATUS_CODE['BAD_REQUEST']
        
        access_token = generate_token(username)
        refresh_token = generate_refresh_token(username, client_id_received)

        store_tokens(username, refresh_token, client_id_received)

        return jsonify({ 'access_token' : access_token, 'refresh_token' : refresh_token}), STATUS_CODE['SUCCESS']
    except jwt.InvalidTokenError as e:
        return jsonify({'error_message': str(e)}), STATUS_CODE['BAD_REQUEST']

@app.route('/revoke', methods=['POST'])
def revoke_token() -> jsonify:

    client_id_received = request.form.get('client_id')
    CLIENTS = fetch_clients()
    if client_id_received not in CLIENTS:
        return jsonify({'error_message': 'Invalid client credentials'}), STATUS_CODE['UNAUTHORIZED']

    refresh_token = request.form.get('refresh_token')
    if not refresh_token:
        return jsonify({'error_message': 'Invalid refresh token'}), STATUS_CODE['BAD_REQUEST']

    # Remove the refresh token from the database
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute('''
        DELETE FROM
            token
        WHERE
            token_refresh = ?;
    ''', (refresh_token,))

    conn.commit()
    cursor.close()

    return jsonify({'message': 'Token revoked'}), STATUS_CODE['SUCCESS']

def store_tokens(username : str,  refresh_token : str, client_id : str):
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            DELETE FROM 
                token
            WHERE 
                fk_utilizador_id = (SELECT utilizador_id FROM utilizador WHERE utilizador_nome = ?);
        ''', (username,))
        cursor.execute('''
            INSERT INTO 
                token (fk_client_application_id, token_refresh, fk_utilizador_id)
            VALUES 
                ((SELECT client_application_id FROM client_application WHERE client_application_client_id = ?), ?, (SELECT utilizador_id FROM utilizador WHERE utilizador_nome = ?));
        ''', (client_id, refresh_token, username))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error storing tokens: {e}")
    finally:
        cursor.close()
        conn.close()

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