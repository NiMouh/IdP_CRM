import os
import sys
import requests
from flask import Flask, redirect, url_for, render_template, make_response, request
from secrets import token_urlsafe
from authlib.integrations.flask_client import OAuth
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend'))
sys.path.append(backend_path)

from middleware import check_permission

app = Flask(__name__, template_folder="templates")
app.secret_key = token_urlsafe(32) # 32 bytes = 256 bits

STATUS_CODE = {
    'SUCCESS': 200,
    'BAD_REQUEST': 400,
    'UNAUTHORIZED': 401,
    'NOT_FOUND': 404,
    'INTERNAL_SERVER_ERROR': 500
}

IDP_URL_ACCESS_TOKEN = 'http://127.0.0.1:5010/access_token'
IDP_AUTHORIZE_URL = 'http://127.0.0.1:5010/authorize'
IDP_URL_REFRESH_TOKEN = 'http://127.0.0.1:5010/refresh'

RESOURCE_SERVER_URL = 'http://127.0.0.1:5020'

CLIENT_ID = 'client_id2'
CLIENT_SECRET = '123457'

# OAUTH - AUTHORIZATION CODE FLOW  #

oauth = OAuth()
oauth.init_app(app)

oauth.register(
    name='idp',
    client_id= CLIENT_ID,
    client_secret= CLIENT_SECRET,
    authorize_url= IDP_AUTHORIZE_URL,
    authorize_params=None,
    access_token_url= IDP_URL_ACCESS_TOKEN,
    access_token_params=None,
    refresh_token_url= IDP_URL_REFRESH_TOKEN,
    refresh_token_params=None,
    client_kwargs={'scope': 'profile'}
)

# SESSION MANAGEMENT #

@app.route('/login', methods=['GET'])
def login(): # STEP 1 - Authorization Request

    if 'access_token' and 'refresh_token' in request.cookies:
        return redirect('/')

    redirect_uri = url_for('authorize', _external=True)
    return oauth.idp.authorize_redirect(redirect_uri, client_secret=CLIENT_SECRET)

@app.route('/authorize')
def authorize(): # STEP 3 - Access Token Request

    token = oauth.idp.authorize_access_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

    if 'error_message' in token:
        return redirect('/')   

    access_token = token['access_token']
    refresh_token = token['refresh_token']
    username = token['username']


    response = make_response(redirect('/dashboard'))
    response.set_cookie('access_token', access_token, httponly=True, secure=True)
    response.set_cookie('refresh_token', refresh_token, httponly=True, secure=True)
    response.set_cookie('username', username, httponly=True, secure=True)

    return response

@app.route('/logout', methods=['GET'])
def logout():
    response = make_response(redirect('/'))
    response.set_cookie('access_token', '', expires=0)
    response.set_cookie('refresh_token', '', expires=0)
    response.set_cookie('username', '', expires=0)

    return response

# ROUTES #

@app.route('/', methods=['GET'])
def index():
    if 'access_token' and 'refresh_token' in request.cookies:
        return redirect('/dashboard')
    return render_template('index.html')

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if ('access_token' and 'refresh_token') not in request.cookies:
        return redirect('/')
    username = request.cookies.get('username')
    return render_template('dashboard.html', username=username)

# TODO: Implementação de Refresh tokens
@app.route('/refresh', methods=['GET'])
def refresh():
    refresh_token = request.cookies.get('refresh_token')
    if refresh_token is None:
        return redirect('/login')
    
    token_url = IDP_URL_REFRESH_TOKEN
    client_id = CLIENT_ID

    # Prepare the request payload
    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_id
    }

    # Make the request to the token endpoint
    try:
        response = requests.post(token_url, data=payload)
        response.raise_for_status()
        token = response.json()

        access_token = token['access_token']
        
        response = make_response(redirect('/dashboard'))
        response.set_cookie('access_token', access_token, httponly=True, secure=True)
        return response

    except requests.exceptions.HTTPError as e:
        return redirect('/login')

@app.route('/contactos_clientes', methods=['GET'])
@check_permission(['vendedor', 'diretor_de_obra'])
def contactos_clientes():
    if ('access_token' and 'refresh_token') not in request.cookies:
        return redirect('/')
    
    url = 'http://127.0.0.1:5020/api/contactos_clientes'
    headers = {
        'Authorization': 'Bearer ' + request.cookies.get('access_token')
    }
    response = requests.get(url, headers=headers)
    print('Contactos Clientes', response.json())

    if response.status_code != 200:
        return redirect('/login')
    return render_template('tables_clients_contactos.html', contactos=response.json(), username=request.cookies.get('username'))

@app.route('/moradas_clientes', methods=['GET'])
@check_permission(['vendedor', 'diretor_de_obra'])
def moradas_clientes():
    if ('access_token' and 'refresh_token') not in request.cookies:
        return redirect('/')
    
    url = 'http://127.0.0.1:5020/api/moradas_clientes'
    headers = {
        'Authorization': 'Bearer ' + request.cookies.get('access_token')
    }
    response = requests.get(url, headers=headers)
    print('Moradas Clientes', response.json())

    if response.status_code != 200:
        return redirect('/login')
    return render_template('tables_clients_moradas.html', moradas=response.json(), username=request.cookies.get('username'))

@app.route('/morada_obra', methods=['GET'])
@check_permission(['vendedor', 'diretor_de_obra'])
def morada_obra():
    if ('access_token' and 'refresh_token') not in request.cookies:
        return redirect('/')
    
    url = 'http://127.0.0.1:5020/api/morada_obra'
    headers = {
        'Authorization': 'Bearer ' + request.cookies.get('access_token')
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return redirect('/login')
    return render_template('tables_obra_morada.html', addresses=response.json(), username=request.cookies.get('username'))

@app.errorhandler(STATUS_CODE['NOT_FOUND'])
def page_not_found(e):
    return render_template('error.html'), STATUS_CODE['NOT_FOUND']

if __name__ == '__main__':
    app.run(debug=True, port=5001)
