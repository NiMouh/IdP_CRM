from functools import wraps
import os
from sqlite3 import Error, connect
from flask import request, make_response, redirect, render_template
import time
import jwt
import json
from jwt.algorithms import RSAAlgorithm
import requests

DATABASE_RELATIVE_PATH = 'database/db.sql'
DATABASE_PATH = os.path.join(os.path.dirname(__file__), DATABASE_RELATIVE_PATH)

JWKS_URL = 'http://127.0.0.1:5010/.well-known/jwks.json'

IDP_URL_REFRESH_TOKEN = 'http://127.0.0.1:5010/refresh'
IDP_URL_REVOKE_TOKEN = 'http://127.0.0.1:5010/revoke'
RESOURCE_SERVER = 'http://127.0.0.1:5020'

CLIENTS = { # Host : Client ID
    '127.0.0.1:5000': 'client_id',
    '127.0.0.1:5001': 'client_id2',
    '127.0.0.1:5002': 'client_id3'
}

STATUS_CODE = {
    'SUCCESS': 200,
    'BAD_REQUEST': 400,
    'UNAUTHORIZED': 401,
    'FORBIDDEN': 403,
    'NOT_FOUND': 404,
    'INTERNAL_SERVER_ERROR': 500
}

AUTHENTICATION_PATHS = ['/login', '/', '/logout', '/authorize']

def create_connection() -> connect:
    try:
        conn = connect(DATABASE_PATH, check_same_thread=False)
        return conn
    except Error as e:
        print("Erro ao conectar ao banco de dados:",e)
        return None

def get_public_key() -> bytes:
    response = requests.get(JWKS_URL)
    if response.status_code != STATUS_CODE['SUCCESS']:
        return b''

    jwks = response.json()
    if 'keys' not in jwks or len(jwks['keys']) == 0:
        return b''

    key = jwks['keys'][0]
    if 'kty' not in key or key['kty'] != 'RSA':
        return b''
    
    public_key = RSAAlgorithm.from_jwk(json.dumps(key))
    return public_key

class TokenRefresher:
    def __init__(self, app):
        self.app = app
        self.app.before_request(self.check_token)

    def check_token(self):

        if request.path in AUTHENTICATION_PATHS:
            return None

        access_token = request.cookies.get('access_token')
        refresh_token = request.cookies.get('refresh_token')

        if access_token:
            host = request.host  # Accessing request context here

            if self.token_expired(access_token):
                new_access_token, refresh_token = self.refresh_token(refresh_token, host)
                if new_access_token is not None:
                    response = make_response(redirect(request.path))
                    response.set_cookie('access_token', new_access_token, httponly=True, secure=True)
                    response.set_cookie('refresh_token', refresh_token, httponly=True, secure=True)
                    return response
                else:
                    return self.clear_cookies()
        else:
            return redirect('/login')

    def token_expired(self, access_token):
        if access_token:
            try:
                public_key = get_public_key()
                if public_key is None:
                    return True
                token_decoded = jwt.decode(access_token, public_key, audience=RESOURCE_SERVER, algorithms=['RS256'])
                return token_decoded.get('exp') < int(time.time())
            except jwt.ExpiredSignatureError:
                return True
            except jwt.InvalidTokenError:
                return True
        return False

    def refresh_token(self, refresh_token : str, host : str):
        if refresh_token:
            try:
                public_key = get_public_key()
                if not public_key:
                    return None, None
                token_decoded = jwt.decode(refresh_token, public_key, audience=RESOURCE_SERVER, algorithms=['RS256'])
                if token_decoded.get('exp') < int(time.time()):
                    return None, None
            except jwt.ExpiredSignatureError:
                self.revoke_refresh_token(refresh_token, host)
                return None, None
            except jwt.InvalidTokenError:
                return None, None

            payload = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': CLIENTS.get(host),
                'username': token_decoded.get('username'),
            }
            try:
                response = requests.post(IDP_URL_REFRESH_TOKEN, data=payload)
                response.raise_for_status()
                token = response.json()
                return token.get('access_token'), token.get('refresh_token')
            except requests.exceptions.HTTPError:
                return None, None
        return None, None

    def revoke_refresh_token(self, refresh_token, host):
        payload = {
            'token': refresh_token,
            'client_id': CLIENTS.get(host)
        }
        try:
            response = requests.post(IDP_URL_REVOKE_TOKEN, data=payload)
            response.raise_for_status()
            return True
        except requests.exceptions.HTTPError:
            return False
    
    def clear_cookies(self):
        response = make_response(redirect('/'))
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        response.delete_cookie('username')
        return response

def get_user(token : str):
    if token:
        try:
            public_key = get_public_key()
            if public_key is None:
                return None
            token_decoded = jwt.decode(token, public_key,  audience='http://127.0.0.1:5020', algorithms=['RS256'])
            return token_decoded.get('username')
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    return None

def get_user_role(username : str):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT nivel_acesso_nome FROM utilizador u JOIN nivel_acesso n ON u.fk_nivel_acesso = n.nivel_acesso_id WHERE utilizador_nome = ?", (username,))
    role = cursor.fetchone()
    cursor.close()
    connection.close()
    return role

def check_permission(roles: list):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            access_token = request.cookies.get('access_token')

            if access_token is None:
                return render_template('401.html'), STATUS_CODE['UNAUTHORIZED']
            
            # Obter do access token do utilizador
            username = get_user(access_token)

            if username is None:
                return render_template('401.html'), STATUS_CODE['UNAUTHORIZED']
            
            user_role = get_user_role(username)

            if user_role[0] is None:
                return render_template('401.html'), STATUS_CODE['UNAUTHORIZED']
            if user_role[0] not in roles:
                return render_template('403.html'), STATUS_CODE['FORBIDDEN']

            return func(*args, **kwargs)
        return wrapper
    return decorator



