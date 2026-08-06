from indicators import ema, rsi, atr

def generate_signal(df):

    df["EMA9"] = ema(df, 9)
    df["EMA21"] = ema(df, 21)
    df["RSI"] = rsi(df, 14)
    df["ATR"] = atr(df, 14)

    last = df.iloc[-1]

    signal = "WAIT"
    score = 0

    # EMA Trend
    if last["EMA9"] > last["EMA21"]:
        score += 1
    else:
        score -= 1

    # RSI Filter
    if last["RSI"] > 60:
        score += 1
    elif last["RSI"] < 40:
        score -= 1

    # ATR Filter
    atr_avg = df["ATR"].tail(20).mean()
    if last["ATR"] < atr_avg * 0.8:
        return {
            "signal": "WAIT",
            "reason": "Sideways Market"
        }

    # Breakout
    high20 = df["high"].tail(20).max()
    low20 = df["low"].tail(20).min()

    if last["close"] > high20:
        score += 2

    elif last["close"] < low20:
        score -= 2

    if score >= 3:
        signal = "CALL"

    elif score <= -3:
        signal = "PUT"

    return {
        "signal": signal,
        "score": score,
        "ema9": round(last["EMA9"],2),
        "ema21": round(last["EMA21"],2),
        "rsi": round(last["RSI"],2),
        "atr": round(last["ATR"],2)
    }
