#!/usr/bin/env python3

import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def health():
    return jsonify({
        'status': 'healthy',
        'environment': os.getenv('ENVIRONMENT', 'unknown'),
        'version': os.getenv('APP_VERSION', '1.0.0')
    })

@app.route('/api/info')
def info():
    return jsonify({
        'app': 'teddy',
        'environment': os.getenv('ENVIRONMENT', 'unknown'),
        'version': os.getenv('APP_VERSION', '1.0.0'),
        'region': os.getenv('AWS_REGION', 'unknown')
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)