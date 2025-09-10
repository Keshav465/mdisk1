# START OF FILE: iPMxBT-main/bot/plugins/private_filter.py

from pyrogram import Client, filters, types as t
from bot.config import Config
from bot.database.subscribers import sub_db

# === YAHAN BADLAV KIYA GAYA HAI ===
# Ab yeh function sirf un private messages par chalega jo forward nahi kiye gaye hain.
@Client.on_message(filters.text & filters.private & ~filters.forwarded, group=3)
async def private_search_handler(c: Client, m: t.Message):
    """
    Handles search queries in private messages. This is the main gatekeeper.
    """
    
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
            "**__Hey Buddy!\nYou Are Using The Free Version Of Your Search Robot 😊**\n\nSelect And Enjoy Your subscribtion 👇__",
            reply_markup=t.InlineKeyboardMarkup(buttons)
        )
