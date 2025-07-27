"""
Custom exceptions for service layer business logic.
"""


class EpicValidationError(Exception):
    """Raised when epic data validation fails."""
    pass


class EpicNotFoundError(Exception):
    """Raised when requested epic is not found."""
    pass


class InvalidEpicStatusError(Exception):
    """Raised when an invalid epic status is provided."""
    pass


class StoryValidationError(Exception):
    """Raised when story data validation fails."""
    pass


class StoryNotFoundError(Exception):
    """Raised when requested story is not found."""
    pass


class InvalidStoryStatusError(Exception):
    """Raised when an invalid story status is provided."""
    pass


class DatabaseError(Exception):
    """Raised when database operations fail."""
    pass