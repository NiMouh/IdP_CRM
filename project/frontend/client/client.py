import os
import sys
import requests
from flask import Flask, redirect, url_for, render_template, make_response, request
from secrets import token_urlsafe
from authlib.integrations.flask_client import OAuth
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend'))
sys.path.append(backend_path)

from middleware import check_permission, TokenRefresher

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

CLIENT_ID = 'client_id'
CLIENT_SECRET = '123456'

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

token_refresher = TokenRefresher(app)

# SESSION MANAGEMENT #

@app.route('/login', methods=['GET'])
def login(): # STEP 1 - Authorization Request

    if 'access_token' in request.cookies:
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
    if 'refresh_token' in request.cookies:
        token_refresher.revoke_refresh_token(request.cookies.get('refresh_token'), request.host)
    return token_refresher.clear_cookies()

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

def make_api_get_request(tab: str) -> dict:
    url = RESOURCE_SERVER_URL + '/api/' + tab

    headers = {
        'Authorization': 'Bearer ' + request.cookies.get('access_token')
    }

    response = requests.get(url, headers=headers)
    if response.status_code != STATUS_CODE['SUCCESS']:
        return redirect('/login')
    
    return response.json()

def make_api_post_request(tab: str, payload: dict) -> dict:
    url = RESOURCE_SERVER_URL + '/api/' + tab

    headers = {
        'Authorization': 'Bearer ' + request.cookies.get('access_token')
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != STATUS_CODE['SUCCESS']:
        return redirect('/login')
    
    return response.json()

@app.route('/ver_clientes', methods=['GET'])
@check_permission(['vendedor', 'diretor_telecomunicacoes'])
def ver_clientes():
    if ('access_token' and 'refresh_token') not in request.cookies:
        return redirect('/')
    
    clients = make_api_get_request('ver_clientes')

    return render_template('tables_ver_clients.html', clients=clients, username=request.cookies.get('username'))

@app.route('/obra_estado', methods=['GET'])
@check_permission(['vendedor', 'diretor_telecomunicacoes'])
def obra_estado():
    if ('access_token' and 'refresh_token') not in request.cookies:
        return redirect('/')
    
    estados = make_api_get_request('obra_estado')

    return render_template('tables_obra_estado.html', estados=estados, username=request.cookies.get('username'))

@app.route('/material_obra', methods=['GET'])
@check_permission(['vendedor', 'trabalhador_de_fabrica', 'tecnico_telecomunicacoes', 'diretor_de_obra', 'diretor_telecomunicacoes'])
def material_obra():
    if ('access_token' and 'refresh_token') not in request.cookies:
        return redirect('/')
    
    materials = make_api_get_request('material_obra')

    return render_template('tables_obra_material.html', materials=materials, username=request.cookies.get('username'))

@app.route('/tabela_preco', methods=['GET'])
@check_permission(['vendedor', 'diretor_de_obra', 'fornecedor', 'tecnico_telecomunicacoes', 'diretor_telecomunicacoes'])
def tabela_preco():
    if ('access_token' and 'refresh_token') not in request.cookies:
        return redirect('/')
    
    prices = make_api_get_request('tabela_preco')

    return render_template('tables_obra_preco.html', prices=prices, username=request.cookies.get('username'))

@app.route('/stock', methods=['GET'])
@check_permission(['trabalhador_de_fabrica', 'vendedor'])
def stock():
    if ('access_token' and 'refresh_token') not in request.cookies:
        return redirect('/')
    
    stock = make_api_get_request('stock')

    return render_template('tables_obra_stock.html', stock=stock, username=request.cookies.get('username'))

@app.route('/stock/update', methods=['POST'])
@check_permission(['fornecedor', 'trabalhador_de_fabrica', 'diretor_de_obra'])
def update_stock():
    if ('access_token' and 'refresh_token') not in request.cookies:
        return redirect('/')
    
    products = request.form.getlist('produto')
    quantities = request.form.getlist('quantidade')

    if not products or not quantities or len(products) != len(quantities):
        return redirect('/stock')

    payload = [
        {
            'product': product, 
            'quantity': quantity
        } 
        for product, quantity in zip(products, quantities)]

    response = make_api_post_request('stock', payload)
    response = response.json()

    if response['status'] != STATUS_CODE['SUCCESS']:
        stock = make_api_get_request('stock')
        return render_template('tables_obra_stock.html', stock=stock, username=request.cookies.get('username'), error_message='Erro ao atualizar stock')

    return redirect('/stock')


@app.route('/stock/delete', methods=['POST'])
@check_permission(['fornecedor', 'trabalhador_de_fabrica', 'diretor_de_obra'])
def delete_stock():
    if ('access_token' and 'refresh_token') not in request.cookies:
        return redirect('/')
    
    product = request.form.get('produto_delete')

    url = f'http://127.0.0.1:5020/api/stock'
    headers = {
        'Authorization': 'Bearer ' + request.cookies.get('access_token')
    }

    payload = {
        'product': product
    }

    response = requests.delete(url, headers=headers, json=payload)

    if response.status_code !=  STATUS_CODE['SUCCESS']:
        stock = make_api_get_request('stock')
        return render_template('tables_obra_stock.html', stock=stock, username=request.cookies.get('username'), error_message='Erro ao apagar stock')

    return redirect('/stock')

@app.errorhandler(STATUS_CODE['NOT_FOUND'])
def page_not_found(e):
    return render_template('404.html'), STATUS_CODE['NOT_FOUND']

if __name__ == '__main__':
    app.run(debug=True, port=5000)
