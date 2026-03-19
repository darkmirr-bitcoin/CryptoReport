import ccxt
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

# 1. 코인 한글명 매핑 딕셔너리
CRYPTO_NAMES = {
    "BTC/USDT": "비트코인", "ETH/USDT": "이더리움", "BNB/USDT": "바이낸스코인",
    "SOL/USDT": "솔라나", "XRP/USDT": "리플", "ADA/USDT": "에이다",
    "AVAX/USDT": "아발란체", "DOGE/USDT": "도지코인", "DOT/USDT": "폴카닷",
    "LINK/USDT": "체인링크", "SHIB/USDT": "시바이누", "BCH/USDT": "비트코인캐시",
    "LTC/USDT": "라이트코인", "NEAR/USDT": "니어프로토콜", "UNI/USDT": "유니스왑",
    "SUI/USDT": "수이", "STX/USDT": "스택스"
}

# 2. 숫자 포맷팅 함수
def format_number(val):
    if pd.isna(val):
        return "0"
    if abs(val) >= 1000:
        return f"{val:,.2f}"
    elif abs(val) >= 1:
        return f"{val:,.4f}"
    else:
        return f"{val:,.6f}"

# 3. 데이터 수집 및 가공 함수
def fetch_crypto_analysis(ticker):
    exchange = ccxt.binance()
    ohlcv = exchange.fetch_ohlcv(ticker, timeframe='1d', limit=150)
    
    df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')

    df.ta.macd(append=True)
    df.ta.rsi(length=14, append=True)
    df.ta.ema(length=5, append=True)
    df.ta.ema(length=20, append=True)
    df.ta.ema(length=50, append=True)
    df.ta.ema(length=100, append=True)
    df.ta.bbands(length=20, append=True)
    df.ta.obv(append=True)

    # [수정된 부분] -1(현재 움직이는 가격) 대신 -2(오전 9시 마감된 종가 캔들) 사용
    latest = df.iloc[-2]
    
    macd_col = [c for c in df.columns if c.startswith('MACD_')][0]
    bbu_col = [c for c in df.columns if c.startswith('BBU_')][0]
    bbl_col = [c for c in df.columns if c.startswith('BBL_')][0]

    # [수정된 부분] 30일 차트도 실시간 가격 제외하고 확정된 30일치(-31 ~ -1)만 사용
    prices_30d = df['close'].iloc[-31:-1].tolist()
    prices_str = ",".join(map(str, prices_30d))
    sparkline_formula = f'=SPARKLINE(SPLIT("{prices_str}", ","))'

    trend_status = "상승추세 🚀" if latest['EMA_5'] > latest['EMA_20'] else "하락추세 🔻"
    avg_volume_14d = df['volume'].iloc[-15:-1].mean() # 거래량 평균도 확정일 기준으로 수정
    volume_strength = (latest['volume'] / avg_volume_14d) * 100

    coin_name = CRYPTO_NAMES.get(ticker, "")
    display_ticker = f"{ticker.replace('/USDT', '')} ({coin_name})"

    result_row = [
        datetime.now().strftime("%Y-%m-%d"),
        display_ticker,
        format_number(latest['close']),  # 이게 오전 9시 확정 종가가 됨
        sparkline_formula, 
        trend_status,
        f"{volume_strength:,.1f}%",
        format_number(latest['OBV']),
        format_number(latest[macd_col]),  
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

# 4. 구글 시트 일괄 업데이트
def update_google_sheet_bulk(data_rows):
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("secrets.json", scope)
    client = gspread.authorize(creds)

    sheet_id = "1Sf0YRhmhE-x5oYIfUG7Io2gI8XclEvmOeQkqy-BY1pc"
    sheet = client.open_by_key(sheet_id)
    worksheet_today = sheet.worksheet("Today")
    
    worksheet_today.append_rows(data_rows, value_input_option='USER_ENTERED')
    print(f"✅ 총 {len(data_rows)}개 코인 데이터 구글 시트 업데이트 완료!")

if __name__ == "__main__":
    tickers = list(CRYPTO_NAMES.keys())
    all_results = []
    
    print("🚀 다중 코인 데이터 수집 시작 (아침 9시 종가 기준)...")
    for ticker in tickers:
        try:
            print(f"수집 중: {ticker} ...")
            row_data = fetch_crypto_analysis(ticker)
            all_results.append(row_data)
            time.sleep(1) 
        except Exception as e:
            print(f"❌ {ticker} 수집 실패 (사유: {e})")
    
    if all_results:
        print("📊 구글 시트에 데이터 일괄 전송 중...")
        update_google_sheet_bulk(all_results)
    else:
        print("⚠️ 수집된 데이터가 없습니다.")