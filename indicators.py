import pandas as pd

def ema(df, period):
    return df["close"].ewm(span=period, adjust=False).mean()

def rsi(df, period=14):
    delta = df["close"].diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))

def atr(df, period=14):
    high_low = df["high"] - df["low"]

    high_close = abs(df["high"] - df["close"].shift())

    low_close = abs(df["low"] - df["close"].shift())

    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

    return tr.rolling(period).mean()
