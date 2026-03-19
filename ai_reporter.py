import json
import time
import os
import requests  # API 호출을 위해 추가
from google import genai
from google.genai import types
from datetime import datetime

# secrets.json 설정
with open("secrets.json", "r") as f:
    secrets = json.load(f)
GEMINI_API_KEY = secrets.get("gemini_api_key")

# Gemini 클라이언트 (main에서 받아서 쓰도록 변경)
MODEL_ID = "gemini-2.0-flash" 

# --- [신규 ✨] 시장 지표 가져오기 함수들 ---

def fetch_fear_and_greed():
    """크립토 공포탐욕지수 API 호출"""
    print("   📊 공포탐욕지수 가져오는 중...")
    try:
        response = requests.get("https://api.alternative.me/fng/")
        data = response.json()
        value = data['data'][0]['value']
        classification = data['data'][0]['value_classification']
        return f"{value} ({classification})"
    except Exception as e:
        print(f"   ⚠️ 공포탐욕지수 수집 실패: {e}")
        return "데이터 없음"

def fetch_mvrv_z_score(client):
    """Gemini 검색을 통해 현재 비트코인 MVRV-Z 스코어 수집"""
    print("   📊 MVRV-Z 스코어 검색 중...")
    prompt = "현재 비트코인의 MVRV Z-Score 값을 구글 검색을 통해 찾아줘. 딱 숫자(소수점 포함)와 간단한 상태(예: 저평가, 고평가)만 답변해."
    
    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        return response.text.strip()
    except Exception as e:
        print(f"   ⚠️ MVRV-Z 스코어 검색 실패: {e}")
        return "데이터 없음"

# --- [신규 ✨] 전체 시황 분석 함수 ---

def analyze_market_overview(client, indicators):
    """Gemini에게 야후파이낸스 등 기반 주요 뉴스 검색 및 시황 요약 요청"""
    print("\n📰 Gemini가 야후 파이낸스 등 외신을 검색하여 오늘의 시황을 분석 중입니다...")
    
    prompt = f"""
    당신은 선임 암호화폐 시장 전략가입니다. 
    구글 검색 도구를 사용하여 야후 파이낸스(Yahoo Finance), 코인데스크(CoinDesk), 블룸버그(Bloomberg) 등 주요 외신에서 지난 24시간 동안 보도된 암호화폐 관련 핵심 뉴스 80개 이상을 종합적으로 모니터링하세요.

    그 후, 수집된 방대한 정보를 바탕으로 오늘의 대략적인 암호화폐 시장 시황 분석 보고서를 마크다운 형식으로 작성해주세요.

    [현재 시장 주요 지표]
    - 공포탐욕지수: {indicators['fng']}
    - 비트코인 MVRV Z-Score: {indicators['mvrv']}

    [요청 사항]
    1. **시황 총평**: 현재 시장이 호재 중심인지 악재 중심인지, 전반적인 투자 심리는 어떤지 강렬한 한 문장으로 요약하세요.
    2. **핵심 드라이버 (주요 뉴스 3)**: 시장에 가장 큰 영향을 미친 뉴스를 야후 파이낸스 등을 인용하여 3가지 이내로 요약하고 분석하세요.
    3. **온체인 지표 해석**: 제공된 공포탐욕지수와 MVRV Z-Score를 분석 내용과 연결하여 해석하세요.

    [출력 형식] - 반드시 마크다운(Markdown) 형식을 지켜주세요.
    ### 🌐 오늘의 암호화폐 시황 총평
    > ... (강렬한 한 문장)

    #### 📍 핵심 시장 드라이버 및 뉴스 분석
    - **...**: ... (야후 파이낸스 인용 등)
    - **...**: ...
    """

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
        print(f"   ❌ 시황 분석 실패 (사유: {e})")
        return "시황 분석 데이터를 가져오지 못했습니다."

# --- 기존 함수들 (살짝 수정) ---

def analyze_with_gemini(client, ticker_display, data_row):
    """각 코인별 분석 (기존 유지)"""
    current_price = data_row[2]
    trend = data_row[4]
    volume_str = data_row[5]
    macd = data_row[7]
    rsi = data_row[8]

    prompt = f"""
    당신은 전문 암호화폐 퀀트 분석가입니다. 
    제공된 기술적 지표 데이터와 당신이 실시간으로 검색한 최신 뉴스를 종합하여 [{ticker_display}]에 대한 투자의견 리포트를 마크다운 형식으로 작성해주세요.

    [기술적 지표 데이터]
    - 현재가(마감 종가): {current_price}
    - 5일/20일 이평선 추세: {trend}
    - 거래량 강도: {volume_str}
    - MACD 상태: {macd}
    - RSI(14): {rsi}

    [출력 형식] - 반드시 아래 마크다운(Markdown) 형식을 지켜주세요. 영역 구분선 '---'를 꼭 포함하세요.
    ---
    SCORE: [100점 만점 기준 점수만 숫자 표기, 예: 85]
    ---
    ### 📰 코인별 최신 뉴스 요약
    - ...
    - ...

    ### 📊 기술적 분석 및 의견
    ...

    ### 💡 점수 산출 근거
    - **점수**: [점수]/100
    - **근거**: ...
    """

    print(f"   🤖 Gemini에게 [{ticker_display}] 개별 분석 요청 중...")
    
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
        # 점수 추출 로직 보강
        if "SCORE:" in ai_text:
            score_part = ai_text.split("SCORE:")[1].split('\n')[0].strip()
            score_str = score_part.replace("[", "").replace("]", "").split('/')[0].strip()
            return int(score_str)
    except Exception as e:
        print(f"   ⚠️ 점수 추출 오류: {e}")
    return 0

def generate_final_report(market_overview, good_reports, fng_data, mvrvz_data):
    """보고서 상단에 시황 및 지표 추가"""
    if not good_reports:
        print("📭 오늘 75점 이상인 코인이 없습니다. 리포트를 생성하지 않습니다.")
        return

    report_dir = "reports"
    os.makedirs(report_dir, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = os.path.join(report_dir, f"Crypto_Report_{date_str}.md")
    
    # --- [수정된 부분 ✨] 마크다운 구조 완전 업그레이드 ---
    report_content = f"# 🔥 오늘의 암호화폐 투자 하이라이트 - {date_str}\n\n"
    report_content += "---\n\n"
    
    # 1. 시장 주요 지표 대시보드
    report_content += "## 📈 시장 주요 지표\n"
    report_content += f"| 지표명 | 현재 상태 |\n"
    report_content += f"| :--- | :--- |\n"
    report_content += f"| **크립토 공포탐욕지수** | `{fng_data}` |\n"
    report_content += f"| **비트코인 MVRV Z-Score** | `{mvrvz_data}` |\n\n"
    
    # 2. AI 종합 시황 분석 (야후파이낸스 등 기반)
    report_content += "## 🌐 AI 종합 시황 분석\n"
    report_content += market_overview + "\n\n"
    
    report_content += "---\n\n"
    
    # 3. 75점 이상 코인 하이라이트
    report_content += "## 🏆 오늘의 추천 코인 (AI 점수 75점 이상)\n"
    report_content += "이 영역에는 당일 기술적 지표와 뉴스 분석을 통해 선정된 우량 코인의 개별 리포트가 담겨 있습니다.\n\n"
    report_content += "\n\n---\n\n".join(good_reports) 
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"📂 최종 분석 리포트가 생성되었습니다: {filename}")
