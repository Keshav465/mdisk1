# START OF FILE: iPMxBT-main/bot/utils.py

import asyncio
import functools
import re
import random
from pyrogram import enums, types, Client
from bot import Bot
from bot.config import Config, Script
from bot.database import user_db, group_db
from telegraph.aio import Telegraph
from collections import OrderedDict
import aiohttp
from urllib.parse import quote
from difflib import SequenceMatcher
from fuzzywuzzy import fuzz

# === YAHAN APNI WEBSITE KA LINK DAAL ===
# Example: "https://<tere-replit-ka-naam>.replit.dev/redirect.html"
# Isko khaali mat chhodna. Apni redirect.html file ka link yahan daal.
REDIRECT_PAGE_URL = "https://cornpay.pages.dev/redirect.html" # <-- YAHAN APNA LINK DAAL

async def short_link(api_key, base_site, link):
    if not api_key or not base_site:
        return link
    
    # === YAHAN HAI ASLI MAGIC ===
    # Bot ke link ko encode karo taaki URL me safe rahe
    encoded_bot_link = quote(link, safe='')
    # Apni redirect website ka link banao
    final_destination = f"{REDIRECT_PAGE_URL}?link={encoded_bot_link}"
    # ============================
    
    api_url = f"https://{base_site}/api"
    params = {'api': api_key, 'url': final_destination} # Ab GPlinks ko website ka link denge
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "success":
                        return data.get("shortenedUrl", link)
    except Exception as e:
        print(f"Error during link shortening: {e}")
    return link

# === NEECHE KA CODE WAISA HI HAI, KOI BADLAV NAHI ===

async def schedule_delete(message: types.Message, delay: int):
    await asyncio.sleep(delay)
    try: await message.delete()
    except: pass

async def filter_chat(c: Bot, query, chat_id_list=Config.DATABASE_CHANNEL, num_results=Config.LIMIT):
    query_list = query.split()
    results = []
    for q in query_list:
        for chat_id in chat_id_list:
            async for message in c.USER.search_messages(chat_id, query=q, limit=Config.LIMIT):
                if message.text or message.caption:
                    text = message.text or message.caption
                    file_name = text.splitlines()[0].lower()
                    ratio = fuzz.token_set_ratio(query, file_name)
                    results.append((message, ratio))
    results.sort(key=lambda x: x[1], reverse=True)
    return [r[0] for r in results[:num_results]]

async def create_telegraph_post(title, content):
    telegraph = Telegraph(random.choice(Config.TELEGRAPH_ACCESS_TOKEN))
    response = await telegraph.create_page(title, html_content=content)
    return response['url']

def remove_link(text):
    return re.sub(r'http\S+', '', text)

def remove_mention(text):
    return re.sub(r'@\S+', f"@{Config.USERNAME}", text)

async def short_from_text(api_key, base_site, text):
    # Yeh bekaar function hai, isko use nahi karna hai
    return text
