from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # This will enable all CORS requests

@app.route('/api/data')
def get_data():
    # Sample data
    data = {
        'name': 'John Doe',
        'age': 30,
        'city': 'New York'
    }
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=5001) # Different port than the client