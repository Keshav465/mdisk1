import contextlib
import logging
import sys
from pyrogram import Client
from bot.config import Config
from telegraph.aio import Telegraph

logger = logging.getLogger(__name__)

class User(Client):
    def __init__(self, user_session, user):
        super().__init__(
            user,
            api_hash=Config.API_HASH,
            api_id=Config.API_ID,
            session_string=str(user_session),
            workers=20
        )

    async def start(self):
        await super().start()
        with contextlib.suppress(Exception):
            await self.export_session_string()
        logger.info('User session started successfully')
        usr_bot_me = await self.get_me()
        return (self, usr_bot_me.id)

    async def stop(self, *args):
        logger.info('Stopping User session...')
        await super().stop()

class Bot(Client):
    USER: User = None
    USER_ID = None
    
    def __init__(self):
        super().__init__(
            Config.BOT_USERNAME,
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins=dict(root="bot.plugins"),
        )

    async def start(self):
        logger.info("Starting Bot...")
        await super().start()
        
        if Config.SESSION_STRING:
            logger.info("Initializing User Session...")
            self.USER, self.USER_ID = await User(Config.SESSION_STRING, "user_bot").start()
        else:
            logger.warning("SESSION_STRING is missing! User session will not be available.")

        if Config.UPDATE_CHANNEL:
            try:
                self.invite_link = await self.create_chat_invite_link(Config.UPDATE_CHANNEL)
            except Exception as e:
                logger.error(f"Failed to create invite link for {Config.UPDATE_CHANNEL}: {e}")
                sys.exit(1)

        me = await self.get_me()
        self.owner = await self.get_users(int(Config.OWNER_ID))
        self.username = f"@{me.username}"

        logger.info("Bot started successfully ✅")

        telegraph = Telegraph()
        if not Config.TELEGRAPH_ACCESS_TOKEN:
            logger.info("Generating Telegraph access tokens...")
            for i in range(5):
                account_info = await telegraph.create_account(
                    short_name=f"{me.username}_{i}", 
                    author_name=f"{self.owner.first_name}_{i}"
                )
                Config.TELEGRAPH_ACCESS_TOKEN.append(account_info["access_token"])

    async def stop(self, *args):
        logger.info("Stopping Bot...")
        if self.USER:
            await self.USER.stop()
        await super().stop()
