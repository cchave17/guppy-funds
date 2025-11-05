from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings


class Database:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None


db = Database()


async def connect_to_mongo():
    """Connect to MongoDB on application startup."""
    db.client = AsyncIOMotorClient(settings.mongodb_url)
    db.db = db.client[settings.mongodb_db_name]
    print(f"Connected to MongoDB: {settings.mongodb_db_name}")


async def close_mongo_connection():
    """Close MongoDB connection on application shutdown."""
    if db.client:
        db.client.close()
        print("Closed MongoDB connection")


def get_database() -> AsyncIOMotorDatabase:
    """Get database instance."""
    return db.db
