#!/usr/bin/env python
"""
Migrate database schema by dropping and recreating tables.
Use this to sync the database schema with model changes.
"""

import sys
from sqlalchemy import text

# Add packages to path
sys.path.insert(0, "/Users/omid.houshyar/dev/ai-rag")

from packages.core.db import Base, engine
from packages.core.models import Document, Chunk, Run, ToolRun


def migrate():
    """Drop all tables and recreate them from models."""
    print("Dropping all tables...")
    with engine.begin() as conn:
        # Create vector extension if not exists
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # Drop all tables in correct order (handles foreign keys)
        Base.metadata.drop_all(bind=conn)

    print("Recreating all tables from models...")
    with engine.begin() as conn:
        # Create all tables
        Base.metadata.create_all(bind=conn)

    print("✓ Database migration complete!")


if __name__ == "__main__":
    migrate()
