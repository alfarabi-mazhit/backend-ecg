from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import HTTPException

class Database:
    client: AsyncIOMotorClient = None

    @staticmethod
    async def connect_to_mongo(uri: str):
        try:
            Database.client = AsyncIOMotorClient(uri)
            await Database.client.admin.command('ping')  # Ensure the database is reachable
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database connection error: {e}")

    @staticmethod
    async def close_mongo_connection():
        if Database.client:
            Database.client.close()
