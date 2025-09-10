# START OF FILE: bot/plugins/search_logic.py (FINAL CLEAN VERSION)

import asyncio
from pyrogram import Client, types as t, enums
from bot.config import Config, Script
from bs4 import BeautifulSoup
from bot.utils import (
    filter_chat, create_telegraph_post, remove_link, 
    remove_mention, schedule_delete, short_link # Naye function ko import kiya
)

async def perform_search(c: Client, m: t.Message, query: str, use_shortener: bool = False):
    database_channels = Config.DATABASE_CHANNEL
    if not database_channels:
        return await m.reply("Database channel not configured.")

    if "Searching" not in m.text:
        sts = await m.reply("`Searching...`")
    else:
        sts = m

    try:
        results = await filter_chat(c, query, database_channels)
    except Exception as e:
        print(f"Error during filter_chat: {e}")
        return await sts.edit("An error occurred while searching.")

    if not results:
        no_results_msg = await not_found_response(sts, query)
        asyncio.create_task(schedule_delete(no_results_msg, 300))
        return

    template = "<aside><b>{i}. {title}</b><br><a href='{link}'>👉 Click Here To Download</a></aside><hr>"
    bin_text = ""
    i = 1
    bot_username = (await c.get_me()).username
    
    # === YEH HAI FINAL WORKING LOGIC ===
    for result in results:
        # Sirf un results ko lo jinme file hai
        if not (result.document or result.video):
            continue

        text_ = result.text or result.caption
        title = remove_mention(remove_link(text_.splitlines()[0]))
        
        # Pehle original, lamba link banayenge
        long_link = f"https://telegram.dog/{bot_username}?start=file_{result.id}_{result.chat.id}"
        
        # Agar free user hai, to is ek link ko short karenge
        final_link = long_link
        if use_shortener and Config.SHORTENER_API and Config.SHORTENER_SITE:
            final_link = await short_link(Config.SHORTENER_API, Config.SHORTENER_SITE, long_link)

        bin_text += template.format(i=i, title=title, link=final_link)
        i += 1
    # ==================================

    if not bin_text:
        no_results_msg = await not_found_response(sts, query)
        asyncio.create_task(schedule_delete(no_results_msg, 300))
        return
    
    text = f"<h3>Results for {query}</h3><br><h4>Total results: {i-1}</h4><br><hr>{bin_text}"
    soup = BeautifulSoup(text, "html.parser")
    formatted_text = soup.prettify()
    reply_url = await create_telegraph_post(query, formatted_text)

    reply_markup = None
    if m.chat.type == enums.ChatType.PRIVATE and Config.RESULTS_HOW_TO_DOWNLOAD_LINK and Config.REQUEST_MOVIE_URL:
        reply_markup = t.InlineKeyboardMarkup(
            [
                [t.InlineKeyboardButton("How to Download?", url=Config.RESULTS_HOW_TO_DOWNLOAD_LINK)],
                [t.InlineKeyboardButton("Request Movie", url=Config.REQUEST_MOVIE_URL)]
            ]
        )

    final_results_msg = await sts.edit(
        Script.RESULTS_MESSAGE.format(query=query.upper(), url=reply_url),
        disable_web_page_preview=True,
        reply_markup=reply_markup
    )
    if m.chat.type == enums.ChatType.PRIVATE:
        asyncio.create_task(schedule_delete(final_results_msg, 300))

async def not_found_response(m, query):
    reply = query.replace(" ", "+")
    reply_markup = t.InlineKeyboardMarkup(
        [[t.InlineKeyboardButton("🔍 Click to Check Spelling✅", url=f"https://www.google.com/search?q={reply}+movie")]]
    )
    return await m.edit(Script.NO_REPLY_TEXT.format(query), disable_web_page_preview=0, reply_markup=reply_markup)
