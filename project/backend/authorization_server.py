from flask import Flask, request, jsonify, redirect, render_template
from secrets import token_urlsafe
from datetime import timedelta
import jwt


app = Flask(__name__)
app.config['SECRET_KEY'] = token_urlsafe(32) # 32 bytes = 256 bits

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

def make_nonce() -> str:
    return token_urlsafe(22)

@app.route('/authorize', methods=['GET', 'POST'])
def authorize(): # STEP 2 - Authorization Code Request
    if request.method == 'GET': # Render the login page
        return render_template('login.html')
    elif request.method == 'POST': 
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return jsonify({'error_message': 'Missing credentials'}), STATUS_CODE['BAD_REQUEST']
        
        if username not in users:
            return jsonify({'error_message': 'Invalid credentials'}), STATUS_CODE['UNAUTHORIZED']
        
        if users[username]['password'] != password:
            return jsonify({'error_message': 'Invalid credentials'}), STATUS_CODE['UNAUTHORIZED']
        
        authorization_code = make_nonce()
        
        redirect_uri = request.headers.get('redirect_uri')

        return redirect(f'{redirect_uri}?code={authorization_code}')

@app.route('/token', methods=['POST'])
def token():
    grant_type = request.form.get('grant_type')
    if grant_type != 'authorization_code':
        return jsonify({'error_message': 'Invalid grant type'}), STATUS_CODE['BAD_REQUEST']
    
    authorization_code = request.form.get('code')
    if not authorization_code:
        return jsonify({'error_message': 'Missing authorization code'}), STATUS_CODE['BAD_REQUEST']
    
    redirect_uri = request.form.get('redirect_uri')
    if not redirect_uri:
        return jsonify({'error_message': 'Missing redirect uri'}), STATUS_CODE['BAD_REQUEST']
    
    # Generate the token
    username = request.form.get('username')
    token = generate_token(username)

    return jsonify({'access_token': token, 'token_type': 'Bearer'}), STATUS_CODE['SUCCESS']

def generate_token(username : str) -> str:

    time = (int) (timedelta(minutes=15).total_seconds())

    payload = {
        'username': username,
        'exp': time,
        'iss': 'http://127.0.0.1:5010',
        'aud': 'idp-crm'
    }

    return jwt.encode(payload, app.secret_key, algorithm='HS256')

def token_required(f):
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error_message': 'Token is missing'}), STATUS_CODE['UNAUTHORIZED']
        
        try:
            jwt.decode(token, app.secret_key, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error_message': 'Token is expired'}), STATUS_CODE['UNAUTHORIZED']
        except jwt.InvalidTokenError:
            return jsonify({'error_message': 'Token is invalid'}), STATUS_CODE['UNAUTHORIZED']
        
        return f(*args, **kwargs)
    
    return decorated
    
@app.route('/admin', methods=['GET'])
@token_required
def admin():

    # Verify if the user is an admin
    token = request.headers.get('Authorization')
    username = jwt.decode(token, app.secret_key, algorithms=['HS256'])['username'] # Get the username from the token

    role = users[username]['role']
    if role != 'admin':
        return jsonify({'error_message': 'Unauthorized'}), STATUS_CODE['UNAUTHORIZED']

    return jsonify({'message': 'Hello Admin!'})


if __name__ == '__main__':
    app.run(debug=True, port=5010) # Different port than the client