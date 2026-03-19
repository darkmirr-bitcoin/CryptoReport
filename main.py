import time
from crypto_analyzer import fetch_crypto_analysis, CRYPTO_NAMES
from sheet_manager import update_google_sheet_bulk
from ai_reporter import (
    GEMINI_API_KEY, analyze_with_gemini, extract_score, 
    generate_final_report, fetch_fear_and_greed, fetch_mvrv_z_score, analyze_market_overview
)
from google import genai

if __name__ == "__main__":
    print("🚀 암호화폐 분석 파이프라인 가동 시작!\n")
    
    # [핵심] 여기서 client를 생성해서 뒤에 계속 전달함!
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    tickers = list(CRYPTO_NAMES.keys())
    all_results = []
    high_score_reports = [] 
    
    # --- 1단계: 시트 데이터 수집 ---
    print("1️⃣ 단계: 구글 시트용 코인 데이터 수집 시작...")
    for ticker in tickers:
        try:
            print(f"   수집 중: {ticker} ...")
            row_data = fetch_crypto_analysis(ticker)
            all_results.append(row_data)
            time.sleep(0.3) 
        except Exception as e:
            print(f"❌ {ticker} 수집 실패 (사유: {e})")
    
    if all_results:
        print("   📊 구글 시트에 데이터 일괄 전송 중...")
        update_google_sheet_bulk(all_results)
    
    # --- 2단계: 시장 지표 및 시황 분석 ---
    print("\n2️⃣ 단계: 시장 전체 시황 및 지표 분석 중...")
    fng_value = fetch_fear_and_greed()
    mvrv_value = fetch_mvrv_z_score(client)
    
    indicators = {'fng': fng_value, 'mvrv': mvrv_value}
    market_summary = analyze_market_overview(client, indicators)
    
    # --- 3단계: 개별 코인 AI 분석 ---
    print("\n3️⃣ 단계: Gemini AI 코인별 개별 분석 시작...")
    for data_row in all_results:
        ticker_display = data_row[1] 
        
        ai_report_text = analyze_with_gemini(client, ticker_display, data_row)
        score = extract_score(ai_report_text)
        print(f"   => [{ticker_display}] 분석 완료 - AI 점수: {score}점")
        
        if score >= 75:
             try:
                 parts = ai_report_text.split("---")
                 if len(parts) >= 3:
                     clean_report = parts[2].strip()
                 else:
                     clean_report = ai_report_text.replace(f"SCORE: {score}", "").strip()
                 
                 high_score_reports.append(f"### {ticker_display} (AI 점수: **{score}/100**)\n\n{clean_report}")
             except Exception as e:
                 pass
        
        time.sleep(1)

    # --- 4단계: 리포트 생성 ---
    print("\n4️⃣ 단계: 최종 MD 리포트 생성 중...")
    generate_final_report(market_summary, high_score_reports, fng_value, mvrv_value)
    
    print("\n✅ 모든 과정 완료!")
