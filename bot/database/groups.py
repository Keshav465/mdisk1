from datetime import datetime
import time
from bot.config import Config
from motor.motor_asyncio import AsyncIOMotorClient


class Database:
    def __init__(self, uri, database_name):
        self._client = AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.groups = self.db["groups"]

    async def get_group(self, group_id):
        group = await self.groups.find_one({"group_id": int(group_id)})
        if not group:
            res = {
                "group_id": group_id,
                "banned": False,
                "shortener_site":None,
                "shortener_api":None,
                'fsub': True,
                'fsub_channel': 0,
                'index_channel':0,
                "last_verified": datetime(1970,1,1),
                "access_days":0, 
                "auto_delete":True, 
                "auto_delete_time":300, 
            }
            await self.groups.insert_one(res)
            group = await self.groups.find_one({"group_id": group_id})
        return group

    async def update_group(self, group_id, value):
        myquery = {
            "group_id": group_id,
        }
        newvalues = {"$set": value}
        return await self.groups.update_one(myquery, newvalues)

    async def filter_groups(self):
        return self.groups.find({})

    async def total_groups_count(self, ):
        return await self.groups.count_documents({})

    async def get_all_groups(self, ):
        return self.groups.find({})

    async def delete_group(self, group_id):
        await self.groups.delete_one({"group_id": int(group_id)})

    async def is_group_exist(self, id):
        group = await self.groups.find_one({"group_id": int(id)})
        return bool(group)

    async def is_group_verified(self, group_id):
        group = await self.get_group(group_id)
        access_days = datetime.fromtimestamp(time.mktime(group["last_verified"].timetuple()) + group['access_days'])
        return (access_days - datetime.now()).total_seconds() >= 0

    async def expiry_date(self, group_id):
        group = await self.get_group(group_id)
        access_days = datetime.fromtimestamp(time.mktime(group["last_verified"].timetuple()) + group['access_days'])
        return access_days, int((access_days - datetime.now()).total_seconds())
    
group_db = Database(Config.DATABASE_URL, Config.DATABASE_NAME)
