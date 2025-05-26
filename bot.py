import discord
from discord.ext import commands
from datetime import datetime
import requests
import io
import logging
import os
from dotenv import load_dotenv
from kakao_image_crawler import crawl_kakao_images
from collections import defaultdict
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz
import json
import random
from discord import Embed
import asyncio

# Set up logging (console + file)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s',
                    handlers=[logging.FileHandler('bot.log', encoding='utf-8'), logging.StreamHandler()])

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not TOKEN:
    logging.error('DISCORD_BOT_TOKEN not found in environment variables!')
    exit(1)

# Discord settings
intents = discord.Intents.default()
intents.message_content = True
# If you need member events, enable this and also enable in Discord Developer Portal
# intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

today_menu_lunch_images = None  # 전역 변수로 선언
toady_menu_dinner_imgages = None 
KST = pytz.timezone('Asia/Seoul')
# 오늘 날짜  인트형으로 변경해서 seed 지정
today_date = datetime.now(KST).strftime("%Y-%m-%d")
today_date = int(today_date.replace("-", ""))
random.seed(today_date)

lock = asyncio.Lock()

async def scheduled_crawl():
    global today_menu_lunch_images
    loop = bot.loop
    today_menu_lunch_images = await loop.run_in_executor(None, crawl_kakao_images)
    logging.info(f"[스케줄] 오늘의 메뉴 이미지 미리 로드 완료: {today_menu_lunch_images}")

@bot.event
async def on_ready():
    global today_menu_lunch_images
    logging.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    logging.info('Bot is ready to receive commands.')
    print('------')
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('Bot is ready!')
    print('------')
    # 스케줄러 설정
    scheduler = AsyncIOScheduler(timezone=KST)
    scheduler.add_job(scheduled_crawl, 'cron', day_of_week='mon-fri', hour=9, minute=55)
    logging.info('Scheduled job for scheduled_crawl at 09:55 mon-fri.')
    scheduler.start()
    # 봇이 처음 켜질 때도 한 번 실행
    await scheduled_crawl()

@bot.command(name='점심')
async def send_lunch_menu(ctx):
    global today_menu_lunch_images
    now = datetime.now(KST)
    # 평일만 뽑기
    if now.weekday() >= 5:
        await ctx.send("🌟 주말에는 점심 메뉴를 제공하지 않습니다!")
        return
    if now.hour < 10:
        await ctx.send("⏰ 점심 메뉴는 오전 10시부터 확인할 수 있습니다!")
        return
    await ctx.send("🍱 오늘의 점심 메뉴를 불러오는 중입니다...")
    if not today_menu_lunch_images:
        await ctx.send("❌ 메뉴 정보를 가져오지 못했습니다. 로그를 확인해주세요.")
        return

    # 1. Remove duplicates
    unique_images = list(set(today_menu_lunch_images))

    # 2. Group by restaurant name (before first underscore)
    grouped = defaultdict(list)
    for img_path in unique_images:
        filename = os.path.basename(img_path)
        restaurant = filename.split('_')[0]
        grouped[restaurant].append(img_path)

    # 3. Send restaurant name, then images
    for restaurant, images in grouped.items():
        await ctx.send(f"🍽️ {restaurant} 오늘의 점심 메뉴입니다!")
        for img_path in images:
            with open(img_path, 'rb') as f:
                await ctx.send(file=discord.File(f))

@bot.command(name='저녁')
async def send_dinner_menu(ctx):
    global today_menu_lunch_images
    now = datetime.now(KST)
    if now.hour < 17:
        await ctx.send("⏰ 저녁 메뉴는 오후 5시부터 확인할 수 있습니다!")
        return
    await ctx.send("🍱 석식메뉴는 대륭 17차만 지원합니다")
    await ctx.send("개발중 입니다..")
    if not today_menu_lunch_images:
        await ctx.send("❌ 메뉴 정보를 가져오지 못했습니다. 로그를 확인해주세요.")
        return

@bot.command(name='음식추천')
async def recommend_food(ctx, *, category: str = None):
    logging.info(f"!음식추천 명령 실행 by {ctx.author} (ID: {ctx.author.id}), category: {category}")
    # Load restaurant data
    with open('restaurants.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Filter by category if provided
    if category:
        keywords = category.split()
        filtered = [r for r in data if any(kw in r['category'] for kw in keywords)]
    else:
        filtered = data
    if not filtered:
        await ctx.send(f'해당 카테고리의 음식점이 없습니다: {category}')
        return
    restaurant = random.choice(filtered)
    embed = Embed(title=restaurant['store_name'], description=f"카테고리: {restaurant['category']}")
    embed.add_field(name='평점', value=restaurant['rating'])
    embed.add_field(name='방문자 리뷰', value=restaurant['visited_review'])
    embed.add_field(name='블로그 리뷰', value=restaurant['blog_review'])
    embed.add_field(name='주소', value=restaurant['address'], inline=False)
    embed.add_field(name='전화번호', value=restaurant.get('tell_num', restaurant.get('phone_num', '없음')))
    embed.add_field(name='영업시간', value=restaurant['business_hours'], inline=False)
    embed.set_footer(text=f"추천 수: {restaurant.get('recommand', 0)}")
    msg = await ctx.send(embed=embed)
    await msg.add_reaction('👍')  # 추천
    await msg.add_reaction('👎')  # 비추천

    # Log user recommendation
    log_entry = {
        "user_id": ctx.author.id,
        "username": str(ctx.author),
        "store_name": restaurant['store_name'],
        "category": restaurant['category'],
        "timestamp": datetime.now().isoformat()
    }
    with open('recommend_log.jsonl', 'a', encoding='utf-8') as logf:
        logf.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    logging.info(f"추천 로그 기록: {log_entry}")

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return
    msg = reaction.message
    if msg.embeds and msg.embeds[0].footer.text.startswith("추천 수:"):
        store_name = msg.embeds[0].title
        if str(reaction.emoji) == '👍':
            async with lock:
                # 실제 메시지의 👍 개수로 카운트
                count = 0
                for react in msg.reactions:
                    if str(react.emoji) == '👍':
                        users = [u async for u in react.users()]
                        count = len([u for u in users if not u.bot])
                with open('restaurants.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for r in data:
                    if r['store_name'] == store_name:
                        r['recommand'] = count
                        break
                with open('restaurants.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                logging.info(f"{store_name} 추천 카운트 동기화: {count} (by {user})")

@bot.event
async def on_reaction_remove(reaction, user):
    if user.bot:
        return
    msg = reaction.message
    if msg.embeds and msg.embeds[0].footer.text.startswith("추천 수:"):
        store_name = msg.embeds[0].title
        if str(reaction.emoji) == '👍':
            async with lock:
                count = 0
                for react in msg.reactions:
                    if str(react.emoji) == '👍':
                        users = [u async for u in react.users()]
                        count = len([u for u in users if not u.bot])
                with open('restaurants.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for r in data:
                    if r['store_name'] == store_name:
                        r['recommand'] = count
                        break
                with open('restaurants.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                logging.info(f"{store_name} 추천 카운트 동기화(해제): {count} (by {user})")

# 리더보드 

@bot.command()
async def 리더보드(ctx):
    with open("restaurants.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # 추천수 기준 내림차순 정렬
    sorted_data = sorted(data, key=lambda x: x.get("recommand", 0), reverse=True)

    # 상위 5개 추출
    top5 = sorted_data[:5]

    embed = discord.Embed(
        title="🏆 추천 맛집 리더보드 (TOP 5)",
        description="많이 추천받은 순으로 정렬했어요!",
        color=0xf1c40f
    )

    for i, store in enumerate(top5, start=1):
        embed.add_field(
            name=f"{i}️⃣ {store['store_name']}",
            value=f"카테고리: {store['category']} | 👍 추천 수: {store['recommand']}",
            inline=False
        )

    await ctx.send(embed=embed)

# Basic error handler
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return # Don't send a message for unknown commands
    logging.error(f"An error occurred during command execution: {error}", exc_info=True) # Log with traceback
    await ctx.send(f"😥 명령어 실행 중 오류가 발생했습니다: {str(error)}")


# clear recommand 만들기 
def clear_recommand():
    with open("restaurants.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    for r in data:
        r["recommand"] = 0
    with open("restaurants.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    bot.run(TOKEN)