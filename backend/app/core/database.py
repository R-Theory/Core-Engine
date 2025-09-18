from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import QueuePool
from sqlalchemy import event
from app.core.config import settings
import logging
import time
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# Create async engine with optimized connection pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True if settings.ENVIRONMENT == "development" else False,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=50,
    pool_timeout=30,
    pool_recycle=1800,  # Recycle connections every 30 minutes
    pool_pre_ping=True,
    pool_reset_on_return='commit',
    connect_args={
        "server_settings": {
            "application_name": "core_engine",
            "jit": "off",  # Disable JIT for faster connection times
        },
        "command_timeout": 60,
    },
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

@asynccontextmanager
async def get_db_transaction():
    """Context manager for database transactions with automatic rollback on error"""
    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def get_db_health():
    """Check database health and connection pool status"""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
            pool = engine.pool
            return {
                "status": "healthy",
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid(),
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

async def init_db():
    """Initialize database tables"""
    try:
        async with engine.begin() as conn:
            # Import all models to ensure they're registered
            from app.models import user, course, assignment, resource, plugin, workflow, agent
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")

        # Log initial pool status
        pool_info = await get_db_health()
        logger.info(f"Database pool initialized: {pool_info}")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

# Database performance monitoring
@event.listens_for(engine.sync_engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(engine.sync_engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    if total > 1.0:  # Log slow queries
        logger.warning(f"Slow query detected: {total:.2f}s - {statement[:100]}...")