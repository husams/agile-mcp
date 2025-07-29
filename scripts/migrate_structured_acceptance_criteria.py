#!/usr/bin/env python3
"""
Migration script to add structured_acceptance_criteria field to existing stories.

This script converts existing string-based acceptance criteria to the new
structured format for stories that don't already have structured criteria.
"""

import sys
import uuid
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agile_mcp.database import create_tables, get_db
from agile_mcp.models.story import Story


def convert_acceptance_criteria_to_structured(acceptance_criteria_list):
    """Convert list of string criteria to structured format."""
    structured_criteria = []
    for i, criterion in enumerate(acceptance_criteria_list):
        structured_criteria.append(
            {
                "id": str(uuid.uuid4()),
                "description": criterion.strip(),
                "met": False,
                "order": i + 1,
            }
        )
    return structured_criteria


def migrate_stories():
    """Migrate existing stories to include structured acceptance criteria."""
    print("Starting migration of acceptance criteria to structured format...")

    # Ensure tables exist
    create_tables()

    db = get_db()
    try:
        # Get all stories that don't have structured_acceptance_criteria
        # field or have empty list
        stories = db.query(Story).all()

        migration_count = 0

        for story in stories:
            # Check if story needs migration (either no field or empty
            # structured criteria)
            needs_migration = (
                not hasattr(story, "structured_acceptance_criteria")
                or not story.structured_acceptance_criteria
                or len(story.structured_acceptance_criteria) == 0
            )

            if needs_migration and story.acceptance_criteria:
                print(f"Migrating story {story.id}: {story.title}")

                # Convert existing acceptance criteria to structured
                # format
                structured_criteria = convert_acceptance_criteria_to_structured(
                    story.acceptance_criteria
                )

                # Update the story with structured criteria
                story.structured_acceptance_criteria = structured_criteria

                migration_count += 1

                print(
                    f"  - Converted {len(structured_criteria)} criteria to "
                    f"structured format"
                )

        # Commit all changes
        db.commit()

        print("\nMigration completed successfully!")
        print(
            f"Migrated {migration_count} stories to structured "
            f"acceptance criteria format."
        )

    except Exception as e:
        print(f"Migration failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()

    return True


def verify_migration():
    """Verify that migration was successful."""
    print("\nVerifying migration...")

    db = get_db()
    try:
        stories = db.query(Story).all()

        for story in stories:
            if not story.structured_acceptance_criteria:
                print(
                    f"Warning: Story {story.id} has no structured "
                    f"acceptance criteria"
                )
            else:
                print(
                    f"✓ Story {story.id} has "
                    f"{len(story.structured_acceptance_criteria)} "
                    f"structured criteria"
                )

        print("Verification completed.")

    except Exception as e:
        print(f"Verification failed: {e}")
        return False
    finally:
        db.close()

    return True


if __name__ == "__main__":
    print("Structured Acceptance Criteria Migration Script")
    print("=" * 50)

    success = migrate_stories()
    if success:
        verify_migration()
        print("\nMigration completed successfully!")
    else:
        print("\nMigration failed!")
        sys.exit(1)
