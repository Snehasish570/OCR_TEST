from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/hello')
def hello():
    return jsonify({"message": "Hello from API 1"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
