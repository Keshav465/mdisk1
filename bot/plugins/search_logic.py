# FILE: bot/plugins/search_logic.py (FINAL AND WORKING CODE)

import asyncio
from pyrogram import Client, types as t, enums
from bot.config import Config, Script
from bs4 import BeautifulSoup
from bot.utils import (
    filter_chat, create_telegraph_post, short_link,
    remove_link, remove_mention, schedule_delete
)

async def perform_search(c: Client, m: t.Message, query: str, use_shortener: bool = False):
    """
    This is the final, working search function.
    It creates a Telegraph page and then shortens the Telegraph URL itself for free users.
    This method completely avoids the shortener loop.
    """
    database_channels = Config.DATABASE_CHANNEL
    if not database_channels:
        # Check if m is a message or callbackquery to respond correctly
        response_obj = m if isinstance(m, t.Message) else m.message
        return await response_obj.edit("Database channel is not configured by the admin.")

    sts = m if isinstance(m, t.CallbackQuery) else await m.reply("`Searching...`")
    response_obj = sts.message if isinstance(sts, t.CallbackQuery) else sts

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

    template = "<aside><b>{i}. {title}</b><br><a href='{link}'>👉 Click Here To Download</a></aside><hr>"
    bin_text = ""
    i = 1
    bot_username = (await c.get_me()).username
    
    # Step 1: Create the Telegraph page content with DIRECT, un-shortened t.me links
    for result in results:
        text_ = result.text or result.caption
        if not text_: continue
        
        title = remove_mention(remove_link(text_.splitlines()[0]))
        # Always use the direct file link inside the Telegraph page
        link = f"https://t.me/{bot_username}?start=file_{result.id}_{result.chat.id}"
        
        bin_text += template.format(i=i, title=title, link=link)
        i += 1

    if not bin_text:
        no_results_msg = await response_obj.edit(Script.NO_REPLY_TEXT.format(query))
        asyncio.create_task(schedule_delete(no_results_msg, 300))
        return
    
    # Step 2: Create the Telegraph Page
    html_content = f"<h3>Results for {query}</h3><br><h4>Total results: {i-1}</h4><br><hr>{bin_text}"
    soup = BeautifulSoup(html_content, "html.parser")
    formatted_text = soup.prettify()
    try:
        telegraph_url = await create_telegraph_post(query, formatted_text)
    except Exception as e:
        await response_obj.edit(f"Could not create Telegraph page. Error: {e}")
        return

    # Step 3: Decide what to send to the user
    final_url_to_send = telegraph_url
    if use_shortener and Config.SHORTENER_API and Config.SHORTENER_SITE:
        # For FREE USERS: Shorten the Telegraph page URL itself
        shortened_url = await short_link(Config.SHORTENER_API, Config.SHORTENER_SITE, telegraph_url)
        if shortened_url and shortened_url != telegraph_url:
            final_url_to_send = shortened_url

    # Step 4: Send the final link to the user
    reply_markup = None
    if response_obj.chat.type == enums.ChatType.PRIVATE and Config.RESULTS_HOW_TO_DOWNLOAD_LINK and Config.REQUEST_MOVIE_URL:
        reply_markup = t.InlineKeyboardMarkup(
            [
                [t.InlineKeyboardButton("How to Download?", url=Config.RESULTS_HOW_TO_DOWNLOAD_LINK)],
                [t.InlineKeyboardButton("Request Movie", url=Config.REQUEST_MOVIE_URL)]
            ]
        )

    await response_obj.edit(
        Script.RESULTS_MESSAGE.format(query=query.upper(), url=final_url_to_send),
        disable_web_page_preview=True,
        reply_markup=reply_markup
    )
