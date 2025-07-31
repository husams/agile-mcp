"""
Custom exceptions for service layer business logic.
"""


class ProjectValidationError(Exception):
    """Raised when project data validation fails."""

    pass


class ProjectNotFoundError(Exception):
    """Raised when requested project is not found."""

    pass


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


class ArtifactValidationError(Exception):
    """Raised when artifact data validation fails."""

    pass


class ArtifactNotFoundError(Exception):
    """Raised when requested artifact is not found."""

    pass


class InvalidRelationTypeError(Exception):
    """Raised when an invalid artifact relation type is provided."""

    pass


class SectionNotFoundError(Exception):
    """Raised when requested story section is not found."""

    pass


class CircularDependencyError(Exception):
    """Raised when adding a dependency would create a circular dependency."""

    pass


class DependencyValidationError(Exception):
    """Raised when dependency data validation fails."""

    pass


class DuplicateDependencyError(Exception):
    """Raised when attempting to add a dependency that already exists."""

    pass
