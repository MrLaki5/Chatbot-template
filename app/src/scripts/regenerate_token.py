#!/usr/bin/env python3
"""
Bearer token regeneration utility script for video intelligence

This script regenerates the bearer token by deleting any existing one and creating a new one.
Just run: python regenerate_token.py
"""

import os
import sys

# Add the parent directory (src) to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orm.crud import regenerate_bearer
from orm.database import get_db


def main():
    """Regenerate bearer token - delete existing and create new one"""
    print("Video Intelligence Bearer Token Regeneration")
    print("==========================================")
    print()
    print("Regenerating bearer token...")

    try:
        # Regenerate bearer token
        db = next(get_db())
        try:
            bearer_record = regenerate_bearer(db)
            bearer_token = bearer_record.bearer_token
            print("✓ Bearer token regenerated successfully!")
            print(f"New Bearer Token: {bearer_token}")
            print("✓ Token regeneration completed successfully!")
            return bearer_token
        finally:
            db.close()

    except Exception as e:
        print(f"✗ Token regeneration failed: {e}")
        return None


if __name__ == "__main__":
    main()
