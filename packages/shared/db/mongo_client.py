import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from ..models.headline import Headline
from ..models.summary import Summary

_client: AsyncIOMotorClient | None = None


async def init_db() -> None:
    """Initialize Beanie ODM with MongoDB Atlas connection."""
    global _client

    uri = os.environ["MONGODB_URI"]
    db_name = os.environ.get("MONGODB_DB_NAME", "ph_news")

    _client = AsyncIOMotorClient(uri)

    await init_beanie(
        database=_client[db_name],
        document_models=[Headline, Summary],
    )


async def close_db() -> None:
    """Close the MongoDB connection."""
    global _client
    if _client:
        _client.close()
        _client = None