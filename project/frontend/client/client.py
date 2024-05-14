from flask import Flask, redirect, url_for, session, render_template
from authlib.integrations.flask_client import OAuth
from authlib.integrations.flask_client import OAuthError

app = Flask(__name__, template_folder="templates")
app.secret_key = 'secret_key'

STATUS_CODE = {
    'SUCCESS': 200,
    'BAD_REQUEST': 400,
    'UNAUTHORIZED': 401,
    'NOT_FOUND': 404,
    'INTERNAL_SERVER_ERROR': 500
}

IDP_URL = 'http://127.0.0.1:5010'

# OAUTH - AUTHORIZATION CODE FLOW  #

oauth = OAuth(app)

oauth.register(
    name='idp',
    client_id='seu_client_id',
    client_secret='seu_client_secret',
    authorize_url= IDP_URL + '/authorize',
    authorize_params=None,
    access_token_url= IDP_URL + '/token',
    access_token_params=None,
    refresh_token_url= None,
    refresh_token_params=None,
    client_kwargs={'scope': 'profile'}
)

@app.route('/login', methods=['GET']) # STEP 1 - Login link
def login():
    redirect_uri = url_for('authorize', _external=True)
    return oauth.idp.authorize_redirect(redirect_uri)

@app.route('/authorize', methods=['GET']) # STEP 3 - Authorization Code Grant
def authorize():
    token = oauth.idp.authorize_access_token()
    session['token'] = token
    return redirect(url_for('index'))

@app.errorhandler(OAuthError)
def handle_oauth_error(error):
    return render_template('error.html', error=error), STATUS_CODE['INTERNAL_SERVER_ERROR']

# ROUTES #

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)