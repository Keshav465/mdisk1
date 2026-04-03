from bot.config import Config
from motor.motor_asyncio import AsyncIOMotorClient


class Database:
    def __init__(self, uri, database_name):
        self._client = AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.users = self.db["users"]

    async def get_user(self, user_id):
        user_id = int(user_id)
        user = await self.users.find_one({"user_id": user_id})
        if not user:
            from datetime import datetime
            res = {
                "user_id": user_id,
                "banned": False,
                "last_active": datetime.now(),
                "reminders_enabled": True
            }
            await self.users.insert_one(res)
            user = await self.users.find_one({"user_id": user_id})
        return user

    async def update_activity(self, user_id):
        from datetime import datetime
        await self.users.update_one(
            {"user_id": int(user_id)},
            {"$set": {"last_active": datetime.now()}}
        )

    async def get_inactive_users(self, threshold_days):
        from datetime import datetime, timedelta
        threshold_date = datetime.now() - timedelta(days=threshold_days)
        return self.users.find({
            "last_active": {"$lt": threshold_date},
            "banned": False,
            "reminders_enabled": {"$ne": False}
        })

    async def update_user(self, user_id, value):
        myquery = {
            "user_id": user_id,
        }
        newvalues = {"$set": value}
        return await self.users.update_one(myquery, newvalues)

    async def filter_users(self):
        return self.users.find({})

    async def total_users_count(self, ):
        return await self.users.count_documents({})

    async def get_all_users(self, ):
        return self.users.find({})

    async def delete_user(self, user_id):
        await self.users.delete_one({"user_id": int(user_id)})

    async def is_user_exist(self, id):
        user = await self.users.find_one({"user_id": int(id)})
        return bool(user)


user_db = Database(Config.DATABASE_URL, Config.DATABASE_NAME)
