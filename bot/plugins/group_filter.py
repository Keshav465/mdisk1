import asyncio
import re
from pyrogram import Client, filters, types as t, enums
from bot.config import Config, Script
from bs4 import BeautifulSoup
from bot.utils import (
    auto_delete_func,
    filter_chat,
    create_telegraph_post,
    is_premium_group,
    short_from_text,
    remove_link,
    remove_mention
)
from bot.database import group_db


@Client.on_message(filters.text & (filters.private | filters.group) & filters.incoming)
async def pm_filter(c, m: t.Message):
    
    free_group = True
    if m.chat.type in [enums.chat_type.ChatType.SUPERGROUP, enums.chat_type.ChatType.GROUP]:
        chat_id = getattr(m.chat, "id", None)
        if await is_premium_group(chat_id):
            free_group = False

    query = m.text

    if m.text.startswith("/"):
        return  # ignore commands
    if re.findall(r"((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", query):
        return

    if 2 < len(query) < 100:

        is_private = m.chat.type == enums.chat_type.ChatType.PRIVATE

        database_channels, auto_delete, auto_delete_time, shortener_api, shortener_site = None, None, None, None, None
        if m.chat.type == enums.chat_type.ChatType.PRIVATE or free_group:
            database_channels = Config.DATABASE_CHANNEL
            auto_delete = Config.AUTO_DELETE
            auto_delete_time = Config.AUTO_DELETE_TIME
            shortener_api = Config.SHORTENER_API
            shortener_site = Config.SHORTENER_SITE
        elif m.chat.type in [enums.chat_type.ChatType.SUPERGROUP, enums.chat_type.ChatType.GROUP]:
            grp_id = m.chat.id
            group_info = await group_db.get_group(grp_id)
            database_channels = [group_info["index_channel"]] if group_info["index_channel"] else []
            auto_delete = group_info["auto_delete"]
            auto_delete_time = group_info["auto_delete_time"]
            shortener_api = group_info["shortener_api"]
            shortener_site = group_info["shortener_site"]

        is_shortener = bool(shortener_api and shortener_site)
        
        if is_shortener:
            database_channels = Config.DATABASE_CHANNEL

        if not database_channels:
            return

        sts = await m.reply("`🔎 Searching... Please wait.`")

        try:
            results = await filter_chat(c, query, database_channels)
        except Exception:
            await sts.edit("⚠️ Some error occurred while searching!")
            return

        # 🌟 Movie Template (Premium Style)
        template = (
            "<b>{i}. 🎬 {title}</b><br>"
            "📂 <b>File:</b> <i>{title}</i><br>"
            "⚖️ <b>Size:</b> <code>{size}</code><br>"
            "👉 <a href='{link}'>DOWNLOAD / WATCH ONLINE 👈</a>"
            "<br><br>"
        )

        bin_text = ""
        i = 1
        for result in results:
            result: t.Message
            text_ = result.text or result.caption
            title = text_.splitlines()[0]

            # 🧾 File size निकालना
            if result.document:
                file_size = f"{round(result.document.file_size / (1024 * 1024), 1)} MB"
                if result.document.file_size >= 1024 * 1024 * 1024:
                    file_size = f"{round(result.document.file_size / (1024 * 1024 * 1024), 1)} GB"
            elif result.video:
                file_size = f"{round(result.video.file_size / (1024 * 1024), 1)} MB"
                if result.video.file_size >= 1024 * 1024 * 1024:
                    file_size = f"{round(result.video.file_size / (1024 * 1024 * 1024), 1)} GB"
            else:
                file_size = "N/A"

            # 🔗 File Link बनाना
            link = None
            if free_group or is_shortener:
                bot_username = c.username.replace("@", "")
                link_temp = f"https://telegram.dog/{bot_username}?start=file_"
                if result.document or result.video:
                    title = remove_mention(remove_link(title))
                    link = f"{link_temp}{result.id}_{result.chat.id}"
            elif result.photo or result.text:
                link = result.link

            if link:
                temp = template.format(
                    i=i,
                    title=title,
                    link=link,
                    size=file_size
                )
                bin_text += temp
                i += 1

        if not bin_text:
            await not_found_response(sts, query)
            return

        # 🔗 Shortener Integration
        if is_shortener:
            bin_text = await short_from_text(shortener_api, shortener_site, bin_text)

        text = f"<h3>🎬 Results for <u>{query}</u></h3><br><h4>Total results: {i-1}</h4><hr>{bin_text}"

        soup = BeautifulSoup(text, "html.parser")
        formatted_text = soup.prettify()

        # 📰 Telegraph Post बनाना
        reply_url = await create_telegraph_post(query, formatted_text)

        # 🎛 Inline Buttons
        reply_markup = t.InlineKeyboardMarkup(
            [
                [
                    t.InlineKeyboardButton(
                        "📺 How to Download?",
                        url=Config.RESULTS_HOW_TO_DOWNLOAD_LINK,
                    ),
                ],
                [
                    t.InlineKeyboardButton(
                        "🎥 Request Movie",
                        url=Config.REQUEST_MOVIE_URL,
                    )
                ],
            ]
        ) if Config.RESULTS_HOW_TO_DOWNLOAD_LINK and Config.REQUEST_MOVIE_URL and is_private else None

        replied_link = await sts.edit(
            Script.RESULTS_MESSAGE.format(
                query=query.upper(),
                url=reply_url
            ),
            disable_web_page_preview=1,
            reply_markup=reply_markup
        )

        if bool(auto_delete and auto_delete_time):
            asyncio.create_task(auto_delete_func(replied_link, auto_delete_time))

        return


# 🚫 Not Found Response
async def not_found_response(m, query):
    reply = query.replace(" ", "+")
    reply_markup = t.InlineKeyboardMarkup(
        [
            [
                t.InlineKeyboardButton(
                    "📅 Check Release Date",
                    url=f"https://www.google.com/search?q={reply}+movie+release+date",
                ),
            ],
            [
                t.InlineKeyboardButton(
                    "🔍 Check Spelling",
                    url=f"https://www.google.com/search?q={reply}+movie",
                )
            ],
        ]
    )

    return await m.edit(
        Script.NO_REPLY_TEXT.format(query),
        disable_web_page_preview=0,
        reply_markup=reply_markup,
    )
