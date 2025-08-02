import asyncpg
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from core.config import settings
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.sync_engine = create_engine(settings.database_url)
        # Convert postgresql:// to postgresql+asyncpg:// for async
        async_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
        self.async_engine = create_async_engine(async_url)
        self.async_session_factory = sessionmaker(
            self.async_engine, class_=AsyncSession, expire_on_commit=False
        )

    @asynccontextmanager
    async def get_async_session(self):
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    def get_sync_connection(self):
        """For synchronous operations like detection tracking"""
        return psycopg2.connect(settings.database_url)

    async def close(self):
        await self.async_engine.dispose()

# Global instance
db_manager = DatabaseManager()
