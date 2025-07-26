"""
Data Access/Repository Layer

This module contains database access abstractions and repository pattern
implementations for data persistence operations.
"""

from .epic_repository import EpicRepository

__all__ = ["EpicRepository"]