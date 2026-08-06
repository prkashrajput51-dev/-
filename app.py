from flask import Flask
import os
from smartapi import SmartConnect
from pyotp import TOTP

app = Flask(__name__)

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

    if angel:
        return """
        <h1 style='color:green'>
        ✅ Angel One Login Success
        </h1>
        """

    return """
    <h1 style='color:red'>
    ❌ Angel One Login Failed
    </h1>
    """


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
