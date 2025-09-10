# START OF FILE: bot/plugins/commands.py

from pyrogram import Client, filters, types, enums
import base64 
from datetime import datetime
from bot.config import Config, Script
from bot.utils import get_group_info_button, get_group_info_text, group_admin_check, group_wrapper, is_bot_admin, is_int, is_premium_group, remove_link, remove_mention, human_time
from bot.database import group_db, user_db
from bot.database.subscribers import sub_db
from bot import Bot
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid

@Client.on_message(filters.command("start") & filters.private, group=2)
async def start(c: Bot, m: types.Message):
    await user_db.get_user(m.from_user.id)
    if len(m.command) > 1:
        payload = m.command[1]
        if payload.startswith("file_"):
            try:
                parts = payload.split("_")
                if len(parts) >= 3:
                    file_id, chat_id = parts[1], parts[2]
                    chnl_msg = await c.get_messages(int(chat_id), int(file_id))
                    caption = chnl_msg.caption or ""
                    clean_caption = remove_mention(remove_link(caption))
                    await chnl_msg.copy(m.from_user.id, caption=clean_caption)
                else:
                    await m.reply("Sorry, this link is invalid.")
            except Exception as e:
                await m.reply(f"Sorry, this link is broken or expired.\nError: {e}")
            return
        elif payload == "subscribe":
            user_name = m.from_user.first_name
            welcome_text = f"**__Hey, {user_name},\nWelcome To Our Premium Access 😉**\n\nSelect Subscribtion Plans Here!\n\nCheck: /status __"
            PLAN_BUTTONS = [[types.InlineKeyboardButton(f"{days} Days Plan @ ₹{price}", callback_data=f"subscribe_{days}")] for days, price in Config.SUBSCRIPTION_PLANS.items()]
            await m.reply(welcome_text, reply_markup=types.InlineKeyboardMarkup(PLAN_BUTTONS))
            return

    markup = types.InlineKeyboardMarkup([
        [types.InlineKeyboardButton("💎 Go Premium 💎", callback_data="go_premium")],
        [types.InlineKeyboardButton(text="Help", callback_data="help"), types.InlineKeyboardButton(text="About", callback_data="about")],
        [types.InlineKeyboardButton(text="Close", callback_data="delete")]
    ])
    await m.reply_text(Script.START_MESSAGE, disable_web_page_preview=True, reply_markup=markup)

@Client.on_message(filters.command("status") & filters.private, group=2)
async def my_status(c: Client, m: types.Message):
    user_id = m.from_user.id
    subscription_details = await sub_db.is_subscribed(user_id)
    if subscription_details:
        expiry_date = subscription_details['expiry_date']
        time_remaining = expiry_date - datetime.now()
        formatted_expiry = expiry_date.strftime("%d %B %Y at %I:%M %p")
        formatted_remaining = human_time(time_remaining.total_seconds()) if time_remaining.total_seconds() > 0 else "Expired"
        status_message = f"**💎 Your Premium Status 💎**\n\n✅ You are an active subscriber.\n\n🗓️ **Expires On:** `{formatted_expiry}`\n⏳ **Time Remaining:** `{formatted_remaining}`"
        await m.reply_text(status_message)
    else:
        not_subscribed_message = "**❌ You Don't Have Premium Subscribtion.**\n\n__To Enjoy Ad-free Entertainment and Get Direct Files Without Any Ads, Consider Subscribing!__"
        markup = types.InlineKeyboardMarkup([[types.InlineKeyboardButton("💎 Go Premium 💎", callback_data="go_premium")]])
        await m.reply_text(not_subscribed_message, reply_markup=markup)

# ... (baaki purane commands.py ke saare commands yahan aayenge, jaise /help, /about, etc.)
@Client.on_message(filters.command("help") & filters.private)
async def help_command(c: Client, m: types.Message):
    await m.reply_text(Script.USER_HELP_MESSAGE, disable_web_page_preview=True)

@Client.on_message(filters.command("about") & filters.private)
async def about(c: Client, m: types.Message):
    await m.reply_text(Script.ABOUT_MESSAGE, disable_web_page_preview=True)
# ... (and all other commands from your old file)
