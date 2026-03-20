import os
import requests

def send_mobile_summary(fng_data, mvrvz_data, good_reports):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("⚠️ 텔레그램 토큰이나 챗 ID가 설정되지 않아 알림을 건너뜁니다.")
        return

    # 모바일 화면에 맞게 핵심만 요약
    text = f"🔥 *오늘의 암호화폐 요약*\n\n"
    text += f"📊 *시장 지표*\n"
    text += f"• 공포탐욕지수: `{fng_data}`\n"
    text += f"• MVRV Z-Score: `{mvrvz_data}`\n\n"
    
    text += f"🏆 *추천 코인 (75점 이상)*\n"
    if not good_reports:
        text += "오늘은 추천 코인이 없어. 관망장이야! ☕️\n"
    else:
        for report in good_reports:
            # 리포트 본문은 빼고 제목(코인 이름과 점수)만 첫 줄에서 추출
            first_line = report.split('\n')[0].replace("### ", "▪️ ").replace("**", "")
            text += f"{first_line}\n"
            
    text += f"\n👉 [웹에서 리포트 전문 보기](https://darkmirr-bitcoin.github.io/CryptoReport/)"
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True # 링크 미리보기 방지 (깔끔하게)
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("📱 텔레그램 모바일 요약본 전송 완료!")
    except Exception as e:
        print(f"❌ 텔레그램 전송 실패: {e}")
