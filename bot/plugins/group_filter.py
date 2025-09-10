# START OF FILE: bot/plugins/group_filter.py

import re
import asyncio
from pyrogram import Client, filters, types as t, enums
from bot.config import Config, Script
from bs4 import BeautifulSoup
from bot.utils import filter_chat, create_telegraph_post, short_from_text, remove_link, remove_mention, is_premium_group
from bot.database import group_db
from bot.database.subscribers import sub_db

@Client.on_message(filters.text & ~filters.bot & ~filters.via_bot, group=3)
async def main_filter_handler(c: Client, m: t.Message):
    if m.text.startswith("/"): return
    if re.findall(r"((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", m.text): return
    
    query = m.text
    
    if m.chat.type == enums.ChatType.PRIVATE:
        user_id = m.from_user.id
        # Admin ke liye bypass
        if user_id in Config.ADMINS:
            await run_search(c, m, query, use_shortener=False)
            return
        
        # Normal users ke liye subscription check
        is_subbed = await sub_db.is_subscribed(user_id)
        if is_subbed:
            await run_search(c, m, query, use_shortener=False)
        else:
            buttons = [
                [t.InlineKeyboardButton("📺 Download With Ads 📺", callback_data=f"ads_search_{query[:50]}")],
                [t.InlineKeyboardButton("💎 Go Premium - No Ads 💎", callback_data="go_premium")]
            ]
            await m.reply(
                "**Hey Buddy!\nYou Are Using The Free Version 😊**\n\nSelect And Enjoy Your Choice 👇",
                reply_markup=t.InlineKeyboardMarkup(buttons)
            )
    elif m.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        # Group mein hamesha ad-wala search hoga
        await run_search(c, m, query, use_shortener=True)

async def run_search(c: Client, m: t.Message, query: str, use_shortener: bool = False):
    sts = await m.reply("`Searching...`")
    
    # Settings from your old code
    database_channels = Config.DATABASE_CHANNEL
    shortener_api = Config.SHORTENER_API
    shortener_site = Config.SHORTENER_SITE
    
    if m.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        if await is_premium_group(m.chat.id):
            group_info = await group_db.get_group(m.chat.id)
            database_channels = [group_info["index_channel"]] if group_info["index_channel"] else Config.DATABASE_CHANNEL
            # Paid groups don't use shortener by default
            use_shortener = False
            if group_info["shortener_api"]: # unless they set one
                shortener_api = group_info["shortener_api"]
                shortener_site = group_info["shortener_site"]
                use_shortener = True

    try:
        results = await filter_chat(c, query, database_channels)
    except Exception as e:
        await sts.edit(f"Search error: {e}")
        return

    if not results:
        reply = query.replace(" ", "+")
        reply_markup = t.InlineKeyboardMarkup([[t.InlineKeyboardButton("🔍 Click to Check Spelling✅", url=f"https://www.google.com/search?q={reply}+movie")]])
        await sts.edit(Script.NO_REPLY_TEXT.format(query), disable_web_page_preview=True, reply_markup=reply_markup)
        return

    # YOUR OLD, WORKING LINK GENERATION LOGIC
    template = "<aside><b>{i}. {title}</b><br><a href='{link}'>👉 Click Here To Download</a></aside><hr>"
    bin_text = ""
    i = 1
    bot_username = (await c.get_me()).username
    
    for result in results:
        if not (result.document or result.video):
            continue # Sirf file waale message lo

        text_ = result.text or result.caption
        title = remove_mention(remove_link(text_.splitlines()[0]))
        link = f"https://telegram.dog/{bot_username}?start=file_{result.id}_{result.chat.id}"
        
        bin_text += template.format(i=i, title=title, link=link)
        i += 1

    if not bin_text:
        await sts.edit(Script.NO_REPLY_TEXT.format(query))
        return

    if use_shortener and shortener_api and shortener_site:
        bin_text = await short_from_text(shortener_api, shortener_site, bin_text)
    
    text = f"<h3>Results for {query}</h3><br><h4>Total results: {i-1}</h4><br><hr>{bin_text}"
    soup = BeautifulSoup(text, "html.parser")
    formatted_text = soup.prettify()
    reply_url = await create_telegraph_post(query, formatted_text)
    
    await sts.edit(Script.RESULTS_MESSAGE.format(query=query.upper(), url=reply_url), disable_web_page_preview=True)
