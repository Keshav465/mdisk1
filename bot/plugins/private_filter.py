# START OF FILE: iPMxBT-main/bot/plugins/private_filter.py

from pyrogram import Client, filters, types as t
from bot.config import Config
from bot.database.subscribers import sub_db

# Correct filter: handles private text messages, and has the lowest priority (group=3)
@Client.on_message(filters.text & filters.private, group=3)
async def private_search_handler(c: Client, m: t.Message):
    """
    Handles search queries in private messages. This is the main gatekeeper.
    """
    
    # === YAHAN PAR BADLAV KIYA GAYA HAI ===
    # Agar message kisi bot ne bheja hai (jaise Livegram), to use ignore kar do.
    if m.from_user and m.from_user.is_bot:
        return  # Yahan se function ruk jayega aur aage search nahi karega.
    # ======================================

    # Explicitly ignore any message that starts with "/" to be safe
    if m.text.startswith('/'):
        return

    user_id = m.from_user.id
    query = m.text
    
    # Admin ke liye special bypass
    if user_id in Config.ADMINS:
        from .search_logic import perform_search
        await perform_search(c, m, query, use_shortener=False)
        return

    # Normal users ke liye subscription check
    is_subbed = await sub_db.is_subscribed(user_id)
    if is_subbed:
        # Agar premium hai, to direct search
        from .search_logic import perform_search
        await perform_search(c, m, query, use_shortener=False)
    else:
        # Agar premium nahi hai, to choice do
        buttons = [
            [t.InlineKeyboardButton("📺 Download With Ads 📺", callback_data=f"ads_search_{query[:50]}")],
            [t.InlineKeyboardButton("💎 Go Premium - No Ads 💎", callback_data="go_premium")]
        ]
        await m.reply(
            "**Hey Buddy!\nYou Are Using The Free Version 😊**\n\nSelect And Enjoy Your Choice 👇",
            reply_markup=t.InlineKeyboardMarkup(buttons)
        )
