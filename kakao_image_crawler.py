import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import re
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import shutil

def get_today_str_with_weekday():
    today = datetime.now()
    weekday_kr = ['월', '화', '수', '목', '금', '토', '일']
    return f"{today.month}월{today.day}일 {weekday_kr[today.weekday()]}요일"

def get_today_str():
    return datetime.now().strftime('%Y_%m_%d')

def parse_today_cards(cards, key):
    """오늘 날짜에 해당하는 카드만 반환"""
    today = datetime.now()
    today_cards = []
    for card in cards:
        try:
            title_strong = card.select_one('strong.tit_card')
            if not title_strong:
                continue
            title_text = title_strong.text.strip()
            is_today = False

            if key == "대륭18차":
                match = re.search(r'(\d{4})년 (\d{2})월 (\d{2})일', title_text)
                if match:
                    y, m, d = match.groups()
                    card_date = datetime(int(y), int(m), int(d))
                    if card_date.date() == today.date():
                        is_today = True
            else:  # 대륭17차, 에이스하이엔드10차
                match = re.search(r'(\d{1,2})월(\d{1,2})일', title_text.replace(" ", ""))
                if match:
                    m, d = match.groups()
                    card_date = datetime(today.year, int(m), int(d))
                    if card_date.date() == today.date():
                        is_today = True
            if is_today:
                today_cards.append(card)
        except Exception as e:
            print(f"Error processing card: {e}")
            continue
    return today_cards

def extract_img_url_from_thumb(thumb_div):
    """썸네일 div에서 이미지 URL 추출"""
    if thumb_div and 'style' in thumb_div.attrs:
        style = thumb_div['style']
        match = re.search(r'url\(["\']?(.*?)["\']?\)', style)
        if match:
            return match.group(1)
    return None

def save_image(img_url, filename):
    """이미지 다운로드 및 저장"""
    response = requests.get(img_url)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"이미지 저장됨: {filename}")
        return True
    return False

def crawl_kakao_images():
    IMAGES_DIR = Path("./kakao_images")
    IMAGES_DIR.mkdir(exist_ok=True)

    kakao_urls = {
        "대륭18차": "https://pf.kakao.com/_YgxdPT/posts",
        "대륭17차": "https://pf.kakao.com/_xfWxfCxj/posts",
        "에이스하이엔드10차": "https://pf.kakao.com/_rXxkCn/posts"
    }

    error_img_map = {
        "대륭18차": './kakao_error_img/대륭18.jpg',
        "대륭17차": './kakao_error_img/대륭17.jpg',
        "에이스하이엔드10차": './kakao_error_img/에이스하이엔드10.jpg'
    }

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    saved_files = []
    today_file_str = get_today_str()

    try:
        for key, url in kakao_urls.items():
            filename = IMAGES_DIR / f"{key}_{today_file_str}.jpg"
            if filename.exists():
                os.remove(filename)

            print(f"크롤링 채널: {key} ({url})")
            driver.get(url)
            time.sleep(5)
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            cards = soup.select('div.wrap_webview div.area_card')
            found_today = False

            # 카드 선택
            if key == "에이스하이엔드10차":
                today_str = get_today_str_with_weekday()
                target_card = None
                for card in cards:
                    title_strong = card.select_one('strong.tit_card')
                    if not title_strong:
                        continue
                    title_text = title_strong.text.strip()
                    if today_str in title_text:
                        target_card = card
                        break
                if target_card:
                    thumb_divs = target_card.select('div.wrap_fit_thumb')
                    if thumb_divs:
                        img_url = extract_img_url_from_thumb(thumb_divs[0])
                        if img_url and save_image(img_url, filename):
                            saved_files.append(str(filename))
                            found_today = True
            else:
                today_cards = parse_today_cards(cards, key)
                target_card = today_cards[0] if today_cards else None
                if target_card:
                    thumb_div = target_card.select_one('div.wrap_fit_thumb')
                    img_url = extract_img_url_from_thumb(thumb_div)
                    if img_url and save_image(img_url, filename):
                        saved_files.append(str(filename))
                        found_today = True

            # 에러 이미지 처리
            if not found_today:
                error_img = error_img_map.get(key)
                if error_img and os.path.exists(error_img):
                    if error_img not in saved_files:
                        saved_files.append(error_img)
                        print(f"에러 이미지 추가됨: {error_img}")
                else:
                    print(f"에러 이미지가 존재하지 않음: {error_img}")

    finally:
        driver.quit()
    return saved_files

def crawl_kakao_images_dinner():
    pass

if __name__ == "__main__":
    result = crawl_kakao_images()
    print("Saved files:", result)