#!/usr/bin/env python3
"""Rebuild the database from scratch.

Downgrades every migration and upgrades back to head, which leaves the tables in place
and empty. Run it with:

    docker compose exec app python scripts/init_db.py
"""

import os
import sys

# Add the parent directory (src) to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alembic import command
from alembic.config import Config
from orm.database import ALEMBIC_INI


def rebuild():
    """Drop every table and create them again, empty."""
    print("Rebuilding the database...")

    try:
        alembic_cfg = Config(ALEMBIC_INI)
        # Each revision's downgrade drops what its upgrade created, in the right order
        command.downgrade(alembic_cfg, "base")
        command.upgrade(alembic_cfg, "head")

        print("✓ All tables dropped and recreated. The database is empty.")
    except Exception as e:
        print(f"✗ Database rebuild failed: {e}")
        raise


if __name__ == "__main__":
    rebuild()
