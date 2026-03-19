import time
from crypto_analyzer import fetch_crypto_analysis, CRYPTO_NAMES
from sheet_manager import update_google_sheet_bulk
from ai_reporter import analyze_with_gemini, extract_score, generate_final_report

if __name__ == "__main__":
    tickers = list(CRYPTO_NAMES.keys())
    all_results = []
    high_score_reports = [] 
    
    print("🚀 다중 코인 데이터 수집 시작 (아침 9시 종가 기준)...")
    
    for ticker in tickers:
        try:
            print(f"   수집 중: {ticker} ...")
            row_data = fetch_crypto_analysis(ticker)
            all_results.append(row_data)
            time.sleep(0.5) 
        except Exception as e:
            print(f"❌ {ticker} 수집 실패 (사유: {e})")
    
    if all_results:
        print("\n📊 구글 시트에 데이터 일괄 전송 중...")
        update_google_sheet_bulk(all_results)
    else:
        print("\n⚠️ 수집된 데이터가 없어 시트 업데이트를 건너뜁니다.")

 # ... (위쪽 코드는 동일) ...
    print("\n🧠 Gemini AI 종합 분석 및 뉴스 검색 시작...")
    for data_row in all_results:
        ticker_display = data_row[1] 
        
        # 맨 앞에 'client, ' 를 추가해줘!
        ai_report_text = analyze_with_gemini(client, ticker_display, data_row)
        score = extract_score(ai_report_text)
        print(f"   => [{ticker_display}] 분석 완료 - AI 점수: {score}점")
        
        # [수정된 부분] 기준점수를 75점으로 낮춤!
        if score >= 75:
             try:
                 # AI가 '---'를 빼먹고 답변할 때를 대비해 더 안전하게 코멘트를 가져옴
                 parts = ai_report_text.split("---")
                 if len(parts) >= 3:
                     clean_report = parts[2].strip()
                 else:
                     clean_report = ai_report_text.replace(f"SCORE: {score}", "").strip()
                 
                 # 마크다운 서식으로 리스트에 추가 (AI 종합 분석 코멘트 포함)
                 high_score_reports.append(f"## 🏆 {ticker_display} (AI 점수: **{score}/100**)\n\n{clean_report}")
             except Exception as e:
                 print(f"   ⚠️ 리포트 파싱 오류: {e}")
        
        time.sleep(2)

    print("\n📂 최종 MD 리포트 생성 중...")
    generate_final_report(high_score_reports)
    
    print("\n✅ 모든 과정이 완벽하게 끝났습니다!")
