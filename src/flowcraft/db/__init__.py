"""Database-backed repository for FlowCraft entities.

Replaces the in-memory store with SQLAlchemy-based persistence.
Falls back to in-memory store when database is unavailable.
"""

import os
from typing import Optional

DATABASE_URL = os.getenv("DATABASE_URL", "")


async def get_store():
    """Get the active store implementation.

    If DATABASE_URL is configured, returns a database-backed store.
    Otherwise, falls back to in-memory store for MVP convenience.
    """
    if DATABASE_URL:
        try:
            from .db_store import DbStore

            store = DbStore()
            await store.init()
            return store
        except Exception:
            pass

    # Fallback to in-memory store
    from ..api.store import store as mem_store

    return mem_store
