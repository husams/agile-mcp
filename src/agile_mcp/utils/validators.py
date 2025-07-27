"""
Shared validation utilities for consistent validation across the application.
"""

import re
from typing import Set


class URIValidator:
    """Utility class for URI validation with consistent patterns."""

    # URI pattern matching scheme:[rest] with no whitespace
    URI_PATTERN = re.compile(
        r"^[a-zA-Z][a-zA-Z\d+\-.]*:"  # scheme
        r"[^\s]*$"  # rest of URI (no whitespace)
    )

    @classmethod
    def is_valid_uri(cls, uri: str) -> bool:
        """
        Validate URI format using consistent pattern.

        Args:
            uri: The URI string to validate

        Returns:
            bool: True if URI format is valid, False otherwise
        """
        if not uri or not uri.strip():
            return False
        return bool(cls.URI_PATTERN.match(uri.strip()))

    @classmethod
    def validate_uri_or_raise(cls, uri: str, max_length: int = 500) -> str:
        """
        Validate URI and raise ValueError if invalid.

        Args:
            uri: The URI string to validate
            max_length: Maximum allowed length for the URI

        Returns:
            str: The trimmed URI if valid

        Raises:
            ValueError: If URI is invalid
        """
        if not uri or not uri.strip():
            raise ValueError("Artifact URI cannot be empty")

        uri = uri.strip()

        if len(uri) > max_length:
            raise ValueError(f"Artifact URI cannot exceed {max_length} characters")

        if not cls.is_valid_uri(uri):
            raise ValueError("Artifact URI must be a valid URI format")

        return uri


class RelationValidator:
    """Utility class for artifact relation type validation."""

    VALID_RELATIONS: Set[str] = {"implementation", "design", "test"}

    @classmethod
    def is_valid_relation(cls, relation: str) -> bool:
        """
        Check if relation type is valid.

        Args:
            relation: The relation type to validate

        Returns:
            bool: True if relation is valid, False otherwise
        """
        return relation in cls.VALID_RELATIONS

    @classmethod
    def validate_relation_or_raise(cls, relation: str) -> str:
        """
        Validate relation type and raise ValueError if invalid.

        Args:
            relation: The relation type to validate

        Returns:
            str: The relation if valid

        Raises:
            ValueError: If relation is invalid
        """
        if not cls.is_valid_relation(relation):
            raise ValueError(
                f"Artifact relation must be one of: "
                f"{', '.join(sorted(cls.VALID_RELATIONS))}"
            )
        return relation
