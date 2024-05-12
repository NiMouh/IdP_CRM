from flask import Flask, render_template
import requests

app = Flask(__name__, template_folder='templates')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/frontend_endpoint', methods=['GET'])
def frontend_endpoint():
    # Make a request to the backend
    response = requests.get('http://backend_endpoint')

    # Process the response from the backend
    data = response.json()

    # Render the frontend template with the data
    return render_template('frontend.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)