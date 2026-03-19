import json
import time
import os  # 폴더 생성을 위해 추가
from google import genai
from google.genai import types
from datetime import datetime

# secrets.json에서 Gemini API 키 가져오기
with open("secrets.json", "r") as f:
    secrets = json.load(f)
GEMINI_API_KEY = secrets.get("gemini_api_key")

# Gemini 클라이언트 초기화
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_ID = "gemini-2.0-flash" 

def analyze_with_gemini(ticker_display, data_row):
    """
    각 코인별로 Gemini에게 실시간 뉴스 검색 및 종합 분석(점수화) 요청
    """
    current_price = data_row[2]
    trend = data_row[4]
    volume_str = data_row[5]
    macd = data_row[7]
    rsi = data_row[8]

    prompt = f"""
    당신은 전문 암호화폐 퀀트 분석가입니다. 
    제공된 기술적 지표 데이터와 당신이 실시간으로 검색한 최신 뉴스를 종합하여 [{ticker_display}]에 대한 투자의견 리포트를 작성해주세요.

    [기술적 지표 데이터]
    - 현재가(마감 종가): {current_price}
    - 5일/20일 이평선 추세: {trend}
    - 14일 평균 대비 거래량 강도: {volume_str}
    - MACD 상태: {macd}
    - RSI(14): {rsi}

    [분석 요청 사항]
    1. **뉴스 검색**: 구글 검색 도구를 사용하여 [{ticker_display}]와 관련된 지난 24시간 동안의 핵심 뉴스(가격에 영향을 미칠 만한 호재나 악재)를 3가지 이내로 요약하세요.
    2. **종합 분석**: 위의 기술적 지표와 검색한 뉴스를 종합하여 현재 시장 상황을 냉철하게 분석하세요.
    3. **투자 점수 및 의견**: 분석을 바탕으로 100점 만점 기준의 '투자 매력도 점수'를 매기고, 그 이유를 짧게 설명하세요.

    [출력 형식] - 반드시 아래 마크다운(Markdown) 형식을 지켜주세요.
    ---
    COIN: [{ticker_display}]
    SCORE: [점수만 숫자 표기, 예: 85]
    ---
    ### 📰 최신 뉴스 요약
    - ...
    - ...

    ### 📊 종합 분석
    ...

    ### 💡 투자의견 및 점수 산출 근거
    - **점수**: [점수]/100
    - **근거**: ...
    """

    print(f"   🤖 Gemini에게 [{ticker_display}] 분석 요청 중 (뉴스 검색 포함)...")
    
    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        return response.text
    except Exception as e:
        print(f"   ❌ Gemini 분석 실패 (사유: {e})")
        return None

def extract_score(ai_text):
    if not ai_text: return 0
    try:
        for line in ai_text.split('\n'):
            if "SCORE:" in line:
                score_str = line.split("SCORE:")[1].strip().replace("[", "").replace("]", "")
                return int(score_str)
    except:
        pass
    return 0

def generate_final_report(good_reports):
    """
    80점 이상 코인들의 리포트를 모아서 reports 폴더 내에 md 파일로 저장
    """
    if not good_reports:
        print("📭 오늘 80점 이상인 코인이 없습니다. 리포트를 생성하지 않습니다.")
        return

    # reports 폴더가 없으면 자동 생성
    report_dir = "reports"
    os.makedirs(report_dir, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    # 확장자를 .md로 변경하고 경로 설정
    filename = os.path.join(report_dir, f"Crypto_Report_{date_str}.md")
    
    # 마크다운 메인 헤더
    report_content = f"# 🔥 오늘의 암호화폐 투자 하이라이트 (80점 이상) - {date_str}\n\n"
    report_content += "---\n\n"
    report_content += "\n\n---\n\n".join(good_reports) # 리포트 사이를 구분선으로 분리
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"📂 최종 분석 리포트가 생성되었습니다: {filename}")
