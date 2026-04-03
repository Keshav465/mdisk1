import asyncio
import logging
from pyrogram import Client, types
from bot.config import Config, Script
from bot.database import user_db
from bot.bot_client import Bot

logger = logging.getLogger(__name__)

async def send_reminder(bot: Bot, user_id: int):
    try:
        markup = types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton("🎬 Search Movies", url=f"https://t.me/{bot.username}")],
            [types.InlineKeyboardButton("🔕 Don't remind me", callback_data="disable_reminders")]
        ])
        await bot.send_message(
            chat_id=user_id,
            text=Script.REMINDER_MSG,
            reply_markup=markup
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send reminder to {user_id}: {e}")
        return False

async def reminder_loop(bot: Bot):
    """
    Background loop that sends reminders to inactive users.
    """
    logger.info("User reminder loop started.")
    while True:
        try:
            # Run once a day (check for users inactive for X days)
            inactive_users = await user_db.get_inactive_users(Config.REMINDER_THRESHOLD)
            
            count = 0
            async for user in inactive_users:
                user_id = user["user_id"]
                if await send_reminder(bot, user_id):
                    count += 1
                # Sleep between messages to avoid flood
                await asyncio.sleep(0.5)
            
            if count > 0:
                logger.info(f"Sent reminders to {count} inactive users.")
                
        except Exception as e:
            logger.error(f"Error in reminder loop: {e}")
            
        # Wait for 24 hours before next check
        await asyncio.sleep(24 * 3600)

@Client.on_callback_query(filters.regex("disable_reminders"))
async def disable_reminders_cb(c, m: types.CallbackQuery):
    await user_db.update_user(m.from_user.id, {"reminders_enabled": False})
    await m.answer("You will no longer receive periodic reminders.", show_alert=True)
    await m.message.delete()
