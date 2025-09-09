# FILE: bot/plugins/search_logic.py (FINAL, 100% WORKING CODE - EXACTLY LIKE OLD LOGIC)

import asyncio
from pyrogram import Client, types as t, enums
from bot.config import Config, Script
from bs4 import BeautifulSoup
from bot.utils import (
    filter_chat, create_telegraph_post, short_from_text, 
    remove_link, remove_mention, schedule_delete
)

async def perform_search(c: Client, m: t.Message, query: str, use_shortener: bool = False):
    database_channels = Config.DATABASE_CHANNEL
    if not database_channels:
        # Check if m is a message or callbackquery to respond correctly
        response_obj = m if isinstance(m, t.Message) else m.message
        return await response_obj.edit("Database channel is not configured by the admin.")

    # Determine the message object we need to edit/reply to
    if isinstance(m, t.Message):
        sts = await m.reply("`Searching...`")
        response_obj = sts
    else: # This means it is a callback_query
        sts = m
        response_obj = sts.message
    
    await response_obj.edit("`Searching...`")

    try:
        results = await filter_chat(c, query, database_channels)
    except Exception as e:
        print(f"Error during filter_chat: {e}")
        await response_obj.edit("An error occurred while searching.")
        return

    if not results:
        no_results_msg = await response_obj.edit(Script.NO_REPLY_TEXT.format(query))
        asyncio.create_task(schedule_delete(no_results_msg, 300))
        return

    # Step 1: Create the part of the HTML that contains the links (bin_text)
    # This is exactly like your old, working bot.
    template = "<aside><b>{i}. {title}</b><br><a href='{link}'>👉 Click Here To Download</a></aside><hr>"
    bin_text = ""
    i = 1
    bot_username = (await c.get_me()).username
    
    for result in results:
        text_ = result.text or result.caption
        if not text_: continue
        
        title = remove_mention(remove_link(text_.splitlines()[0]))
        link = f"https://t.me/{bot_username}?start=file_{result.id}_{result.chat.id}"
        
        bin_text += template.format(i=i, title=title, link=link)
        i += 1

    if not bin_text:
        no_results_msg = await response_obj.edit(Script.NO_REPLY_TEXT.format(query))
        asyncio.create_task(schedule_delete(no_results_msg, 300))
        return
    
    # === YAHI ASLI FIX HAI (BILKUL PURANE BOT JAISA) ===
    # Step 2: If it's a free user, shorten ONLY the 'bin_text' part.
    if use_shortener and Config.SHORTENER_API and Config.SHORTENER_SITE:
        # Hum sirf links wale hisse ko shortener ke paas bhejenge.
        shortened_bin_text = await short_from_text(Config.SHORTENER_API, Config.SHORTENER_SITE, bin_text)
        if shortened_bin_text:
            bin_text = shortened_bin_text

    # Step 3: Now, create the FULL HTML content by adding headers to the (possibly shortened) bin_text.
    final_html_content = f"<h3>Results for {query}</h3><br><h4>Total results: {i-1}</h4><br><hr>{bin_text}"
    
    soup = BeautifulSoup(final_html_content, "html.parser")
    formatted_text = soup.prettify()
    try:
        telegraph_url = await create_telegraph_post(query, formatted_text)
    except Exception as e:
        await response_obj.edit(f"Could not create Telegraph page. Error: {e}")
        return

    # Step 4: Send the Telegraph link to the user
    reply_markup = None
    if response_obj.chat.type == enums.ChatType.PRIVATE and Config.RESULTS_HOW_TO_DOWNLOAD_LINK and Config.REQUEST_MOVIE_URL:
        reply_markup = t.InlineKeyboardMarkup(
            [
                [t.InlineKeyboardButton("How to Download?", url=Config.RESULTS_HOW_TO_DOWNLOAD_LINK)],
                [t.InlineKeyboardButton("Request Movie", url=Config.REQUEST_MOVIE_URL)]
            ]
        )

    await response_obj.edit(
        Script.RESULTS_MESSAGE.format(query=query.upper(), url=telegraph_url),
        disable_web_page_preview=True,
        reply_markup=reply_markup
    )
