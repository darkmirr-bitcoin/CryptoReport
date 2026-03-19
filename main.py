import time
from crypto_analyzer import fetch_crypto_analysis, CRYPTO_NAMES
from sheet_manager import update_google_sheet_bulk

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