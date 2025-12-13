"""
Initialize the database and create tables.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import create_async_engine
from backend.app.models.database import Base
from backend.app.core.config import settings


async def init_db():
    """Initialize database tables"""
    print(f"Connecting to database: {settings.DATABASE_URL}")

    engine = create_async_engine(settings.DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        print("Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)

        print("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()

    print("Database initialized successfully!")


if __name__ == "__main__":
    asyncio.run(init_db())
