from flask import Flask
import os
from smartapi import SmartConnect
from pyotp import TOTP

app = Flask(__name__)

# ===== Environment Variables =====
API_KEY = os.getenv("ONE_API_KEY")
CLIENT_CODE = os.getenv("CLIENT_CODE")
PIN = os.getenv("PIN")
TOTP_SECRET = os.getenv("TOTP")

def angel_login():
    try:
        obj = SmartConnect(api_key=API_KEY)
        totp = TOTP(TOTP_SECRET).now()
        data = obj.generateSession(CLIENT_CODE, PIN, totp)

        if data.get("status") == False:
            return None

        return obj

    except Exception as e:
        print(e)
        return None

@app.route("/")
def home():
    angel = angel_login()

    if angel is None:
        return "<h2>❌ Angel One Login Failed</h2>"

    return "<h2>✅ Angel One Login Success</h2>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
