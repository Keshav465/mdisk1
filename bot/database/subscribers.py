# bot/database/subscribers.py

from datetime import datetime, timedelta
from bot.config import Config
from motor.motor_asyncio import AsyncIOMotorClient

class SubDB:
    def __init__(self, uri, database_name):
        self._client = AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.subs = self.db["subscribers"]
        self.pending = self.db["pending_payments"]

    async def add_subscriber(self, user_id, days):
        expiry_date = datetime.now() + timedelta(days=days)
        await self.subs.update_one({'user_id': int(user_id)}, {'$set': {'expiry_date': expiry_date, 'user_id': int(user_id)}}, upsert=True)

    async def remove_subscriber(self, user_id):
        await self.subs.delete_one({'user_id': int(user_id)})

    async def is_subscribed(self, user_id):
        sub = await self.subs.find_one({'user_id': int(user_id)})
        if sub and sub.get('expiry_date') and sub['expiry_date'] > datetime.now():
            return sub
        return None
    
    async def add_pending_payment(self, amount, user_id, plan_days):
        await self.pending.insert_one({'amount': str(amount), 'user_id': int(user_id), 'plan_days': int(plan_days), 'createdAt': datetime.utcnow()})

    async def get_pending_payment(self, amount):
        await self.pending.delete_many({'createdAt': {'$lt': datetime.utcnow() - timedelta(minutes=15)}})
        return await self.pending.find_one({'amount': str(amount)})

    async def remove_pending_payment(self, amount):
        await self.pending.delete_one({'amount': str(amount)})

sub_db = SubDB(Config.DATABASE_URL, Config.DATABASE_NAME)
