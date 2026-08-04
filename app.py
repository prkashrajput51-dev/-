import pandas as pd
from flask import Flask, render_template_string
from datetime import datetime
from smartapi import SmartConnect
from pyotp import TOTP

app = Flask(__name__)

# ===== Angel One Details =====
API_KEY = "DdAy4ZfK" #
CLIENT_CODE = "H92168" #
PASSWORD = "8228" #
TOTP_SECRET = "35UQA4SDBC3GPZJN7WYLJDTVWE" #

TARGET_OPTION_PRICE_MIN = 100
TARGET_OPTION_PRICE_MAX = 120
TARGET_POINTS = 25
SL_POINTS = 12

def angel_login():
    try:
        obj = SmartConnect(api_key=API_KEY)
        totp = TOTP(TOTP_SECRET).now()
        data = obj.generateSession(CLIENT_CODE, PASSWORD, totp)

        if not data or data.get("status") is False:
            return None

        return obj

    except Exception as e:
        print("Login Error:", e)
        return None


def generate_pro_signal():
    angel = angel_login()

    if not angel:
        return {"error": "Angel Login Failed"}

    try:
        nifty_token = "99926000"

        ltp_data = angel.ltpData("NSE", "NIFTY", nifty_token)
        ltp = float(ltp_data["data"]["ltp"])

        fromdate = datetime.now().strftime("%Y-%m-%d 09:15")
        todate = datetime.now().strftime("%Y-%m-%d 15:30")

        candle_data = angel.getCandleData({
            "exchange": "NSE",
            "symboltoken": nifty_token,
            "interval": "FIVE_MINUTE",
            "fromdate": fromdate,
            "todate": todate
        })

        df = pd.DataFrame(
            candle_data["data"],
            columns=["time", "open", "high", "low", "close", "volume"]
        )

        df[["open", "high", "low", "close", "volume"]] = \
            df[["open", "high", "low", "close", "volume"]].astype(float)

        if len(df) < 21:
            return {"error": "Not enough candle data"}

    except Exception as e:
        return {"error": str(e)}

    signal = {
        "direction": "WAIT",
        "score": 0,
        "time": datetime.now().strftime("%H:%M:%S"),
        "ltp": round(ltp, 2)
    }

    last = df.iloc[-1]
    prev = df.iloc[-2]

    high_20 = df["high"].iloc[-21:-1].max()
    low_20 = df["low"].iloc[-21:-1].min()

    # Breakout
    if last["close"] > high_20:
        signal["score"] += 1
    elif last["close"] < low_20:
        signal["score"] -= 1

    # Bullish
    if last["close"] > last["open"] and prev["close"] < prev["open"]:
        if last["close"] > prev["open"]:
            signal["score"] += 1

    # Bearish
    if last["close"] < last["open"] and prev["close"] > prev["open"]:
        if last["close"] < prev["open"]:
            signal["score"] -= 1

    avg_vol = df["volume"].iloc[-10:].mean()

    if last["volume"] > avg_vol * 1.5:
        if last["close"] > last["open"]:
            signal["score"] += 1
        else:
            signal["score"] -= 1

    if signal["score"] >= 2:
        signal["direction"] = "CALL"
    elif signal["score"] <= -2:
        signal["direction"] = "PUT"

    atm = round(ltp / 50) * 50

    if signal["direction"] == "CALL":
        signal["option"] = f"NIFTY {atm+50} CE"
    elif signal["direction"] == "PUT":
        signal["option"] = f"NIFTY {atm-50} PE"
    else:
        signal["option"] = "-"

    signal["entry"] = f"{TARGET_OPTION_PRICE_MIN}-{TARGET_OPTION_PRICE_MAX}"

    return signal


@app.route("/")
def home():

    sig = generate_pro_signal()

    if "error" in sig:
        return f"<h1>{sig['error']}</h1>"

    color = {
        "WAIT": "yellow",
        "CALL": "lightgreen",
        "PUT": "tomato"
    }[sig["direction"]]

    return render_template_string(f"""
    <body style="background:#0e1117;color:white;text-align:center;
    font-family:Arial;padding:30px">

    <h1>📊 NIFTY PRO SIGNAL BOARD v3.2</h1>

    <h2>NIFTY : {sig['ltp']}</h2>

    <h2 style="color:{color};font-size:45px">
    {sig['direction']}
    </h2>

    <h3>{sig['option']}</h3>

    <h3>Entry : {sig['entry']}</h3>

    <h3>Target : +{TARGET_POINTS}</h3>

    <h3>Stop Loss : -{SL_POINTS}</h3>

    <p>Time : {sig['time']}</p>

    </body>
    """)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
