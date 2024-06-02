from functools import wraps
import os
from sqlite3 import Error, connect
from flask import Flask, jsonify, request, make_response, redirect
import time
import jwt
import json
from jwt.algorithms import RSAAlgorithm
import requests

DATABASE_RELATIVE_PATH = 'database/db.sql'
DATABASE_PATH = os.path.join(os.path.dirname(__file__), DATABASE_RELATIVE_PATH)

def create_connection() -> connect:
    try:
        conn = connect(DATABASE_PATH, check_same_thread=False)
        return conn
    except Error as e:
        print("Erro ao conectar ao banco de dados:",e)
        return None

JWKS_URL = 'http://127.0.0.1:5010/.well-known/jwks.json'

def get_public_key() -> bytes:
    response = requests.get(JWKS_URL)
    if response.status_code != 200:
        return None

    jwks = response.json()
    if 'keys' not in jwks or len(jwks['keys']) == 0:
        return None

    key = jwks['keys'][0]
    if 'kty' not in key or key['kty'] != 'RSA':
        return None

    public_key = RSAAlgorithm.from_jwk(json.dumps(key))
    return public_key

IDP_URL_REFRESH_TOKEN = 'http://127.0.0.1:5010/refresh'
IDP_URL_REVOKE_TOKEN = 'http://127.0.0.1:5010/revoke'
RESOURCE_SERVER = 'http://127.0.0.1:5020'

CLIENTS = { # Host : Client ID
    '127.0.0.1:5000': 'client_id',
    '127.0.0.1:5001': 'client_id2',
    '127.0.0.1:5002': 'client_id3'
}

AUTHENTICATION_PATHS = ['/login', '/', '/logout', '/authorize']

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
                refreshed_token = self.refresh_token(refresh_token, host)  # Passing host to refresh_token
                if refreshed_token:
                    response = make_response(redirect(request.path))
                    response.set_cookie('access_token', refreshed_token, httponly=True, secure=True)
                    return response
                else:
                    response = make_response(redirect('/login'))
                    response.delete_cookie('access_token')
                    response.delete_cookie('refresh_token')
                    response.delete_cookie('username')
                    return response
        else:
            return redirect('/login')

    def token_expired(self, access_token): # Check if the token is 5 minutes from expiring
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

    def refresh_token(self, refresh_token, host):
        if refresh_token:
            try:
                public_key = get_public_key()
                if public_key is None:
                    return None
                token_decoded = jwt.decode(refresh_token, public_key, audience=RESOURCE_SERVER, algorithms=['RS256'])
                if token_decoded.get('exp') < int(time.time()):  # Check if refresh token is expired
                    return None
            except jwt.ExpiredSignatureError: # TODO: If it's expired, revoke it
                self.revoke_refresh_token(refresh_token, host)
                return None
            except jwt.InvalidTokenError:
                return None

            payload = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': CLIENTS.get(host)
            }
            try:
                response = requests.post(IDP_URL_REFRESH_TOKEN, data=payload)
                response.raise_for_status()
                token = response.json()
                return token.get('access_token')
            except requests.exceptions.HTTPError:
                return None
        return None

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

def get_user(token):
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

def get_user_role(username):
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
                return jsonify({"message": "No access token provided"}), 403
            
            # Obter do access token do utilizador
            username = get_user(access_token)

            if username is None:
                return jsonify({"message": "No username provided"}), 403
            
            user_role = get_user_role(username)

            if user_role[0] is None:
                return jsonify({"message": "No role found"}), 403
            if user_role[0] not in roles:
                return jsonify({"message": "Unauthorized"}), 403

            return func(*args, **kwargs)
        return wrapper
    return decorator



