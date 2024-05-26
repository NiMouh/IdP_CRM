from flask import Flask, redirect, url_for, render_template, make_response, request
from secrets import token_urlsafe
from authlib.integrations.flask_client import OAuth


app = Flask(__name__, template_folder="templates")
app.secret_key = token_urlsafe(32) # 32 bytes = 256 bits

STATUS_CODE = {
    'SUCCESS': 200,
    'BAD_REQUEST': 400,
    'UNAUTHORIZED': 401,
    'NOT_FOUND': 404,
    'INTERNAL_SERVER_ERROR': 500
}

IDP_URL_REQUEST_TOKEN = 'http://127.0.0.1:5010/oauth/request_token'
IDP_URL_ACCESS_TOKEN = 'http://127.0.0.1:5010/access_token'
IDP_AUTHORIZE_URL = 'http://127.0.0.1:5010/authorize'

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
    refresh_token_url= None,
    refresh_token_params=None,
    client_kwargs={'scope': 'profile'}
)

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

    response = make_response(redirect('/dashboard'))
    response.set_cookie('access_token', access_token, httponly=True, secure=True)

    return response

@app.route('/logout', methods=['GET'])
def logout():
    response = make_response(redirect('/'))
    response.set_cookie('access_token', '', expires=0)

    return response

# ROUTES #

@app.route('/', methods=['GET'])
def index():
    if 'access_token' in request.cookies:
        return redirect('/dashboard')
    return render_template('index.html')

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'access_token' not in request.cookies:
        return redirect('/')
    access_token = request.cookies.get('access_token')
    return render_template('dashboard.html', access_token=access_token)

# TODO: Implementação de Refresh tokens

@app.errorhandler(STATUS_CODE['NOT_FOUND'])
def page_not_found(e):
    return render_template('error.html'), STATUS_CODE['NOT_FOUND']

if __name__ == '__main__':
    app.run(debug=True, port=5000)