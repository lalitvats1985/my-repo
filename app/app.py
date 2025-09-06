from flask import Flask
import os

app = Flask(__name__)

@app.get('/')
def hello():
    version = os.environ.get('APP_VERSION', 'v1')
    return f'Hello from GKE! Version: {version}\n'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', '8080')))
