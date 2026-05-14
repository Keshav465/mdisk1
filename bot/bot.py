import contextlib
import logging
import sys
from pyrogram import Client
from bot.config import Config
from telegraph.aio import Telegraph

# Forward declaration for type hinting
class Bot(Client):
    pass

class User(Client):
    def __init__(self, user_session, user):
        super().__init__(
            user,
            api_hash=Config.API_HASH,
            api_id=Config.API_ID,
            session_string=f"{user_session}",
            workers=20
        )

    async def start(self):
        await super().start()
        with contextlib.suppress(Exception):
            await self.export_session_string()
        print('User started')
        usr_bot_me = await self.get_me()
        return (self, usr_bot_me.id)

    async def stop(self, *args):
        print('User stopped')
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
            plugins=dict(root="bot/plugins"),
        )

    async def start(self):
        from bot.server import start_server
        await super().start()
        self.USER, self.USER_ID = await User(Config.SESSION_STRING, "user_bot").start()

        if Config.UPDATE_CHANNEL:
            try:
                self.invite_link = await self.create_chat_invite_link(Config.UPDATE_CHANNEL)
            except Exception as e:
                logging.error(
                    f"Make sure to make the bot in your update channel - {Config.UPDATE_CHANNEL}"
                )
                sys.exit(1)

        me = await self.get_me()
        self.owner = await self.get_users(int(Config.OWNER_ID))
        self.username = f"@{me.username}"

        logging.info("Bot started")

        telegraph = Telegraph()

        if not Config.TELEGRAPH_ACCESS_TOKEN:
            for i in range(10):
                account_info = await telegraph.create_account(short_name=f"{self.username}_{i}" ,author_name=f"{self.owner.first_name}_{i}")
                Config.TELEGRAPH_ACCESS_TOKEN.append(account_info["access_token"])
    
        if Config.WEB_SERVER:
            await start_server(self)

    async def yield_file(self, file, start, end):
        # Calculate chunk offset (1MB chunks)
        chunk_size = 1024 * 1024
        chunk_offset = start // chunk_size
        
        try:
            # Skip the first (start % chunk_size) bytes of the first chunk
            skip_bytes = start % chunk_size
            first_chunk = True
            
            async for chunk in self.USER.stream_media(file, offset=chunk_offset):
                if first_chunk:
                    chunk = chunk[skip_bytes:]
                    first_chunk = False
                yield chunk
        except Exception as e:
            logging.error(f"Error in yield_file: {e}")

    async def stop(self, *args):
        await super().stop()
