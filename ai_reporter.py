import json
import os
import requests
from google import genai
from google.genai import types
from datetime import datetime

# secrets.json 설정
with open("secrets.json", "r") as f:
    secrets = json.load(f)
GEMINI_API_KEY = secrets.get("gemini_api_key")

MODEL_ID = "gemini-2.0-flash"

def fetch_fear_and_greed():
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

def analyze_market_overview(client, indicators):
    print("   📰 외신(Yahoo Finance 등) 기반 시황 요약 중...")
    prompt = f"""
    당신은 선임 암호화폐 시장 전략가입니다. 
    구글 검색 도구를 사용하여 야후 파이낸스, 코인데스크, 블룸버그 등 주요 외신에서 지난 24시간 동안 보도된 암호화폐 뉴스를 검색하세요.

    [현재 시장 주요 지표]
    - 공포탐욕지수: {indicators['fng']}
    - 비트코인 MVRV Z-Score: {indicators['mvrv']}

    [요청 사항]
    1. 시황 총평: 시장의 전반적인 투자 심리를 강렬한 한 문장으로 요약하세요.
    2. 핵심 드라이버 (주요 뉴스 3): 시장에 가장 큰 영향을 미친 뉴스를 야후 파이낸스 등을 인용하여 3가지 요약하세요.
    3. 지표 해석: 공포탐욕지수와 MVRV Z-Score를 바탕으로 현재 시장 위치를 분석하세요.

    [출력 형식] - 마크다운
    ### 🌐 오늘의 암호화폐 시황 총평
    > ...

    #### 📍 핵심 시장 드라이버 및 뉴스 분석
    - ...
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
        return "시황 분석 데이터를 가져오지 못했습니다."

def analyze_with_gemini(client, ticker_display, data_row):
    current_price = data_row[2]
    trend = data_row[4]
    volume_str = data_row[5]
    macd = data_row[7]
    rsi = data_row[8]

    prompt = f"""
    당신은 전문 퀀트 분석가입니다. 실시간 검색을 통해 [{ticker_display}]의 최신 뉴스를 찾고 아래 지표와 함께 분석하세요.

    [기술적 지표]
    - 현재가: {current_price}
    - 이평선 추세: {trend}
    - 거래량 강도: {volume_str}
    - MACD: {macd}
    - RSI(14): {rsi}

    [출력 형식] - 마크다운 필수, '---' 구분선 필수
    ---
    SCORE: [100점 만점 기준 점수 숫자만, 예: 85]
    ---
    ### 📰 최신 뉴스 요약
    - ...
    
    ### 📊 종합 분석
    ...
    
    ### 💡 투자의견 및 근거
    - **점수**: [점수]/100
    - **근거**: ...
    """
    print(f"   🤖 [{ticker_display}] 개별 분석 및 뉴스 검색 중...")
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
        return None

def extract_score(ai_text):
    if not ai_text: return 0
    try:
        if "SCORE:" in ai_text:
            score_part = ai_text.split("SCORE:")[1].split('\n')[0].strip()
            score_str = score_part.replace("[", "").replace("]", "").split('/')[0].strip()
            return int(score_str)
    except:
        pass
    return 0

def generate_final_report(market_overview, good_reports, fng_data, mvrvz_data):
    if not good_reports:
        print("📭 오늘 75점 이상인 코인이 없습니다. 리포트를 생성하지 않습니다.")
        return
