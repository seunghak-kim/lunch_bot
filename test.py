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

if __name__ == "__main__":
    asyncio.run(main())