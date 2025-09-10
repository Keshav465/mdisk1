# START OF FILE: bot/plugins/search_logic.py (FINAL VERSION WITH YOUR EXACT LOGIC FROM SCREENSHOT)

import asyncio
from pyrogram import Client, types as t, enums
from bot.config import Config, Script
from bs4 import BeautifulSoup
from bot.utils import (
    filter_chat, create_telegraph_post, short_from_text, 
    remove_link, remove_mention, schedule_delete
)

async def perform_search(c: Client, m: t.Message, query: str, use_shortener: bool = False):
    """
    This is the main search function. It now uses your tested and working logic from group_filter.py.
    """
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
    
    for result in results:
        result: t.Message

        text_ = result.text or result.caption
        if not text_:
            continue

        title = text_.splitlines()[0]
        link = None # Link ko pehle None set karte hain

        # === YEH AAPKA PURANA AUR 100% SAHI LOGIC HAI (SCREENSHOT WALA) ===
        # Yeh sirf un messages ka link banayega jinme asli file (document/video) hai
        if result.document or result.video:
            # Title ko saaf karo
            clean_title = remove_mention(remove_link(title))
            # Ab link banao
            link = f"https://telegram.dog/{bot_username}?start=file_{result.id}_{result.chat.id}"
            
            # Result ko list mein add karo
            bin_text += template.format(i=i, title=clean_title, link=link)
            i += 1
        # =================================================================

    if not bin_text:
        no_results_msg = await not_found_response(sts, query)
        asyncio.create_task(schedule_delete(no_results_msg, 300))
        return

    # Sirf FREE user ke liye GPlinks use hoga.
    if use_shortener and Config.SHORTENER_API and Config.SHORTENER_SITE:
        bin_text = await short_from_text(Config.SHORTENER_API, Config.SHORTENER_SITE, bin_text)
    
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
    """
    Handles the response when no results are found.
    """
    reply = query.replace(" ", "+")
    reply_markup = t.InlineKeyboardMarkup(
        [[t.InlineKeyboardButton("🔍 Click to Check Spelling✅", url=f"https://www.google.com/search?q={reply}+movie")]]
    )
    return await m.edit(Script.NO_REPLY_TEXT.format(query), disable_web_page_preview=0, reply_markup=reply_markup)

# END OF FILE: bot/plugins/search_logic.py
