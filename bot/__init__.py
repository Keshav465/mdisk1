import contextlib
import logging
import logging.config
import sys
from pyrogram import Client
from aiohttp import web
from bot.config import Config
from telegraph.aio import Telegraph


# Get logging configurations

logging.getLogger().setLevel(logging.INFO)

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
            routes = web.RouteTableDef()

            @routes.get("/", allow_head=True)
            async def root_route_handler(request):
                res = {
                    "status": "running",
                }
                return web.json_response(res)

            async def web_server():
                web_app = web.Application(client_max_size=30000000)
                web_app.add_routes(routes)
                return web_app

            app = web.AppRunner(await web_server())
            await app.setup()
            await web.TCPSite(app, "0.0.0.0", 8000).start()

    async def stop(self, *args):
        await super().stop()
