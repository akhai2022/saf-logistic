import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def to_sync_url(url: str) -> str:
    """Convert async driver URL to sync for Alembic offline mode."""
    return url.replace("+asyncpg", "+psycopg").replace("+aiosqlite", "")


def get_url() -> str:
    return os.getenv(
        "DATABASE_URL",
        config.get_main_option("sqlalchemy.url", "postgresql+asyncpg://saf:saf@localhost:5432/saf"),
    )


def run_migrations_offline() -> None:
    url = to_sync_url(get_url())
    context.configure(url=url, target_metadata=None, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=None)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    url = get_url()
    # Ensure async driver
    if "+psycopg" in url and "+asyncpg" not in url:
        url = url.replace("+psycopg", "+asyncpg")

    connectable = create_async_engine(url, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
