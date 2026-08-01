import requests
import pandas as pd
import time
import yfinance as yf
from flask import Flask, render_template_string
from datetime import datetime

app = Flask(__name__)

# ===== SETTINGS =====
LOT_SIZE = 50        # NIFTY 1 Lot
TARGET_POINTS = 25   # 25 Point Target
SL_POINTS = 12       # 12 Point Stop Loss
DAILY_TARGET = 200   # Daily 200 Point Target

# ===== GLOBAL =====
in_trade = False
entry_price = 0
trade_type = ""
strike = 0
daily_pnl = 0
entry_nifty = 0

# ===== MARKET TIME =====
def is_market_open():
    now = datetime.now()
    # Mon-Fri and 9:15 AM to 3:30 PM
    return now.weekday() < 5 and (9 <= now.hour < 15 or (now.hour == 9 and now.minute >= 15))

# ===== SIGNAL LOGIC =====
def generate_signal():
    try:
        # 1. NIFTY 5min डेटा लाओ
        nifty = yf.download("^NSEI", period="5d", interval="5m", progress=False)
        ltp = round(nifty['Close'][-1], 2)
    except:
        return {"error": "Data नहीं मिल रहा"}
    
    signal = {}
    signal['time'] = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    signal['ltp'] = ltp
    signal['direction'] = "WAIT"
    signal['candle'] = "No Pattern"
    
    # 2. कैंडल साइकोलॉजी - Engulfing
    last = nifty.iloc[-1]
    prev = nifty.iloc[-2]
    
    # Bullish Engulfing = CALL Signal
    if last['Close'] > last['Open'] and prev['Close'] < prev['Open']:
        if last['Close'] > prev['Open'] and last['Open'] < prev['Close']:
            signal['candle'] = "BULLISH ENGULFING ✅ Buyers Strong"
            signal['direction'] = "CALL"
    
    # Bearish Engulfing = PUT Signal
    elif last['Close'] < last['Open'] and prev['Close'] > prev['Open']:
        if last['Close'] < prev['Open'] and last['Open'] > prev['Close']:
            signal['candle'] = "BEARISH ENGULFING ❌ Sellers Strong"
            signal['direction'] = "PUT"
    
    # 3. Key Levels
    atm = round(ltp/50)*50
    signal['support'] = atm
    signal['resistance'] = atm + 100
    
    # 4. 100-120 वाले ऑप्शन का सजेशन
    if signal['direction'] == "CALL":
        signal['option'] = f"NIFTY {atm + 50} CE"
    elif signal['direction'] == "PUT":
        signal['option'] = f"NIFTY {atm - 50} PE"
    else:
        signal['option'] = "-"
    
    signal['entry'] = "100-110"
    signal['target'] = f"{TARGET_POINTS} Points = ₹{TARGET_POINTS * LOT_SIZE}"
    signal['sl'] = f"{SL_POINTS} Points = ₹{SL_POINTS * LOT_SIZE}"
    signal['daily_target'] = f"{DAILY_TARGET} Points = ₹{DAILY_TARGET * LOT_SIZE}"
    
    return signal

# ===== WEB PAGE =====
@app.route('/')
def home():
    if not is_market_open():
        return """
        <body style="background:#0e1117; color:white; text-align:center; padding-top:100px;">
        <h1>📊 NIFTY SIGNAL BOARD</h1>
        <h2 style="color:red;">Market Closed</h2>
        <p>Market Time: Mon-Fri 9:15 AM to 3:30 PM</p>
        </body>
        """
    
    sig = generate_signal()
    if "error" in sig:
        return f"<h1>Error: {sig['error']}</h1>"
    
    html = f"""
    <body style="font-family: Arial; background:#0e1117; color:white; padding:20px; text-align:center;">
    <h1>📊 NIFTY SIGNAL BOARD v2.1</h1>
    <p><b>Time:</b> {sig['time']} | <b>LTP:</b> {sig['ltp']}</p>
    <hr style="border:1px solid #333;">
    
    <h3>1. Candle: {sig['candle']}</h3>
    <h3>2. Levels: Support {sig['support']} | Resistance {sig['resistance']}</h3>
    <h3>3. Suggested Option: {sig['option']}</h3>
    
    <hr style="border:1px solid #333;">
    <h2 style="color:yellow;">>>> FINAL SIGNAL: {sig['direction']}</h2>
    <p><b>Entry Zone:</b> {sig['entry']} | <b>Target:</b> {sig['target']} | <b>SL:</b> {sig['sl']}</p>
    <p><b>Daily Target:</b> {sig['daily_target']}</p>
    
    <h4 style="color:red;">⚠️ NOTE: This is only a SIGNAL. No auto trade. Entry at your own risk.</h4>
    </body>
    """
    return render_template_string(html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
