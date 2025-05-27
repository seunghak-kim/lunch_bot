import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from zoneinfo import ZoneInfo  # Python 3.9+

KST = ZoneInfo("Asia/Seoul")

def hello_world():
    print(f"[{datetime.now(tz=KST)}] 안녕하세요!")

async def main():
    scheduler = AsyncIOScheduler(timezone=KST)
    scheduler.add_job(hello_world, 'interval', seconds=5)
    scheduler.start()

    print("⏰ KST 기준 스케줄러 작동 중...")

    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        print("종료 중...")

import json

# 카테고리 또는 가게명에 따른 메뉴 키워드 매핑
keyword_map = {
    "분식": ["김밥", "라면", "떡볶이", "순대", "우동"],
    "중식당": ["짜장면", "짬뽕", "탕수육", "볶음밥", "마파두부"],
    "국밥": ["돼지국밥", "소고기국밥", "순댓국", "감자탕"],
    "찌개": ["된장찌개", "김치찌개", "순두부찌개", "부대찌개"],
    "전골": ["곱창전골", "버섯전골"],
    "죽": ["전복죽", "소고기야채죽", "호박죽", "닭죽"],
    "고기": ["삼겹살", "목살", "항정살", "돼지불백"],
    "일식": ["돈가스", "카레", "우동", "소바", "연어덮밥"],
    "샐러드": ["닭가슴살 샐러드", "연어 샐러드", "발사믹 샐러드"],
    "곱창": ["소곱창", "막창", "대창", "곱창전골"],
    "요리주점": ["양꼬치", "꿔바로우", "마라샹궈"],
}

def infer_menu_keywords(store):
    category = store.get("category", "").lower()
    name = store.get("store_name", "").lower()

    keywords = set()

    for key, menu_items in keyword_map.items():
        if key in category or key in name:
            keywords.update(menu_items)

    return list(keywords)

# 파일 읽기
with open("restaurants.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# menu_keywords 추가
for store in data:
    store["menu_keywords"] = infer_menu_keywords(store)

# 파일 저장
with open("restaurants_with_keywords.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("✅ menu_keywords 추가 완료! → restaurants_with_keywords.json 저장됨")


if __name__ == "__main__":
    asyncio.run(main())