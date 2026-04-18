import pandas as pd

def find_swings(df, window=2):
    """Identifies fractal highs and lows (The base of SMC)."""
    # Ensure window is applied to identify local peaks/valleys
    df['high_swing'] = df['High'].rolling(window=2*window+1, center=True).apply(
        lambda x: x[window] == max(x), raw=True
    )
    df['low_swing'] = df['Low'].rolling(window=2*window+1, center=True).apply(
        lambda x: x[window] == min(x), raw=True
    )
    return df

def get_smc_signals(df):
    """Detects BOS and finds Entry/SL/TP levels."""
    highs = df[df['high_swing'] == 1]['High']
    lows = df[df['low_swing'] == 1]['Low']
    
    if len(highs) < 2 or len(lows) < 2:
        return "Building Structure...", 0, 0, 0

    last_high = float(highs.values[-1])
    last_low = float(lows.values[-1])
    current_price = float(df['Close'].values[-1])
    
    # Bullish BOS: Price breaks above the most recent swing high
    if current_price > last_high:
        entry = current_price
        sl = last_low 
        tp = entry + (entry - sl) * 2 # 1:2 Risk Reward
        return "BULLISH BOS DETECTED", round(entry, 5), round(sl, 5), round(tp, 5)
    
    # Bearish BOS: Price breaks below the most recent swing low
    elif current_price < last_low:
        entry = current_price
        sl = last_high 
        tp = entry - (sl - entry) * 2
        return "BEARISH BOS DETECTED", round(entry, 5), round(sl, 5), round(tp, 5)
    
    return "Market Ranging (No BOS)", 0, 0, 0