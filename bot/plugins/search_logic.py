# START OF FILE: iPMxBT-main/bot/plugins/search_logic.py

import asyncio
from pyrogram import Client, types as t, enums
from bot.config import Config, Script
from bs4 import BeautifulSoup
from bot.utils import (
    filter_chat, create_telegraph_post, 
    remove_link, remove_mention, schedule_delete
)

# === IS POORE FUNCTION KO REPLACE KAR DIJIYE ===
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
        no_results_msg = await sts.edit(Script.NO_REPLY_TEXT.format(query))
        asyncio.create_task(schedule_delete(no_results_msg, 300))
        return

    template = "<aside><b>{i}. {title}</b><br><a href='{link}'>👉 Click Here To Download</a></aside><hr>"
    bin_text = ""
    i = 1
    bot_username = (await c.get_me()).username
    
    for result in results:
        text_ = result.text or result.caption
        if not text_: continue
        
        title = remove_mention(remove_link(text_.splitlines()[0]))
        
        # YAHAN PAR ASLI FIX HAI
        if use_shortener:
            # Free user ke liye, hum ek special 'adsget_' link banayenge jo bot ke paas wapas aayega.
            # Yeh loop ko rokega.
            link = f"https://t.me/{bot_username}?start=adsget_{result.id}_{result.chat.id}"
        else:
            # Premium user ke liye, direct file link.
            link = f"https://t.me/{bot_username}?start=file_{result.id}_{result.chat.id}"
        
        bin_text += template.format(i=i, title=title, link=link)
        i += 1

    if not bin_text:
        no_results_msg = await sts.edit(Script.NO_REPLY_TEXT.format(query))
        asyncio.create_task(schedule_delete(no_results_msg, 300))
        return

    # Hum Telegraph page ke content ko ab short nahi karenge. Loop yahin se ban raha tha.
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

    await sts.edit(
        Script.RESULTS_MESSAGE.format(query=query.upper(), url=reply_url),
        disable_web_page_preview=True,
        reply_markup=reply_markup
    )
