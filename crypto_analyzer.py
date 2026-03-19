import ccxt
import pandas as pd
import pandas_ta as ta
from datetime import datetime

# 코인 한글명 매핑
CRYPTO_NAMES = {
    "BTC/USDT": "비트코인", "ETH/USDT": "이더리움", "BNB/USDT": "바이낸스코인",
    "SOL/USDT": "솔라나", "XRP/USDT": "리플", "ADA/USDT": "에이다",
    "AVAX/USDT": "아발란체", "DOGE/USDT": "도지코인", "DOT/USDT": "폴카닷",
    "LINK/USDT": "체인링크", "SHIB/USDT": "시바이누", "BCH/USDT": "비트코인캐시",
    "LTC/USDT": "라이트코인", "NEAR/USDT": "니어프로토콜", "UNI/USDT": "유니스왑",
    "SUI/USDT": "수이", "STX/USDT": "스택스"
}

def format_number(val):
    if pd.isna(val):
        return "0"
    if abs(val) >= 1000:
        return f"{val:,.2f}"
    elif abs(val) >= 1:
        return f"{val:,.4f}"
    else:
        return f"{val:,.6f}"

def fetch_crypto_analysis(ticker):
    exchange = ccxt.binance()
    ohlcv = exchange.fetch_ohlcv(ticker, timeframe='1d', limit=150)
    
    df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')

    # 보조지표 계산
    df.ta.macd(append=True)
    df.ta.rsi(length=14, append=True)
    df.ta.ema(length=5, append=True)
    df.ta.ema(length=20, append=True)
    df.ta.ema(length=50, append=True)
    df.ta.ema(length=100, append=True)
    df.ta.bbands(length=20, append=True)
    df.ta.obv(append=True)

    df['OBV_EMA_20'] = ta.ema(df['OBV'], length=20)
    latest = df.iloc[-2]  # 오전 9시 마감된 종가 캔들
    
    macd_col = [c for c in df.columns if c.startswith('MACD_')][0]
    macds_col = [c for c in df.columns if c.startswith('MACDs_')][0]
    bbu_col = [c for c in df.columns if c.startswith('BBU_')][0]
    bbl_col = [c for c in df.columns if c.startswith('BBL_')][0]

    # 스파크라인 (30일치)
    prices_30d = df['close'].iloc[-31:-1].tolist()
    prices_str = ",".join(map(str, prices_30d))
    sparkline_formula = f'=SPARKLINE(SPLIT("{prices_str}", ","))'

    trend_status = "상승추세 🚀" if latest['EMA_5'] > latest['EMA_20'] else "하락추세 🔻"
    avg_volume_14d = df['volume'].iloc[-15:-1].mean()
    volume_strength = (latest['volume'] / avg_volume_14d) * 100

    obv_trend = "상승 📈" if latest['OBV'] > latest['OBV_EMA_20'] else "하락 📉"
    
    macd_val = latest[macd_col]
    signal_val = latest[macds_col]
    macd_status = "골든 🟢" if macd_val > signal_val else "데드 🔴"
    macd_display = f"{macd_status} ({format_number(macd_val)})"

    coin_name = CRYPTO_NAMES.get(ticker, "")
    display_ticker = f"{ticker.replace('/USDT', '')} ({coin_name})"

    result_row = [
        datetime.now().strftime("%Y-%m-%d"),
        display_ticker,
        format_number(latest['close']),
        sparkline_formula, 
        trend_status,
        f"{volume_strength:,.1f}%",
        obv_trend,
        macd_display,
        round(latest['RSI_14'], 2),
        format_number(latest['EMA_5']),
        format_number(latest['EMA_20']),
        format_number(latest['EMA_50']),
        format_number(latest['EMA_100']),
        format_number(latest[bbu_col]),   
        format_number(latest[bbl_col]),   
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ]
    return result_row