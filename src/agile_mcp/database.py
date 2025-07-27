"""
Database configuration and setup for the Agile Management MCP Server.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .models.epic import Base
from .models import Story  # Import to register with metadata
from .models import Artifact  # Import to register with metadata

# Database file path
DATABASE_URL = "sqlite:///agile_mcp.db"

# Create engine with proper SQLite configuration
engine = create_engine(
    DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
    echo=False
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Get database session."""
    return SessionLocal()