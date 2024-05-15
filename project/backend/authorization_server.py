from flask import Flask, request, jsonify, redirect, render_template
from secrets import token_urlsafe
from datetime import timedelta,datetime
import logging
import jwt


app = Flask(__name__, template_folder="templates")
app.secret_key = token_urlsafe(32) # 32 bytes = 256 bits

STATUS_CODE = {
    'SUCCESS': 200,
    'BAD_REQUEST': 400,
    'UNAUTHORIZED': 401,
    'NOT_FOUND': 404,
    'INTERNAL_SERVER_ERROR': 500
}

users = {
    'utilizador1': {
        'password': 'password1',
        'role': 'admin'
    },
    'utilizador2': {
        'password': 'password2',
        'role': 'user'
    }
}

CLIENTS = {
    'client_id': '123456'
}

authorization_codes = {}

def make_nonce() -> str:
    return token_urlsafe(22)

@app.route('/authorize', methods=['GET', 'POST'])
def authorize(): # STEP 2 - Authorization Code Request
    if request.method == 'GET':

        client_id_received = request.args.get('client_id')
        client_secret_received = request.args.get('client_secret')
        if CLIENTS.get(client_id_received) != client_secret_received:
            # logging.error('Invalid client credentials received during authorization request')
            return render_template('error.html', error_message='Invalid client credentials'), STATUS_CODE['UNAUTHORIZED']

        return render_template('login.html', state=request.args.get('state'))
    
    elif request.method == 'POST': 

        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            # logging.error('Missing credentials received during authorization request')
            return render_template('login.html', state=request.args.get('state'), error_message='Missing credentials')
        
        if username not in users or users[username]['password'] != password:
            # logging.error('Invalid credentials received during authorization request')
            return render_template('login.html', state=request.args.get('state'), error_message='Invalid credentials')
        
        authorization_code = make_nonce()

        global authorization_codes
        authorization_codes[authorization_code] = username
        
        redirect_uri = request.args.get('redirect_uri')
        # logging.info(f'Authorization code generated for user: {username}')
        return redirect(f'{redirect_uri}?code={authorization_code}&state={request.args.get("state")}')
    
@app.route('/access_token', methods=['POST'])
def access_token() -> jsonify: # STEP 4 - Access Token Grant

    # Validate client id and secret
    client_id_received = request.form.get('client_id')
    client_secret_received = request.form.get('client_secret')
    if CLIENTS.get(client_id_received) != client_secret_received:
        # logging.error('Invalid client credentials received during access token request')
        return jsonify({'error_message': 'Invalid client credentials'}), STATUS_CODE['UNAUTHORIZED']

    # Validate auth. code
    authorization_code = request.form.get('code')
    global authorization_codes
    if not authorization_code or not authorization_codes:
        # logging.error('Invalid authorization code received during access token request')
        return jsonify({'error_message': 'Invalid authorization'}), STATUS_CODE['BAD_REQUEST']
    
    # TODO: Verify redirect uri matches the one from the authorization request

    username = authorization_codes[authorization_code]
    
    authorization_codes.pop(authorization_code)

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
    # logging.basicConfig(filename='authorization_server_file.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
    app.run(debug=True, port=5010) # Different port than the client