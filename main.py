import os
import re
import urllib.request
import xml.etree.ElementTree as ET
import google.generativeai as genai

# 1. 환경 변수 로드
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Gemini API 설정
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def send_telegram_message(message):
    """텔레그램 메시지 발송 함수"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ 텔레그램 토큰 또는 Chat ID가 설정되지 않았습니다.")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = urllib.parse.urlencode({
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': False
    }).encode('utf-8')
    
    try:
        req = urllib.request.Request(url, data=params)
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"⚠️ 텔레그램 발송 실패: {e}")

def summarize_with_gemini(text):
    """Gemini AI를 사용한 뉴스 요약 함수"""
    if not GEMINI_API_KEY:
        return "Gemini API 키가 없어 요약을 생성할 수 없습니다."
    
    try:
        # 지원 가능한 최신 Flash 모델 사용
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"다음 뉴스 내용을 바탕으로 핵심 내용을 2-3줄로 명확하게 요약해 주세요:\n\n{text}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"❌ Gemini AI 요약 생성 실패: {e}")
        return "AI 요약 생성 중 오류가 발생했습니다."

def load_sent_links():
    """이미 발송한 링크 목록 불러오기"""
    if os.path.exists("sent_links.txt"):
        with open("sent_links.txt", "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_sent_link(link):
    """발송한 링크 저장하기"""
    with open("sent_links.txt", "a", encoding="utf-8") as f:
        f.write(f"{link}\n")

def main():
    print("🚀 실시간 뉴스 수집 및 AI 브리핑 로봇 실행...")
    
    sent_links = load_sent_links()
    
    # 네이버 뉴스 RSS 예시 (필요시 키워드/RSS URL 변경 가능)
    rss_url = "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"
    
    try:
        req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        xml_data = response.read()
        root = ET.fromstring(xml_data)
        
        items = root.findall('.//item')
        count = 0
        
        for item in items[:5]:  # 상위 5개 기사 처리
            title = item.find('title').text if item.find('title') is not None else "제목 없음"
            link = item.find('link').text if item.find('link') is not None else ""
            description = item.find('description').text if item.find('description') is not None else ""
            
            # HTML 태그 제거
            clean_description = re.sub('<[^<]+?>', '', description)
            
            if link and link not in sent_links:
                print(f"📰 새로운 뉴스 처리 중: {title}")
                
                # Gemini AI 요약 생성
                summary = summarize_with_gemini(clean_description or title)
                
                # 텔레그램 메시지 구성
                message = f"<b>[실시간 뉴스 브리핑]</b>\n\n" \
                          f"📌 <b>{title}</b>\n\n" \
                          f"🤖 <b>AI 요약:</b>\n{summary}\n\n" \
                          f"🔗 <a href='{link}'>기사 원문 보기</a>"
                
                send_telegram_message(message)
                save_sent_link(link)
                count += 1
                
        print(f"🎉 총 {count}건의 뉴스를 브리핑하여 발송 완료했습니다.")
        
    except Exception as e:
        print(f"❌ 뉴스 수집 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
