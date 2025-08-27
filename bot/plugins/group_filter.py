import asyncio
import re
from pyrogram import Client, filters, types as t, enums
from bot.config import Config, Script
from bs4 import BeautifulSoup
from bot.utils import (
    auto_delete_func, filter_chat, create_telegraph_post, 
    is_premium_group, short_link, short_from_text, remove_link, remove_mention
)
from bot.database import group_db, user_db
from datetime import datetime, timedelta

@Client.on_message(filters.text & (filters.private | filters.group) & filters.incoming)
async def smart_filter_handler(c: Client, m: t.Message):

    if m.text.startswith("/"):
        return
    if re.findall(r"((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", m.text):
        return

    query = m.text
    if not (2 < len(query) < 100):
        return

    # =================================================================================
    #   LOGIC FOR PRIVATE CHAT (Pre-Verification System)
    # =================================================================================
    if m.chat.type == enums.ChatType.PRIVATE:
        user_id = m.from_user.id
        shortener_api = Config.SHORTENER_API
        shortener_site = Config.SHORTENER_SITE

        user_data = await user_db.get_user(user_id)
        last_time = user_data.get('last_shortener_time', datetime(1970, 1, 1))

        if datetime.now() - last_time > timedelta(hours=12):
            if shortener_api and shortener_site:
                bot_username = (await c.get_me()).username
                verification_link = f"https://t.me/{bot_username}?start=verified_user"
                shortened_link = await short_link(shortener_api, shortener_site, verification_link)

                if not shortened_link:
                    await m.reply_text("❌ Shortener service mein koi problem hai. Please thodi der baad try karein.")
                    return

                btn = [
                    [t.InlineKeyboardButton("➡️ Verify Now ⬅️", url=shortened_link)]
                ]
                
                if Config.HOW_TO_VERIFY_LINK: # Note: This variable was changed from RESULTS_HOW_TO_DOWNLOAD_LINK
                    btn.append(
                        [t.InlineKeyboardButton("❓ How To Verify ❓", url=Config.HOW_TO_VERIFY_LINK)]
                    )

                await m.reply_text(
                    "**👋 Welcome!**\n\n"
                    "ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ **Completed Verification** ᴛᴏᴅᴀʏ, "
                    "ᴘʟᴇᴀꜱᴇ ᴄʟɪᴄᴋ ᴏɴ **Verify Now** & ɢᴇᴛ ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴄᴄᴇꜱꜱ ᴛɪʟʟ ɴᴇxᴛ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ",
                    reply_markup=t.InlineKeyboardMarkup(btn)
                )
                return

        database_channels = Config.DATABASE_CHANNEL
        # --- ADDED AUTO-DELETE LOGIC (Private) ---
        auto_delete = Config.AUTO_DELETE
        auto_delete_time = Config.AUTO_DELETE_TIME
        # --- END ---
        if not database_channels: return

        sts = await m.reply("`Searching...`")
        results = await filter_chat(c, query, database_channels)

        if not results:
            return await not_found_response(sts, query)

        bot_username = (await c.get_me()).username
        template = "<aside><b>{i}. {title}</b><br><a href='{link}'>👉 Click Here To Download</a> | {id}</aside><hr>"
        bin_text = ""
        i = 1
        for result in results:
            link = f"https://telegram.dog/{bot_username}?start=file_{result.id}_{result.chat.id}"
            title = (result.text or result.caption).splitlines()[0]
            title = remove_mention(remove_link(title))
            bin_text += template.format(i=i, title=title, link=link, id=result.id)
            i += 1
        
        text = f"<h3>Results for {query}</h3><br><h4>Total results: {i-1}</h4><br><hr>{bin_text}"
        soup = BeautifulSoup(text, "html.parser")
        formatted_text = soup.prettify()
        reply_url = await create_telegraph_post(query, formatted_text)
        await sts.edit(Script.RESULTS_MESSAGE.format(query=query.upper(), url=reply_url), disable_web_page_preview=1)
        
        # --- ADDED AUTO-DELETE LOGIC (Private) ---
        if bool(auto_delete and auto_delete_time):
            asyncio.create_task(auto_delete_func(sts, auto_delete_time))
        # --- END ---
        return

    # =================================================================================
    #   LOGIC FOR GROUP CHAT
    # =================================================================================
    elif m.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = m.chat.id
        group_info = await group_db.get_group(grp_id)
        is_premium = await is_premium_group(grp_id)
        
        database_channels = [group_info["index_channel"]] if group_info["index_channel"] and is_premium else Config.DATABASE_CHANNEL
        # --- ADDED AUTO-DELETE LOGIC (Group) ---
        auto_delete = group_info.get("auto_delete", Config.AUTO_DELETE)
        auto_delete_time = group_info.get("auto_delete_time", Config.AUTO_DELETE_TIME)
        # --- END ---
        
        if not database_channels: return
        sts = await m.reply("`Searching...`")
        results = await filter_chat(c, query, database_channels)

        if not results:
            return await not_found_response(sts, query)
            
        bot_username = (await c.get_me()).username
        template = "<aside><b>{i}. {title}</b><br><a href='{link}'>👉 Click Here To Download</a> | {id}</aside><hr>"
        bin_text = ""
        i = 1
        for result in results:
            link = f"https://telegram.dog/{bot_username}?start=file_{result.id}_{result.chat.id}"
            title = (result.text or result.caption).splitlines()[0]
            title = remove_mention(remove_link(title))
            bin_text += template.format(i=i, title=title, link=link, id=result.id)
            i += 1
        
        text = f"<h3>Results for {query}</h3><br><h4>Total results: {i-1}</h4><br><hr>{bin_text}"
        soup = BeautifulSoup(text, "html.parser")
        formatted_text = soup.prettify()
        reply_url = await create_telegraph_post(query, formatted_text)
        await sts.edit(Script.RESULTS_MESSAGE.format(query=query.upper(), url=reply_url), disable_web_page_preview=1)

        # --- ADDED AUTO-DELETE LOGIC (Group) ---
        if bool(auto_delete and auto_delete_time):
            asyncio.create_task(auto_delete_func(sts, auto_delete_time))
        # --- END ---
        return

async def not_found_response(m, query):
    reply = query.replace(" ", "+")
    reply_markup = t.InlineKeyboardMarkup(
        [[t.InlineKeyboardButton("🔍 Click to Check Spelling✅", url=f"https://www.google.com/search?q={reply}+movie")]]
    )
    return await m.edit(Script.NO_REPLY_TEXT.format(query), disable_web_page_preview=0, reply_markup=reply_markup)
