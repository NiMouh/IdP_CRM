from functools import wraps
import os
from sqlite3 import Error, connect
from flask import Flask, jsonify, request
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
        raise Exception(f"Failed to fetch JWKS: {response.status_code}")

    jwks = response.json()
    if 'keys' not in jwks or len(jwks['keys']) == 0:
        raise Exception("No keys found in JWKS")

    key = jwks['keys'][0]
    public_key = RSAAlgorithm.from_jwk(json.dumps(key))
    return public_key

SECRET_KEY = get_public_key()

#fazer decode do token para obter o utilizador
def get_user(token):
    print(token)
    if token:
        try:
            token_decoded = jwt.decode(token, SECRET_KEY,  audience='http://127.0.0.1:5020', algorithms=['RS256'])
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
    print(roles)
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            access_token = request.cookies.get('access_token')
            if access_token is None:
                return jsonify({"message": "No access token provided"}), 403
            print('access token:',access_token)
            #obter do access toke o utilizador
            username = get_user(access_token)
            print(username)
            if username is None:
                return jsonify({"message": "No username provided"}), 403
            user_role = get_user_role(username)
            print(user_role[0])
            if user_role[0] is None:
                return jsonify({"message": "No role found"}), 403
            if user_role[0] not in roles:
                return jsonify({"message": "Unauthorized"}), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator



