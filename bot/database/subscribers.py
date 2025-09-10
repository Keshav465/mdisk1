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

    # === Subscriber Management ===

    async def add_subscriber(self, user_id, days):
        """Adds a new subscriber or updates an existing one."""
        expiry_date = datetime.now() + timedelta(days=days)
        await self.subs.update_one(
            {'user_id': int(user_id)},
            {'$set': {'expiry_date': expiry_date, 'user_id': int(user_id)}},
            upsert=True
        )

    async def remove_subscriber(self, user_id):
        """Removes a subscriber."""
        await self.subs.delete_one({'user_id': int(user_id)})

    async def is_subscribed(self, user_id):
        """Checks if a user has an active subscription."""
        sub = await self.subs.find_one({'user_id': int(user_id)})
        if sub and sub['expiry_date'] > datetime.now():
            return sub
        return None

    async def get_all_subscribers(self):
        """Gets all subscribers from the database."""
        return self.subs.find({})

    # === Pending Payment Management ===
    
    async def add_pending_payment(self, amount, user_id, plan_days):
        """Adds a pending payment with a 15-minute expiry."""
        # MongoDB TTL index is needed for this to work automatically.
        # Create it once manually in your MongoDB collection:
        # db.pending_payments.createIndex( { "createdAt": 1 }, { expireAfterSeconds: 900 } )
        await self.pending.insert_one({
            'amount': str(amount),
            'user_id': int(user_id),
            'plan_days': int(plan_days),
            'createdAt': datetime.utcnow()
        })

    async def get_pending_payment(self, amount):
        """Gets a pending payment by amount."""
        # Also remove payments older than 15 minutes
        await self.pending.delete_many({'createdAt': {'$lt': datetime.utcnow() - timedelta(minutes=15)}})
        return await self.pending.find_one({'amount': str(amount)})

    async def remove_pending_payment(self, amount):
        """Removes a pending payment."""
        await self.pending.delete_one({'amount': str(amount)})


# Initialize the database instance
sub_db = SubDB(Config.DATABASE_URL, Config.DATABASE_NAME)
