import motor.motor_asyncio
from bot.config import Config

class MovieDatabase:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(Config.DATABASE_URL)
        self.db = self.client[Config.DATABASE_NAME]
        self.collection = self.db["movies"]

    async def get_movie(self, movie_id):
        return await self.collection.find_one({"movie_id": movie_id})

    async def update_movie(self, movie_id, data):
        return await self.collection.update_one(
            {"movie_id": movie_id},
            {"$set": data},
            upsert=True
        )

    async def add_file_to_movie(self, movie_id, file_data):
        return await self.collection.update_one(
            {"movie_id": movie_id},
            {"$addToSet": {"files": file_data}},
            upsert=True
        )

    async def find_by_name(self, name):
        return await self.collection.find_one({"name": name})

movie_db = MovieDatabase()
