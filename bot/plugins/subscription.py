# bot/plugins/subscription.py

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
    # ... (yahan poora subscription.py ka code aayega) ...
    user_name = cb.from_user.first_name
    welcome_text = f"**__Hey, {user_name},\nWelcome To Our Premium Access 😉**\n\nSelect Subscribtion Plans Here!__ 👇"
    PLAN_BUTTONS = [[types.InlineKeyboardButton(f"{days} Days Plan @ ₹{price}", callback_data=f"subscribe_{days}")] for days, price in Config.SUBSCRIPTION_PLANS.items()]
    PLAN_BUTTONS.append([types.InlineKeyboardButton("⬅️ Back", callback_data="home")])
    await cb.message.edit(welcome_text, reply_markup=types.InlineKeyboardMarkup(PLAN_BUTTONS))

@Client.on_callback_query(filters.regex(r"^subscribe_"))
async def subscribe_callback(c, cb: types.CallbackQuery):
    # ... (baaki ka code) ...
    days = int(cb.data.split("_")[1])
    price = Config.SUBSCRIPTION_PLANS[str(days)]
    user_id = cb.from_user.id
    unique_amount = f"{price}.{random.randint(10, 99)}"
    await sub_db.add_pending_payment(unique_amount, user_id, days)
    payment_page_link = f"{Config.PAYMENT_PAGE_URL}?amount={unique_amount}"
    message_text = f"**__Plan Selected: {days} Days\n\nPlease Pay Exact Amount: **`₹{unique_amount}`**\nClick The Button Below For Secure Payment.__"
    PAYMENT_BUTTONS = [[types.InlineKeyboardButton("💳 Pay Now", url=payment_page_link)], [types.InlineKeyboardButton("⬅️ Back", callback_data="go_premium")]]
    await cb.message.edit(text=message_text, reply_markup=types.InlineKeyboardMarkup(PAYMENT_BUTTONS))

@Client.on_callback_query(filters.regex(r"^ads_search_"))
async def ads_search_callback(c, cb: types.CallbackQuery):
    query = cb.data.split("_", 2)[2]
    await cb.message.delete()
    await run_search(c, cb.message, query, use_shortener=True)

# ... (baaki poora subscription logic) ...
