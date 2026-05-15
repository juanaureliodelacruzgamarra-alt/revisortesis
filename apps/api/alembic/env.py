"""Alembic environment.

Uses async SQLAlchemy engine. Imports kimy.models so autogenerate picks up
every mapped class.
"""
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from kimy.core.config import get_settings
from kimy.db.base import Base
from kimy.models import *  # noqa: F401,F403  -- ensure all models are imported

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", get_settings().database_url)

target_metadata = Base.metadata


# Indexes managed manually via raw SQL (pgvector HNSW, anything with custom
# operator classes) should be invisible to autogenerate, otherwise it tries to
# drop them on every revision.
_IGNORED_INDEX_NAMES = {"ix_document_chunks_embedding_hnsw"}


def _include_object(object, name, type_, reflected, compare_to) -> bool:
    if type_ == "index" and name in _IGNORED_INDEX_NAMES:
        return False
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_object=_include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        include_object=_include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
