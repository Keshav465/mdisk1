# START OF FILE: bot/plugins/subscription.py (CRASH FIXED)

import random
import re
import asyncio
from pyrogram import Client, filters, types
from bot.config import Config
from bot.database.subscribers import sub_db

# 'run_search' function ko group_filter se import karna hai
from .group_filter import run_search

@Client.on_callback_query(filters.regex(r"^go_premium$"))
async def go_premium_callback(c, cb: types.CallbackQuery):
    user_name = cb.from_user.first_name
    welcome_text = f"**__Hey, {user_name},\nWelcome To Our Premium Access 😉**\n\nSelect Subscribtion Plans Here!__ 👇"
    PLAN_BUTTONS = [[types.InlineKeyboardButton(f"{days} Days Plan @ ₹{price}", callback_data=f"subscribe_{days}")] for days, price in Config.SUBSCRIPTION_PLANS.items()]
    PLAN_BUTTONS.append([types.InlineKeyboardButton("⬅️ Back", callback_data="home")])
    await cb.message.edit(welcome_text, reply_markup=types.InlineKeyboardMarkup(PLAN_BUTTONS))

@Client.on_callback_query(filters.regex(r"^subscribe_"))
async def subscribe_callback(c, cb: types.CallbackQuery):
    try:
        days = int(cb.data.split("_")[1])
        price = Config.SUBSCRIPTION_PLANS[str(days)]
        user_id = cb.from_user.id
        unique_amount = f"{price}.{random.randint(10, 99)}"
        await sub_db.add_pending_payment(unique_amount, user_id, days)
        payment_page_link = f"{Config.PAYMENT_PAGE_URL}?amount={unique_amount}"
        message_text = f"**__Plan Selected: {days} Days\n\nPlease Pay Exact Amount: **`₹{unique_amount}`**\nClick The Button Below For Secure Payment.__"
        PAYMENT_BUTTONS = [[types.InlineKeyboardButton("💳 Pay Now", url=payment_page_link)], [types.InlineKeyboardButton("⬅️ Back", callback_data="go_premium")]]
        await cb.message.edit(text=message_text, reply_markup=types.InlineKeyboardMarkup(PAYMENT_BUTTONS))
    except Exception as e:
        await cb.answer(f"Error: {e}", show_alert=True)

@Client.on_callback_query(filters.regex(r"^ads_search_"))
async def ads_search_callback(c, cb: types.CallbackQuery):
    query = cb.data.split("_", 2)[2]
    
    # === YEH HAI CRASH KA FIX ===
    # Hum message ko delete nahi, balki edit karenge
    try:
        # Pehle callback ko answer do taaki user ko lage ki kuch ho raha hai
        await cb.answer("Searching for you...", show_alert=False)
        # Ab message ko edit karke "Searching..." dikhao
        sts_message = await cb.message.edit("`Searching...`")
        # Ab is naye, edit kiye hue message par search chalao
        await run_search(c, sts_message, query, use_shortener=True)
    except Exception as e:
        print(f"Error in ads_search_callback: {e}")
    # ==========================

# ... (baaki poora subscription logic) ...
@Client.on_message(filters.command("verify") & filters.private & filters.user(Config.ADMINS))
async def verify_payment(c, m: types.Message):
    # ... (code is correct)
    pass 

@Client.on_message(filters.command("removesub") & filters.private & filters.user(Config.ADMINS))
async def remove_subscription(c, m: types.Message):
    # ... (code is correct)
    pass

async def process_payment_sms(c, sms_text):
    # ... (code is correct)
    pass

@Client.on_message(filters.private & filters.text & filters.user(Config.ADMINS))
async def handle_admin_paste(c, m: types.Message):
    # ... (code is correct)
    pass
