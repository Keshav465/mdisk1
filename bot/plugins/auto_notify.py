from pyrogram import Client, filters, types, enums
from bot.config import Config, Script
from bot.database import user_db
from bot.utils import remove_link, remove_mention
import asyncio
import logging

logger = logging.getLogger(__name__)

@Client.on_message(filters.chat(Config.DATABASE_CHANNEL) & (filters.document | filters.video) & ~filters.service)
async def auto_notify_handler(c: Client, m: types.Message):
    """
    Automatically notifies all users when a new movie is added to the database channel.
    """
    if not Config.AUTO_NOTIFICATION:
        return
    
    # 1. Extract Details
    text = m.caption or m.text or "New Movie Added"
    title = text.splitlines()[0]
    title = remove_mention(remove_link(title))
    
    # Generate the deep link for the bot
    bot_username = c.me.username
    deep_link = f"https://t.me/{bot_username}?start=file_{m.id}_{m.chat.id}"
    
    # 2. Prepare Notification Message
    notify_text = f"<b>🎬 New Movie Updated!</b>\n\n<b>名称:</b> <code>{title}</code>\n\n"
    notify_text += f"You can now watch or download this movie directly in the bot."
    
    reply_markup = types.InlineKeyboardMarkup(
        [
            [
                types.InlineKeyboardButton("🚀 Watch & Download", url=deep_link)
            ]
        ]
    )
    
    # 3. Broadcast to all users
    users = await user_db.get_all_users()
    count = 0
    success = 0
    failed = 0
    
    async for user in users:
        user_id = user["user_id"]
        try:
            await c.send_message(
                chat_id=user_id,
                text=notify_text,
                reply_markup=reply_markup
            )
            success += 1
            await asyncio.sleep(0.1) # Small delay to avoid severe rate limits
        except Exception:
            failed += 1
        
        count += 1
        if count % 100 == 0:
            logger.info(f"Notification in progress: {success} success, {failed} failed")
            await asyncio.sleep(2) # Cooldown after 100 messages

    logger.info(f"Notification Completed: Total {count}, Success {success}, Failed {failed}")
