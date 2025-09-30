from flask import Flask
import requests

app = Flask(__name__)

@app.route('/response')
def call_api1():
    # Call API 1 using service name 'api1'
    response = requests.get("http://api1:5001/hello")
    print("Response from API 1:", response.json())
    return ({"message": "Hello from API 2", "api1_response": response.json()})   

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6001)
