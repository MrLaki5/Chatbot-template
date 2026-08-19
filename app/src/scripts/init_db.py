#!/usr/bin/env python3
"""
Database initialization utility script for video intelligence

This script creates database tables and generates a bearer token.
Just run: python init_db.py
"""

import os
import sys

# Add the parent directory (src) to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orm.crud import regenerate_bearer
from orm.database import create_tables, get_db


def main():
    """Initialize database - create tables and generate bearer token"""
    print("Video Intelligence Database Initialization")
    print("===================================")
    print()
    print("Creating database tables and generating bearer token...")

    try:
        # Create database tables
        create_tables()
        print("✓ Database tables created successfully!")

        # Generate bearer token
        db = next(get_db())
        try:
            bearer_record = regenerate_bearer(db)
            bearer_token = bearer_record.bearer_token
            print("✓ Bearer token generated successfully!")
            print(f"Bearer Token: {bearer_token}")
            print("✓ Database initialization completed successfully!")
            return bearer_token
        finally:
            db.close()

    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return None


if __name__ == "__main__":
    main()
