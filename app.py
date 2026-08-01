import pandas as pd
from flask import Flask, render_template_string
from datetime import datetime
from smartapi import SmartConnect
from pyotp import TOTP

app = Flask(__name__)

# ===== अपनी ANGEL API DETAILS यहां डालो =====
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
        return obj
    except Exception as e:
        print("Login Error:", e)
        return None

def generate_pro_signal():
    angel = angel_login()
    if not angel:
        return {"error": "Angel Login Failed. API Key चेक करो"}
    
    try:
        nifty_token = "99926000"
        ltp_data = angel.ltpData("NSE", "NIFTY", nifty_token)
        ltp = float(ltp_data['data']['ltp'])
        
        fromdate = datetime.now().strftime("%Y-%m-%d 09:15")
        todate = datetime.now().strftime("%Y-%m-%d 15:30")
        candle_data = angel.getCandleData({
            "exchange": "NSE", "symboltoken": nifty_token, "interval": "FIVE_MINUTE",
            "fromdate": fromdate, "todate": todate
        })
        df = pd.DataFrame(candle_data['data'], columns=['time','open','high','low','close','volume'])
        df = df.astype(float)
        
    except Exception as e:
        return {"error": f"Data Error: {e}"}
    
    signal = {'direction': 'WAIT', 'score': 0}
    signal['time'] = datetime.now().strftime('%H:%M:%S')
    signal['ltp'] = round(ltp, 2)
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    high_20 = df['high'][-20:].max()
    low_20 = df['low'][-20:].min()
    
    if last['close'] > high_20: signal['score'] += 1
    elif last['close'] < low_20: signal['score'] += 1
    
    if last['close'] > last['open'] and prev['close'] < prev['open']:
        if last['close'] > prev['open']: signal['score'] += 1
    
    avg_vol = df['volume'][-10:].mean()
    if last['volume'] > avg_vol * 1.5: signal['score'] += 1
    
    if signal['score'] >= 2:
        signal['direction'] = "CALL"
    elif signal['score'] <= -2:
        signal['direction'] = "PUT"
    
    atm = round(ltp/50)*50
    signal['option'] = f"NIFTY {atm+50} CE" if signal['direction'] == "CALL" else f"NIFTY {atm-50} PE" if signal['direction'] == "PUT" else "-"
    signal['entry'] = f"{TARGET_OPTION_PRICE_MIN}-{TARGET_OPTION_PRICE_MAX}"
    
    return signal

@app.route('/')
def home():
    sig = generate_pro_signal()
    if "error" in sig:
        return f"<h1>Error: {sig['error']}</h1>"
    
    color = "yellow" if sig['direction'] == "WAIT" else "lightgreen" if sig['direction'] == "CALL" else "tomato"
    
    html = f"""
    <body style="background:#0e1117; color:white; padding:20px; text-align:center; font-family:Arial;">
    <h1>📊 NIFTY PRO SIGNAL BOARD v3.2</h1>
    <p><b>NIFTY LTP:</b> {sig['ltp']} | <b>Time:</b> {sig['time']}</p>
    <h2 style="color:{color}; font-size:40px;">SIGNAL: {sig['direction']}</h2>
    <h3>Option: {sig['option']}</h3>
    <p>Entry: {sig['entry']} | Target: +25 | SL: -12</p>
    <p style="color:orange;">⚠️ Signal Only Board. No Auto Trade.</p>
    </body>
    """
    return render_template_string(html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
