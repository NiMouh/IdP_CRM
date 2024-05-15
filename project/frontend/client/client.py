from flask import Flask, redirect, url_for, render_template, make_response
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

# OAUTH - AUTHORIZATION CODE FLOW  #

oauth = OAuth()
oauth.init_app(app)

oauth.register(
    name='idp',
    client_id='client_id',
    client_secret='123456',
    authorize_url= IDP_AUTHORIZE_URL,
    authorize_params=None,
    access_token_url= IDP_URL_ACCESS_TOKEN,
    access_token_params=None,
    refresh_token_url= None,
    refresh_token_params=None,
    client_kwargs={'scope': 'profile'}
)

@app.route('/login', methods=['GET'])
def login(): # STEP 1 - Authorization Request
    redirect_uri = url_for('authorize', _external=True)
    return oauth.idp.authorize_redirect(redirect_uri, client_secret='123456')

@app.route('/authorize')
def authorize(): # STEP 3 - Access Token Request
    token = oauth.idp.authorize_access_token(client_id='client_id', client_secret='123456')

    if 'error_message' in token:
        return redirect('/')

    access_token = token['access_token']

    response = make_response(redirect('/'))
    response.set_cookie('access_token', access_token, httponly=True, secure=True)

    return response

# ROUTES #
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True, port=5000)