# bot/plugins/scheduler.py
import asyncio
from datetime import datetime
import logging

from bot.database.subscribers import sub_db

# Set up a logger for this file
logger = logging.getLogger(__name__)

async def remove_expired_scheduler():
    """
    Runs in the background to remove expired subscribers every 24 hours.
    """
    logger.info("Background scheduler started.")
    while True:
        try:
            all_subs = await sub_db.get_all_subscribers()
            now = datetime.now()
            count = 0
            
            # Pyrogram/Motor cursor ko list mein convert karo
            sub_list = await all_subs.to_list(length=None)

            for sub in sub_list:
                if sub.get('expiry_date') and sub['expiry_date'] < now:
                    user_id = sub['user_id']
                    await sub_db.remove_subscriber(user_id)
                    logger.info(f"Removed expired subscriber: {user_id}")
                    count += 1
            
            if count > 0:
                logger.info(f"Scheduler run finished. Removed {count} expired users.")

        except Exception as e:
            logger.error(f"Error in scheduler: {e}", exc_info=True)

        # Wait for 24 hours before running again
        await asyncio.sleep(24 * 60 * 60)
