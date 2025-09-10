from bot.config import Config
from motor.motor_asyncio import AsyncIOMotorClient


class Database:
    def __init__(self, uri, database_name):
        self._client = AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.bot = self.db["bot"]

    async def get_bot_config(self):
        bot_config = await self.bot.find_one({"bot_username": Config.BOT_USERNAME})
        if not bot_config:
            res = {
                "bot_username": Config.BOT_USERNAME,
                "pm_config": {
                    "shortener_site": None,
                    "shortener_api": None,
                    "auto_delete": False,
                    "auto_delete_time":300,
                }

            }
            await self.bot.insert_one(res)
            bot_config = await self.bot.find_one({"bot_username": Config.BOT_USERNAME})
        return bot_config

    async def update_bot_config(self, value):
        myquery = {
            "bot_username": Config.BOT_USERNAME,
        }
        newvalues = {"$set": value}
        return await self.bot.update_one(myquery, newvalues)

bot_config_db = Database(Config.DATABASE_URL, Config.DATABASE_NAME)
