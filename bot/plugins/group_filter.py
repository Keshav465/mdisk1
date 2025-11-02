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

    query = m.text.strip()

    # Ignore commands or emoji-only messages
    if m.text.startswith("/") or re.findall(r"((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", query):
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

        sts = await m.reply("`🔍 Searching your movie...`")

        try:
            results = await filter_chat(c, query, database_channels)
        except Exception as e:
            await sts.edit(f"⚠️ Some error occurred: `{e}`")
            return

        # Template for each result
        template = """
<aside>
<b>{i}. 🍿 {title}</b><br>
👉 <a href='{link}'>Click Here To Download 👈</a> | {size} 📦
</aside>
<hr>
"""

        bin_text = ""
        i = 1
        for result in results:
            text_ = result.text or result.caption or ""
            title = text_.splitlines()[0]

            # Detect file size if available
            size = "Unknown Size"
            if result.document and result.document.file_size:
                file_size = result.document.file_size / (1024 * 1024)  # in MB
                size = f"{file_size/1024:.2f} GB" if file_size > 1024 else f"{file_size:.2f} MB"

            # Generate download link
            link = ""
            if free_group or is_shortener:
                bot_username = c.username.replace("@", "")
                link = f"https://telegram.dog/{bot_username}?start=file_{result.id}_{result.chat.id}"
            elif result.link:
                link = result.link

            temp = template.format(i=i, title=remove_mention(remove_link(title)), link=link, size=size)
            bin_text += temp
            i += 1

        if not bin_text:
            await not_found_response(sts, query)
            return

        # Apply shortener if configured
        if is_shortener:
            bin_text = await short_from_text(shortener_api, shortener_site, bin_text)

        # Format telegraph post
        html_content = f"""
<h3>🍿 Results for {query.upper()}</h3>
<h4>Total Results: {i-1}</h4>
<hr>
{bin_text}
"""
        soup = BeautifulSoup(html_content, "html.parser")
        formatted_text = soup.prettify()

        try:
            reply_url = await create_telegraph_post(query, formatted_text)
        except Exception:
            await sts.edit("❌ Failed to create Telegraph post.")
            return

        # Final formatted Telegram message
        custom_message = f"""
Click Here 👇 For "{query.upper()}"

🍿🎬 <a href="{reply_url}">{query.upper()}</a>
🍿🎬 <a href="{reply_url}">CLICK ME FOR RESULTS</a>

🎬 Watch & Download More Movies and Series Here 👇
🌐 https://filmy4uhd.vercel.app
"""

        replied_link = await sts.edit(
            custom_message,
            disable_web_page_preview=True
        )

        # Auto delete (if enabled)
        if bool(auto_delete and auto_delete_time):
            asyncio.create_task(auto_delete_func(replied_link, auto_delete_time))


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
