# app.py
from flask import Flask, render_template_string, request, jsonify
import hmac
import hashlib
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

# --- OTP Functions ---
def validate_master_phrase(phrase: str) -> bool:
    return len(phrase.split()) >= 5

def generate_otp(master_phrase: str, user_id: str, secret_key: bytes, timestamp_str: str = None) -> str:
    if not validate_master_phrase(master_phrase):
        raise ValueError("Master phrase must have at least 5 words.")
    if timestamp_str is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    else:
        timestamp = timestamp_str
    combined = f"{master_phrase} {user_id} {timestamp}"
    return hmac.new(secret_key, combined.encode('utf-8'), hashlib.sha256).hexdigest()

def verify_otp(client_otp: str, master_phrase: str, user_id: str, secret_key: bytes, window_seconds: int = 60) -> bool:
    current = datetime.now(timezone.utc)
    for i in range(window_seconds + 1):
        check_time = current - timedelta(seconds=i)
        timestamp = check_time.strftime("%Y-%m-%d %H:%M:%S")
        if generate_otp(master_phrase, user_id, secret_key, timestamp) == client_otp:
            return True
    return False

SECRET_KEY = b"supersecretkey"

# --- HTML Templates ---
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Weird Sentence OTP Demo</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-6">
            <h1 class="text-center mb-4">Weird Sentence OTP</h1>
            <form id="form" class="border p-4 rounded">
                <div class="mb-3">
                    <input type="text" class="form-control" id="phrase" placeholder="Master Phrase (min 5 words)" required>
                </div>
                <div class="mb-3">
                    <input type="text" class="form-control" id="user_id" placeholder="User ID" required>
                </div>
                <button type="button" class="btn btn-primary w-100" onclick="login()">Login</button>
            </form>
            <div id="result" class="mt-3"></div>
        </div>
    </div>
    <script>
        async function login() {
            const phrase = document.getElementById('phrase').value;
            const user_id = document.getElementById('user_id').value;
            if (!phrase || !user_id) return alert("Fill all fields");
            const res = await fetch('/verify', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({phrase, user_id})
            });
            const data = await res.json();
            const div = document.getElementById('result');
            div.innerHTML = data.success 
                ? `<div class="alert alert-success">Success! OTP: <code>${data.otp}</code><br><a href="/dashboard" class="btn btn-success mt-2">Dashboard</a></div>`
                : `<div class="alert alert-danger">${data.error}</div>`;
        }
    </script>
</body>
</html>
"""

DASHBOARD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="container mt-5 text-center">
    <h1>Welcome!</h1>
    <p>You are logged in with Weird Sentence OTP.</p>
    <a href="/" class="btn btn-primary">Back</a>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HOME_TEMPLATE)

@app.route('/verify', methods=['POST'])
def verify():
    try:
        data = request.json
        phrase = data['phrase']
        user_id = data['user_id']
        otp = generate_otp(phrase, user_id, SECRET_KEY)
        if verify_otp(otp, phrase, user_id, SECRET_KEY):
            return jsonify({'success': True, 'otp': otp})
        return jsonify({'success': False, 'error': 'Invalid OTP'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/dashboard')
def dashboard():
    return render_template_string(DASHBOARD)

# فقط برای لوکال
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)