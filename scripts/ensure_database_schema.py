#!/usr/bin/env python3
"""
Ensure database schema is up to date.

This script checks if the database schema matches the current model definitions
and applies any necessary migrations. It's safe to run multiple times.
"""

import sys
from pathlib import Path

from sqlalchemy import text

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agile_mcp.database import create_tables, engine  # noqa: E402


def check_column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    try:
        with engine.connect() as conn:
            # For SQLite, use PRAGMA table_info to check columns
            result = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
            columns = [row[1] for row in result]  # Column name is at index 1
            return column_name in columns
    except Exception:
        return False


def ensure_structured_acceptance_criteria_column():
    """Ensure the structured_acceptance_criteria column exists in the stories table."""
    if not check_column_exists("stories", "structured_acceptance_criteria"):
        print("Adding structured_acceptance_criteria column to stories table...")
        try:
            with engine.connect() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE stories ADD COLUMN "
                        "structured_acceptance_criteria JSON NOT NULL DEFAULT '[]'"
                    )
                )
                conn.commit()
            print("✓ Added structured_acceptance_criteria column successfully")
            return True
        except Exception as e:
            print(f"✗ Failed to add structured_acceptance_criteria column: {e}")
            return False
    else:
        print("✓ structured_acceptance_criteria column already exists")
        return True


def ensure_comments_column():
    """Ensure the comments column exists in the stories table."""
    if not check_column_exists("stories", "comments"):
        print("Adding comments column to stories table...")
        try:
            with engine.connect() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE stories ADD COLUMN "
                        "comments JSON NOT NULL DEFAULT '[]'"
                    )
                )
                conn.commit()
            print("✓ Added comments column successfully")
            return True
        except Exception as e:
            print(f"✗ Failed to add comments column: {e}")
            return False
    else:
        print("✓ comments column already exists")
        return True


def ensure_database_schema():
    """Ensure database schema is up to date."""
    print("Ensuring database schema is up to date...")

    # First, create all tables (this is safe to run multiple times)
    try:
        create_tables()
        print("✓ Base tables created/verified")
    except Exception as e:
        print(f"✗ Failed to create base tables: {e}")
        return False

    # Apply specific migrations
    migrations = [
        ensure_structured_acceptance_criteria_column,
        ensure_comments_column,
    ]

    for migration in migrations:
        if not migration():
            return False

    print("✓ Database schema is up to date")
    return True


if __name__ == "__main__":
    print("Database Schema Migration Script")
    print("=" * 40)

    success = ensure_database_schema()
    if success:
        print("\n✅ Database schema update completed successfully!")
    else:
        print("\n❌ Database schema update failed!")
        sys.exit(1)
