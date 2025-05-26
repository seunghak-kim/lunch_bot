from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import csv
import selenium.common.exceptions

# 크롬 드라이버 실행 (환경변수 등록 시 경로 생략 가능)
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 20)

driver.get("https://map.naver.com/v5/")

# 1. 검색창 대기 및 검색어 입력
search_box = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "input_search")))
search_box.send_keys("독산역 맛집")
search_box.send_keys(Keys.ENTER)

# 2. 검색 결과 iframe 대기 및 전환
iframe = None
for _ in range(40):  # 최대 40초 동안 반복 체크
    try:
        iframe = driver.find_element(By.CSS_SELECTOR, "iframe#searchIframe")
        break
    except selenium.common.exceptions.NoSuchElementException:
        time.sleep(1)
if iframe is None:
    raise Exception("iframe#searchIframe을 찾지 못했습니다.")
driver.switch_to.frame(iframe)

# 3. 스크롤 내리기
scroll_div = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[3]/div/div[2]/div[1]")))
for _ in range(5):
    driver.execute_script("arguments[0].scrollBy(0,2000);", scroll_div)
    time.sleep(1)

# 4. CSV 파일 준비
file = open('stores.csv', mode='w', newline='', encoding='utf-8')
writer = csv.writer(file)
writer.writerow(["place", "rate", "address", "info", "image"])
final_result = []

# 5. 페이지 반복
for i in range(2, 6):  # 2~5페이지
    stores = driver.find_elements(By.CSS_SELECTOR, "li.VLTHu.OW9LQ")  # 최신 클래스명 확인 필요
    for store in stores:
        try:
            name = store.find_element(By.CSS_SELECTOR, "span.YwYLL").text
        except:
            name = ''
        try:
            rating = store.find_element(By.CSS_SELECTOR, "span.YzBgS").text
        except:
            rating = ''
        try:
            img_tag = store.find_element(By.CSS_SELECTOR, "img.K0PDV")
            img_src = img_tag.get_attribute('src')
        except:
            img_src = ''
        try:
            address = store.find_element(By.CSS_SELECTOR, "span.Pb4bU").text
        except:
            address = ''
        try:
            info = store.find_element(By.CSS_SELECTOR, "span.YzBgS").text
        except:
            info = ''
        store_info = {
            'placetitle': name,
            'rate': rating,
            'address': address,
            'info': info,
            'image': img_src
        }
        print(name, rating, address, img_src, info)
        print("*" * 50)
        final_result.append(store_info)

    # 다음 페이지 이동
    try:
        next_button = driver.find_element(By.LINK_TEXT, str(i))
        next_button.click()
        time.sleep(3)
    except Exception as e:
        print(f"페이지 {i} 이동 실패: {e}")
        break

# 6. CSV 저장
for result in final_result:
    writer.writerow([result['placetitle'], result['rate'], result['address'], result['info'], result['image']])

file.close()
print(final_result)
driver.quit()