import json
import os
import requests
import markdown  # HTML 변환용
import sass      # SCSS 컴파일용
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
    # [수정됨 ✨] 코인이 없어도 종료(return)하지 않고 무조건 리포트 생성 로직으로 넘어감

    report_dir = "reports"
    os.makedirs(report_dir, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    md_filename = os.path.join(report_dir, f"Crypto_Report_{date_str}.md")
    html_filename = os.path.join(report_dir, f"Crypto_Report_{date_str}.html")
    
    # 마크다운 뼈대 만들기 (이 부분은 코인 유무와 상관없이 항상 들어감)
    report_content = f"# 🔥 오늘의 암호화폐 투자 하이라이트 - {date_str}\n\n"
    report_content += "---\n\n"
    report_content += "## 📈 시장 주요 지표\n"
    report_content += f"| 지표명 | 현재 상태 |\n| :--- | :--- |\n"
    report_content += f"| **크립토 공포탐욕지수** | `{fng_data}` |\n"
    report_content += f"| **비트코인 MVRV Z-Score** | `{mvrvz_data}` |\n\n"
    report_content += "## 🌐 AI 종합 시황 분석\n"
    report_content += market_overview + "\n\n---\n\n"
    report_content += "## 🏆 오늘의 추천 코인 (AI 점수 75점 이상)\n\n"

    # 코인이 없을 때와 있을 때 분기 처리
    if not good_reports:
        report_content += "> **오늘은 AI 분석 결과 75점을 넘는 추천 코인이 없습니다. 무리한 투자보다는 시장을 관망하는 것을 추천합니다.**\n"
        print("📭 75점 이상 코인이 없지만, 시황 대시보드 리포트를 생성합니다.")
    else:
        report_content += "\n\n---\n\n".join(good_reports)

    # 1. MD 파일 저장
    with open(md_filename, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"📂 MD 리포트 생성 완료: {md_filename}")

    # 2. SCSS를 CSS로 컴파일해서 최상위 폴더에 저장 (index.html이 읽을 수 있게)
    if os.path.exists("style.scss"):
        compiled_css = sass.compile(filename="style.scss")
        with open("style.css", "w", encoding="utf-8") as f:
            f.write(compiled_css)
    else:
        print("⚠️ style.scss 파일이 없습니다. 기본 스타일로 진행합니다.")

    # 3. MD 내용을 HTML로 변환
    html_body = markdown.markdown(report_content, extensions=['tables'])
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crypto Report - {date_str}</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        {html_body}
    </div>
</body>
</html>"""

    # 4. 개별 날짜용 HTML 저장
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # 5. [깃허브 페이지용] 최상위 폴더에 무조건 index.html 덮어쓰기
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("📄 웹 배포용 index.html 생성 완료!")
