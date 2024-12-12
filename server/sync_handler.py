import os
import subprocess
from flask import Flask, request, jsonify
from functools import wraps

app = Flask(__name__)

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "No authorization header"}), 401

        token = auth_header.split(" ")[1]
        if token != os.getenv("SYNC_AUTH_TOKEN"):
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)
    return decorated

@app.route('/sync', methods=['POST'])
@require_auth
def sync():
    try:
        # Pull latest changes
        subprocess.run(['git', 'pull'], check=True)
        
        # Reload Evennia (assuming it's running as a service)
        subprocess.run(['systemctl', 'restart', 'evennia'], check=True)
        
        return jsonify({"status": "success"}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 