"""
Custom exceptions for service layer business logic.
"""


class EpicValidationError(Exception):
    """Raised when epic data validation fails."""
    pass


class EpicNotFoundError(Exception):
    """Raised when requested epic is not found."""
    pass


class DatabaseError(Exception):
    """Raised when database operations fail."""
    pass