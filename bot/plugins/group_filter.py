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
