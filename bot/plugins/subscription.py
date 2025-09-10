# START OF FILE: bot/plugins/subscription.py (FINAL CLEAN VERSION)

import random
import re
import asyncio
from pyrogram import Client, filters, types
from bot.config import Config
from bot.database.subscribers import sub_db
from .search_logic import perform_search
from bot.utils import schedule_delete, remove_link, remove_mention

@Client.on_callback_query(filters.regex(r"^go_premium$"))
async def go_premium_callback(c, cb: types.CallbackQuery):
    user_name = cb.from_user.first_name
    welcome_text = f"**__Hey, {user_name},\nWelcome To Our Premium Access 😉**\n\nSelect Subscribtion Plans Here!__ 👇"
    PLAN_BUTTONS = [
        [types.InlineKeyboardButton(
            f"{days} Days Plan @ ₹{price}",
            callback_data=f"subscribe_{days}"
        )] for days, price in Config.SUBSCRIPTION_PLANS.items()
    ]
    PLAN_BUTTONS.append([types.InlineKeyboardButton("⬅️ Back", callback_data="home")])
    await cb.message.edit(welcome_text, reply_markup=types.InlineKeyboardMarkup(PLAN_BUTTONS))

@Client.on_callback_query(filters.regex(r"^subscribe_"))
async def subscribe_callback(c, cb: types.CallbackQuery):
    if not Config.PAYMENT_PAGE_URL:
        await cb.answer("Payment page is not configured by the admin yet.", show_alert=True)
        return
    try:
        days = int(cb.data.split("_")[1])
        price = Config.SUBSCRIPTION_PLANS[str(days)]
        user_id = cb.from_user.id
        unique_amount = f"{price}.{random.randint(10, 99)}"
        await sub_db.add_pending_payment(unique_amount, user_id, days)
        payment_page_link = f"{Config.PAYMENT_PAGE_URL}?amount={unique_amount}"
        message_text = f"""
**__Plan Selected: {days} Days

Please Pay Exact Amount: **`₹{unique_amount}`**
Click The Button Below For Secure Payment.__
"""
        PAYMENT_BUTTONS = [
            [types.InlineKeyboardButton("💳 Pay Now", url=payment_page_link)],
            [types.InlineKeyboardButton("⬅️ Back", callback_data="go_premium")]
        ]
        await cb.message.edit(text=message_text, reply_markup=types.InlineKeyboardMarkup(PAYMENT_BUTTONS))
    except Exception as e:
        print(f"Error in subscribe_callback: {e}")
        await cb.answer("An error occurred. Please try again.", show_alert=True)

@Client.on_callback_query(filters.regex(r"^ads_search_"))
async def ads_search_callback(c, cb: types.CallbackQuery):
    query = cb.data.split("_", 2)[2]
    await cb.message.delete()
    sts = await c.send_message(chat_id=cb.message.chat.id, text="`Searching...`")
    await perform_search(c, sts, query, use_shortener=True)

@Client.on_callback_query(filters.regex(r"^ads_get_"))
async def ads_get_callback(c, cb: types.CallbackQuery):
    file_details = cb.data.replace("ads_get_", "")
    await cb.message.delete()
    try:
        parts = file_details.split("_")
        if len(parts) == 2:
            file_id, chat_id = parts
            chnl_msg = await c.get_messages(int(chat_id), int(file_id))
            caption = chnl_msg.caption or ""
            clean_caption = remove_mention(remove_link(caption))
            sent_file_msg = await chnl_msg.copy(cb.from_user.id, caption=clean_caption)
            asyncio.create_task(schedule_delete(sent_file_msg, 86400))
    except Exception as e:
        await c.send_message(cb.from_user.id, f"Sorry, an error occurred while sending the file: {e}")

@Client.on_message(filters.command("verify") & filters.private & filters.user(Config.ADMINS), group=1)
async def verify_payment(c, m: types.Message):
    if len(m.command) < 2:
        await m.reply("Usage: `/verify 20.55`")
        return
    amount_to_verify = m.command[1]
    pending = await sub_db.get_pending_payment(amount_to_verify)
    if not pending:
        await m.reply(f"No pending payment found for ₹{amount_to_verify}.")
        return
    user_id = pending['user_id']
    days = pending['plan_days']
    await sub_db.add_subscriber(user_id, days)
    await sub_db.remove_pending_payment(amount_to_verify)
    await m.reply(f"✅ Manually verified for user `{user_id}`. Subscribed for {days} days.")
    try:
        await c.send_message(user_id, f"🎉 An admin manually verified your payment.\n\nYour **{days} days** subscription is now active.")
    except Exception as e:
        await m.reply(f"Could not notify user. Error: {e}")

@Client.on_message(filters.command("removesub") & filters.private & filters.user(Config.ADMINS), group=1)
async def remove_subscription(c, m: types.Message):
    if len(m.command) < 2:
        await m.reply("Usage: `/removesub <user_id>`")
        return
    try:
        user_id_to_remove = int(m.command[1])
    except ValueError:
        await m.reply("Please provide a valid numeric User ID.")
        return
    is_subbed = await sub_db.is_subscribed(user_id_to_remove)
    if not is_subbed:
        await m.reply(f"User `{user_id_to_remove}` is not a premium subscriber.")
        return
    await sub_db.remove_subscriber(user_id_to_remove)
    await m.reply(f"✅ Subscription for user `{user_id_to_remove}` has been removed.")
    try:
        await c.send_message(user_id_to_remove, "An admin has removed your premium subscription.")
    except Exception as e:
        await m.reply(f"Could not notify the user.")

async def process_payment_sms(c, sms_text):
    amount_regex = r"(?:Rs\.?|INR|credited with|sent)\s*([\d,]+\.\d{2})"
    match = re.search(amount_regex, sms_text, re.IGNORECASE)
    if not match: match = re.search(r"([\d,]+\.\d{2})", sms_text)
    if not match or not match.group(1):
        await c.send_message(Config.OWNER_ID, f"🤖 **SMS Alert**: Could not find amount in:\n`{sms_text}`")
        return
    amount = match.group(1).replace(",", "")
    pending = await sub_db.get_pending_payment(amount)
    if not pending:
        await c.send_message(Config.OWNER_ID, f"🤖 **SMS Alert**: No pending payment for ₹{amount}.\n(SMS: `{sms_text}`)")
        return
    user_id = pending['user_id']
    days = pending['plan_days']
    await sub_db.add_subscriber(user_id, days)
    await sub_db.remove_pending_payment(amount)
    await c.send_message(Config.OWNER_ID, f"✅ **Auto-Verified!**\nUser `{user_id}` subscribed for **{days} days** for `₹{amount}`.")
    try:
        await c.send_message(user_id, f"🎉 Your payment was verified automatically!\n\nYour **{days} days** subscription is now active.")
    except Exception as e:
        await c.send_message(Config.OWNER_ID, f"⚠️ Could not notify user `{user_id}`. Error: {e}")

@Client.on_message(filters.private & filters.text & filters.user(Config.ADMINS) & ~filters.command(["start", "verify", "admincheck", "removesub"]), group=1)
async def handle_admin_paste(c, m: types.Message):
    text = m.text
    if "credited" in text.lower() or "rs." in text.lower() or "inr" in text.lower() or re.search(r"\d+\.\d{2}", text):
        await m.reply("`Processing as a payment SMS...`")
        await process_payment_sms(c, text)
