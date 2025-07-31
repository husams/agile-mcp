"""
Integration utilities for working with the document system.

This module provides utilities for integrating with the documents.getSection tool
and other document-related functionality for context compilation.
"""

from typing import Any, Dict, List, Optional


class DocumentIntegrationError(Exception):
    """Exception raised when document integration fails."""

    pass


class DocumentIntegrator:
    """Utility class for integrating with the document system."""

    def __init__(self, document_client=None):
        """
        Initialize the document integrator.

        Args:
            document_client: Optional client for document operations
        """
        self.document_client = document_client

    async def get_section_content(
        self,
        document_id: str,
        section_name: str,
        project_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Retrieve content from a specific document section.

        Args:
            document_id: The unique identifier of the document
            section_name: The name/title of the section to retrieve
            project_id: Optional project ID for scoped lookup

        Returns:
            Section content as string, or None if not found

        Raises:
            DocumentIntegrationError: If the document operation fails
        """
        try:
            if self.document_client:
                # Use the actual document client
                result = await self.document_client.get_section(
                    document_id=document_id,
                    section_name=section_name,
                    project_id=project_id,
                )
                return result.get("content") if result else None
            else:
                # Return mock data for development/testing
                return self._get_mock_section_content(document_id, section_name)

        except Exception as e:
            raise DocumentIntegrationError(
                f"Failed to retrieve section '{section_name}' from document "
                f"'{document_id}': {str(e)}"
            )

    def _get_mock_section_content(
        self, document_id: str, section_name: str
    ) -> Optional[str]:
        """
        Provide mock section content for development and testing.

        This method should be removed when the actual document system is implemented.
        """
        mock_sections = {
            "architecture": {
                "overview": """
                This system uses a microservices architecture with JWT authentication.
                Key components include:
                - API Gateway for request routing
                - Authentication Service for user management
                - Business Logic Services for core functionality
                - Database Layer with PostgreSQL and Redis
                """,
                "authentication": """
                Authentication Strategy:
                - JWT tokens for stateless authentication
                - Redis for session storage and token blacklisting
                - bcrypt for password hashing with salt rounds=12
                - Token expiry: 24 hours for access tokens, 7 days for refresh tokens
                """,
                "database": """
                Database Design:
                - PostgreSQL for persistent data storage
                - Redis for caching and session management
                - SQLAlchemy ORM for database operations
                - Alembic for database migrations
                """,
                "patterns": """
                Architectural Patterns:
                - Repository Pattern for data access abstraction
                - Service Layer for business logic encapsulation
                - Factory Pattern for object creation
                - Observer Pattern for event handling
                """,
            },
            "api-specs": {
                "authentication": """
                Authentication Endpoints:

                POST /api/auth/login
                - Request: {"email": "string", "password": "string"}
                - Response: {"access_token": "string", "refresh_token": "string", \
"user_id": "string"}

                POST /api/auth/refresh
                - Request: {"refresh_token": "string"}
                - Response: {"access_token": "string"}

                POST /api/auth/logout
                - Request: {"refresh_token": "string"}
                - Response: {"message": "Logged out successfully"}
                """,
                "user-management": """
                User Management Endpoints:

                GET /api/users/profile
                - Headers: Authorization: Bearer <token>
                - Response: {"id": "string", "email": "string", "name": "string", \
"created_at": "datetime"}

                PUT /api/users/profile
                - Headers: Authorization: Bearer <token>
                - Request: {"name": "string", "email": "string"}
                - Response: {"id": "string", "email": "string", "name": "string", \
"updated_at": "datetime"}
                """,
            },
            "coding-standards": {
                "python": """
                Python Coding Standards:
                - Use PEP 8 style guide
                - Maximum line length: 88 characters (Black formatter)
                - Use type hints for all function parameters and returns
                - Use docstrings for all public functions and classes
                - Import organization: standard library, third-party, local imports
                """,
                "testing": """
                Testing Standards:
                - Unit tests for all business logic
                - Integration tests for API endpoints
                - Test coverage minimum: 80%
                - Use pytest framework
                - Mock external dependencies
                - Test file naming: test_<module_name>.py
                """,
                "security": """
                Security Guidelines:
                - Never log sensitive information (passwords, tokens)
                - Use parameterized queries to prevent SQL injection
                - Validate all input data
                - Use HTTPS for all communications
                - Implement rate limiting on public endpoints
                """,
            },
        }

        document_content = mock_sections.get(document_id, {})
        return document_content.get(section_name)

    async def get_multiple_sections(
        self,
        sections: List[Dict[str, str]],
        project_id: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Retrieve content from multiple document sections.

        Args:
            sections: List of dicts with 'document_id' and 'section_name' keys
            project_id: Optional project ID for scoped lookup

        Returns:
            Dictionary mapping section keys to content

        Raises:
            DocumentIntegrationError: If any document operation fails
        """
        results: Dict[str, str] = {}

        for section_spec in sections:
            document_id = section_spec.get("document_id")
            section_name = section_spec.get("section_name")

            if not document_id or not section_name:
                continue

            section_key = f"{document_id}.{section_name}"
            try:
                content = await self.get_section_content(
                    document_id=document_id,
                    section_name=section_name,
                    project_id=project_id,
                )
                if content:
                    results[section_key] = content
            except DocumentIntegrationError:
                # Log the error but continue with other sections
                results[section_key] = f"[Error retrieving section: {section_key}]"

        return results

    def create_context_from_document_sections(
        self,
        section_contents: Dict[str, str],
        context_mapping: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a structured context dictionary from document section contents.

        Args:
            section_contents: Dictionary mapping section keys to content
            context_mapping: Optional mapping of section keys to context paths

        Returns:
            Structured context dictionary for use with ContextCompiler
        """
        if not context_mapping:
            context_mapping = self._get_default_context_mapping()

        context: Dict[str, Any] = {}

        for section_key, content in section_contents.items():
            # Determine the context path for this section
            context_path = context_mapping.get(section_key)
            if not context_path:
                continue

            # Navigate/create the nested context structure
            path_parts = context_path.split(".")
            current_context = context

            for i, part in enumerate(path_parts):
                if i == len(path_parts) - 1:
                    # Last part - set the value
                    current_context[part] = content
                else:
                    # Intermediate part - ensure dict exists
                    if part not in current_context:
                        current_context[part] = {}
                    current_context = current_context[part]

        return context

    def _get_default_context_mapping(self) -> Dict[str, str]:
        """Get the default mapping of document sections to context paths."""
        return {
            "architecture.overview": "architecture.overview",
            "architecture.authentication": "architecture.auth_strategy",
            "architecture.database": "architecture.database_design",
            "architecture.patterns": "architecture.patterns",
            "api-specs.authentication": "api.auth_endpoints",
            "api-specs.user-management": "api.user_endpoints",
            "coding-standards.python": "standards.python",
            "coding-standards.testing": "testing.standards",
            "coding-standards.security": "constraints.security",
        }

    async def validate_document_access(
        self,
        document_ids: List[str],
        project_id: Optional[str] = None,
    ) -> Dict[str, bool]:
        """
        Validate that the specified documents are accessible.

        Args:
            document_ids: List of document IDs to validate
            project_id: Optional project ID for scoped validation

        Returns:
            Dictionary mapping document IDs to accessibility status
        """
        results: Dict[str, bool] = {}

        for document_id in document_ids:
            try:
                if self.document_client:
                    # Use the actual document client
                    content = await self.get_section_content(
                        document_id=document_id,
                        section_name="overview",  # Common section name
                        project_id=project_id,
                    )
                    results[document_id] = content is not None
                else:
                    # Check if document exists in mock data
                    mock_sections: Dict[str, Dict[str, str]] = {
                        "architecture": {
                            "overview": "Mock content",
                            "authentication": "Mock content",
                            "database": "Mock content",
                            "patterns": "Mock content",
                        },
                        "api-specs": {
                            "authentication": "Mock content",
                            "user-management": "Mock content",
                        },
                        "coding-standards": {
                            "python": "Mock content",
                            "testing": "Mock content",
                            "security": "Mock content",
                        },
                    }
                    results[document_id] = document_id in mock_sections
            except DocumentIntegrationError:
                results[document_id] = False

        return results

    def create_section_request_batch(
        self,
        document_sections: Dict[str, List[str]],
    ) -> List[Dict[str, str]]:
        """
        Create a batch of section requests from a document-sections mapping.

        Args:
            document_sections: Dictionary mapping document IDs to section names

        Returns:
            List of section request dictionaries
        """
        requests: List[Dict[str, str]] = []

        for document_id, section_names in document_sections.items():
            for section_name in section_names:
                requests.append(
                    {
                        "document_id": document_id,
                        "section_name": section_name,
                    }
                )

        return requests


class DocumentContextBuilder:
    """Builder class for creating context from document sources."""

    def __init__(self, integrator: DocumentIntegrator):
        """Initialize with a document integrator."""
        self.integrator = integrator
        self.section_requests: List[Dict[str, str]] = []
        self.context_mapping: Dict[str, str] = {}

    def add_section(
        self,
        document_id: str,
        section_name: str,
        context_path: str,
    ) -> "DocumentContextBuilder":
        """
        Add a document section to be retrieved and mapped to a context path.

        Args:
            document_id: The document to retrieve from
            section_name: The section within the document
            context_path: The path in the context dictionary \
(e.g., "architecture.overview")

        Returns:
            Self for method chaining
        """
        self.section_requests.append(
            {
                "document_id": document_id,
                "section_name": section_name,
            }
        )
        section_key = f"{document_id}.{section_name}"
        self.context_mapping[section_key] = context_path
        return self

    def add_architecture_context(
        self,
        document_id: str = "architecture",
        sections: Optional[List[str]] = None,
    ) -> "DocumentContextBuilder":
        """
        Add common architecture sections to the context.

        Args:
            document_id: The architecture document ID
            sections: List of section names, defaults to common architecture sections

        Returns:
            Self for method chaining
        """
        if sections is None:
            sections = ["overview", "patterns", "authentication", "database"]

        section_mapping = {
            "overview": "architecture.overview",
            "patterns": "architecture.patterns",
            "authentication": "architecture.auth_strategy",
            "database": "architecture.database_design",
        }

        for section in sections:
            if section in section_mapping:
                self.add_section(
                    document_id=document_id,
                    section_name=section,
                    context_path=section_mapping[section],
                )

        return self

    def add_api_context(
        self,
        document_id: str = "api-specs",
        sections: Optional[List[str]] = None,
    ) -> "DocumentContextBuilder":
        """
        Add common API specification sections to the context.

        Args:
            document_id: The API specifications document ID
            sections: List of section names, defaults to common API sections

        Returns:
            Self for method chaining
        """
        if sections is None:
            sections = ["authentication", "user-management"]

        section_mapping = {
            "authentication": "api.auth_endpoints",
            "user-management": "api.user_endpoints",
        }

        for section in sections:
            if section in section_mapping:
                self.add_section(
                    document_id=document_id,
                    section_name=section,
                    context_path=section_mapping[section],
                )

        return self

    async def build(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Build the context dictionary by retrieving all requested sections.

        Args:
            project_id: Optional project ID for scoped document access

        Returns:
            Structured context dictionary ready for use with ContextCompiler

        Raises:
            DocumentIntegrationError: If document retrieval fails
        """
        if not self.section_requests:
            return {}

        # Retrieve all section contents
        section_contents = await self.integrator.get_multiple_sections(
            sections=self.section_requests,
            project_id=project_id,
        )

        # Create structured context
        return self.integrator.create_context_from_document_sections(
            section_contents=section_contents,
            context_mapping=self.context_mapping,
        )


# Convenience functions for common use cases
async def get_architecture_context(
    integrator: DocumentIntegrator,
    project_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Get common architecture context from documents."""
    builder = DocumentContextBuilder(integrator)
    builder.add_architecture_context()
    return await builder.build(project_id)


async def get_api_context(
    integrator: DocumentIntegrator,
    project_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Get common API context from documents."""
    builder = DocumentContextBuilder(integrator)
    builder.add_api_context()
    return await builder.build(project_id)


async def get_full_development_context(
    integrator: DocumentIntegrator,
    project_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Get comprehensive development context from documents."""
    builder = DocumentContextBuilder(integrator)
    builder.add_architecture_context()
    builder.add_api_context()
    builder.add_section("coding-standards", "testing", "testing.standards")
    builder.add_section("coding-standards", "security", "constraints.security")
    return await builder.build(project_id)
