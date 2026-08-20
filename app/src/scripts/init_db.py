#!/usr/bin/env python3
"""Rebuild the database from scratch.

Drops every table and creates them again, empty. Run it with:

    docker compose exec app python scripts/init_db.py
"""

import asyncio
import os
import sys

# Add the parent directory (src) to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orm.database import dispose_engine, get_engine
from orm.models import Base


async def rebuild():
    """Drop every table and create them again, empty."""
    print("Rebuilding the database...")

    try:
        async with get_engine().begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

        print("✓ All tables dropped and recreated. The database is empty.")
    except Exception as e:
        print(f"✗ Database rebuild failed: {e}")
        raise
    finally:
        await dispose_engine()


if __name__ == "__main__":
    asyncio.run(rebuild())
