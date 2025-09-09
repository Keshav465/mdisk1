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
from difflib import SequenceMatcher
from fuzzywuzzy import fuzz

async def schedule_delete(message: types.Message, delay: int):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception as e:
        print(f"Error while deleting message {message.id}: {e}")

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

INTERVALS = OrderedDict([
    ('millennium', 31536000000),
    ('century', 3153600000),
    ('year', 31536000),
    ('month', 2627424),
    ('week', 604800),
    ('day', 86400),
    ('hour', 3600),
    ('minute', 60),
    ('second', 1)
])

async def filter_chat(c: Bot, query, chat_id_list=Config.DATABASE_CHANNEL, offset=0, filter: enums.MessagesFilter = enums.MessagesFilter.EMPTY, num_results=Config.LIMIT):
    query_list = query.split()
    results = []
    for q in query_list:
        for chat_id in chat_id_list:
            async for message in c.USER.search_messages(chat_id, query=q, offset=offset, filter=filter, limit=Config.LIMIT):
                if message.text or message.caption:
                    text = message.text or message.caption
                    file_name = text.splitlines()[0].lower()
                    ratio = fuzz.token_set_ratio(query, file_name)
                    results.append((message, ratio))
    results.sort(key=lambda x: x[1], reverse=True)
    return [r[0] for r in results[:num_results]]

async def add_new_user(c, user_id, mention):
    is_user = await user_db.is_user_exist(user_id)
    if not is_user:
        await user_db.get_user(user_id)
        await c.send_message(Config.LOG_CHANNEL, f"#NewUser\n\nUser ID: `{user_id}`\nName: {mention}")

async def create_telegraph_post(title, content):
    telegraph = Telegraph(random.choice(Config.TELEGRAPH_ACCESS_TOKEN))
    response = await telegraph.create_page(title, html_content=content)
    return response['url']

def remove_link(text):
    pattern = r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)'
    return re.sub(pattern, "", text)

def remove_mention(text):
    pattern = r'@(\w+)'
    return re.sub(pattern, f"@{Config.USERNAME}", text)

async def group_admin_check(client, userid, message):
    if not userid: return
    if userid in Config.ADMINS: return True
    st = await client.get_chat_member(message.chat.id, userid)
    return st.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]

def is_int(string):
    try:
        int(string)
        return True
    except ValueError:
        return False

async def is_bot_admin(c, channel_id):
    if channel_id:
        try:
            await c.create_chat_invite_link(channel_id)
            return True
        except Exception:
            return
    return True

async def is_premium_group(group_id):
    return bool(await group_db.is_group_verified(group_id))

def group_wrapper(func):
    @functools.wraps(func)
    async def wrapper(client, message):
        user_id = getattr(message.from_user, "id", None)
        chat_id = getattr(message.chat, "id", None)
        is_admin = await group_admin_check(client, user_id, message)
        if not is_admin: return
        if not await is_premium_group(chat_id):
            await message.reply(Script.NO_SUBSCRIPTION_TEXT)
            return
        return await func(client, message)
    return wrapper

def human_time(seconds):
    if seconds is None: return "N/A"
    if not isinstance(seconds, (int, float)): return str(seconds)
    if seconds < 60: return f"{int(seconds)} seconds"
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    result = []
    if days > 0: result.append(f"{int(days)} days")
    if hours > 0: result.append(f"{int(hours)} hours")
    if minutes > 0: result.append(f"{int(minutes)} minutes")
    return ", ".join(result) if result else "0 seconds"

async def get_group_info_button(group_id: int):
    btn = [[types.InlineKeyboardButton(f"Add {human_time(s)}", callback_data=f'validity#{group_id}#{s}')] for s in Config.VALIDITY]
    btn.append([types.InlineKeyboardButton("Remove access", callback_data=f"removeaccess#{group_id}")])
    btn.append([types.InlineKeyboardButton("Close", callback_data="delete")])
    return btn

async def get_group_info_text(client, group_id: int):
    group = await group_db.get_group(group_id)
    expiry_date, time_remaining = await group_db.expiry_date(group_id)
    sub_date = group['last_verified']
    if not await group_db.is_group_verified(group_id):
        sub_date = expiry_date = time_remaining = "Expired"
    tg_group = await client.get_chat(group_id)
    return Script.GROUP_INFO_TEXT.format(
        group_id=group_id,
        group_link=tg_group.invite_link,
        subscription_date=sub_date,
        expiry_date=expiry_date,
        time_remaining=human_time(time_remaining) if isinstance(time_remaining, int) else time_remaining,
        shortener_api=group['shortener_api'],
        shortener_site=group['shortener_site'],
        auto_delete=group['auto_delete'],
        auto_delete_time=group['auto_delete_time'],
        index_channel=group['index_channel']
    )

# === YAHAN BADA BADLAV KIYA GAYA HAI ===
# shortzy library ko hata diya hai aur GPlinks se seedha baat karne ka code daala hai
async def short_link(api_key, base_site, link):
    if not api_key or not base_site:
        return link
    
    # GPlinks ke liye API URL (assume kar rahe hain ki site ka naam gplinks.co jaisa hai)
    api_url = f"https://{base_site}/api"
    params = {'api': api_key, 'url': link}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "success":
                        return data.get("shortenedUrl", link)
                    else:
                        print(f"GPlinks API Error: {data.get('message', 'Unknown error')}")
                        return link
                else:
                    print(f"GPlinks request failed with status: {response.status}")
                    return link
    except Exception as e:
        print(f"Error during link shortening: {e}")
        return link

async def short_from_text(api_key, base_site, text):
    # Yeh bekaar function hata diya gaya hai. Ab iska koi kaam nahi.
    # Isko call karne se koi error na aaye, isliye bas text wapas bhej rahe hain.
    return text
