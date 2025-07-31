"""
Unit tests for the ContextCompiler utility.
"""

import json

from src.agile_mcp.utils.context_compiler import (
    ContextCompiler,
    compile_api_dev_notes,
    compile_basic_dev_notes,
    create_context_from_documents,
)


class TestContextCompiler:
    """Test cases for the ContextCompiler class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.compiler = ContextCompiler()
        self.sample_contexts = {
            "architecture": {
                "overview": "Use JWT tokens with Redis session storage",
                "patterns": ["Repository Pattern", "Service Layer"],
                "dependencies": ["redis", "pyjwt", "sqlalchemy"],
            },
            "implementation": {
                "files": ["src/auth/auth_service.py", "src/models/user.py"],
                "methods": ["authenticate_user()", "generate_jwt_token()"],
                "entry_points": ["/api/auth/login", "/api/auth/logout"],
            },
            "constraints": {
                "technical": [
                    "Token expiry: 24 hours",
                    "Session cleanup: Every 4 hours",
                ],
                "business": ["Password must contain special characters"],
            },
            "testing": {
                "unit": "Test authentication service methods",
                "integration": "Test full auth flow with Redis",
                "e2e": "Test login/logout user journey",
            },
        }

    def test_basic_template_compilation(self):
        """Test compilation using the basic template."""
        dev_notes_json = self.compiler.compile_dev_notes(self.sample_contexts, "basic")

        dev_notes = json.loads(dev_notes_json)

        # Check that main sections are present
        assert "architecture" in dev_notes
        assert "implementation" in dev_notes
        assert "testing_guidance" in dev_notes
        assert "_metadata" in dev_notes

        # Check that context references were resolved
        assert (
            dev_notes["architecture"]["overview"]
            == "Use JWT tokens with Redis session storage"
        )
        assert dev_notes["architecture"]["patterns"] == [
            "Repository Pattern",
            "Service Layer",
        ]
        assert dev_notes["technical_constraints"] == [
            "Token expiry: 24 hours",
            "Session cleanup: Every 4 hours",
        ]

        # Check metadata
        assert "compiled_at" in dev_notes["_metadata"]
        assert dev_notes["_metadata"]["template_used"] == "basic"
        assert "architecture" in dev_notes["_metadata"]["context_sources"]

    def test_api_development_template(self):
        """Test compilation using the API development template."""
        api_contexts = {
            **self.sample_contexts,
            "api": {
                "endpoints": [
                    {"method": "POST", "path": "/api/auth/login"},
                    {"method": "POST", "path": "/api/auth/logout"},
                ],
                "request_models": ["LoginRequest", "LogoutRequest"],
                "response_models": ["AuthResponse", "ErrorResponse"],
                "authentication": "JWT Bearer token",
            },
        }

        dev_notes_json = self.compiler.compile_dev_notes(
            api_contexts, "api_development"
        )

        dev_notes = json.loads(dev_notes_json)

        # Check API-specific sections
        assert "api_specification" in dev_notes
        assert "validation" in dev_notes
        assert (
            dev_notes["api_specification"]["endpoints"]
            == api_contexts["api"]["endpoints"]
        )
        assert dev_notes["api_specification"]["authentication"] == "JWT Bearer token"

    def test_custom_template(self):
        """Test compilation using a custom template."""
        custom_template = {
            "custom_section": {
                "custom_field": "$architecture.overview",
                "static_field": "static_value",
            }
        }

        dev_notes_json = self.compiler.compile_dev_notes(
            self.sample_contexts, custom_template=custom_template
        )

        dev_notes = json.loads(dev_notes_json)

        assert "custom_section" in dev_notes
        assert (
            dev_notes["custom_section"]["custom_field"]
            == "Use JWT tokens with Redis session storage"
        )
        assert dev_notes["custom_section"]["static_field"] == "static_value"

    def test_missing_context_handling(self):
        """Test handling of missing context references."""
        incomplete_contexts = {
            "architecture": {
                "overview": "Some overview",
            }
            # Missing other expected contexts
        }

        dev_notes_json = self.compiler.compile_dev_notes(incomplete_contexts, "basic")

        dev_notes = json.loads(dev_notes_json)

        # Should have placeholder for missing context
        assert "[Context not found:" in str(dev_notes)
        assert dev_notes["architecture"]["overview"] == "Some overview"

    def test_context_reference_resolution(self):
        """Test resolution of context references."""
        # Test simple reference
        result = self.compiler._resolve_context_reference(
            "$architecture.overview", self.sample_contexts
        )
        assert result == "Use JWT tokens with Redis session storage"

        # Test nested reference
        result = self.compiler._resolve_context_reference(
            "$constraints.technical", self.sample_contexts
        )
        assert result == ["Token expiry: 24 hours", "Session cleanup: Every 4 hours"]

        # Test missing reference
        result = self.compiler._resolve_context_reference(
            "$missing.reference", self.sample_contexts
        )
        assert "[Context not found:" in result

    def test_create_context_from_sources(self):
        """Test creating context from source materials."""
        architecture_docs = """
        # Overview
        This system uses JWT authentication with Redis session storage.

        # Patterns
        - Repository Pattern
        - Service Layer
        - Dependency Injection

        # Dependencies
        - redis
        - pyjwt
        - sqlalchemy
        """

        api_specs = """
        POST /api/auth/login
        GET /api/auth/profile
        DELETE /api/auth/logout
        """

        related_stories = [
            {
                "id": "story-123",
                "title": "Basic Authentication",
                "dev_notes": "Implementation uses bcrypt for password hashing",
            }
        ]

        context = self.compiler.create_context_from_sources(
            architecture_docs=architecture_docs,
            api_specs=api_specs,
            related_stories=related_stories,
        )

        assert "architecture" in context
        assert "api" in context
        assert "related" in context

        # Check parsed content
        assert "Repository Pattern" in context["architecture"]["patterns"]
        endpoints = context["api"]["endpoints"]
        assert any("POST" in str(endpoint) for endpoint in endpoints)
        assert len(context["related"]["stories"]) == 1
        assert context["related"]["stories"][0]["id"] == "story-123"

    def test_validate_dev_notes_valid(self):
        """Test validation of valid dev_notes."""
        dev_notes_json = self.compiler.compile_dev_notes(self.sample_contexts, "basic")

        validation_result = self.compiler.validate_dev_notes(dev_notes_json)

        assert validation_result["valid"] is True
        assert validation_result["score"] > 50
        assert "quality_level" in validation_result

    def test_validate_dev_notes_invalid_json(self):
        """Test validation of invalid JSON."""
        invalid_json = "{ invalid json structure"

        validation_result = self.compiler.validate_dev_notes(invalid_json)

        assert validation_result["valid"] is False
        assert validation_result["score"] == 0
        assert "Invalid JSON format" in validation_result["errors"]

    def test_validate_dev_notes_missing_sections(self):
        """Test validation with missing required sections."""
        minimal_notes = json.dumps({"some_section": "some_value"})

        validation_result = self.compiler.validate_dev_notes(minimal_notes)

        assert validation_result["valid"] is False
        assert validation_result["score"] < 100
        errors = validation_result["errors"]
        assert any("Missing required section" in error for error in errors)

    def test_validate_dev_notes_with_missing_context(self):
        """Test validation with missing context references."""
        notes_with_missing = {
            "architecture": {"overview": "[Context not found: $missing.ref]"},
            "implementation": {"files": ["file1.py"]},
            "testing_guidance": {"unit": "Some guidance"},
        }

        validation_result = self.compiler.validate_dev_notes(
            json.dumps(notes_with_missing)
        )

        assert validation_result["score"] < 100
        recommendations = validation_result["recommendations"]
        assert any("missing context" in rec.lower() for rec in recommendations)

    def test_text_extraction_methods(self):
        """Test text extraction helper methods."""
        sample_text = """
        # Overview
        This is the overview section.
        Some more overview content.

        # Patterns
        - Pattern 1
        - Pattern 2
        * Pattern 3

        # Dependencies
        1. Dependency 1
        2. Dependency 2
        """

        # Test section extraction
        overview = self.compiler._extract_section(sample_text, "overview")
        assert "This is the overview section" in overview

        # Test list extraction
        patterns = self.compiler._extract_list_section(sample_text, "patterns")
        assert "Pattern 1" in patterns
        assert "Pattern 2" in patterns
        assert "Pattern 3" in patterns

        dependencies = self.compiler._extract_list_section(sample_text, "dependencies")
        assert "Dependency 1" in dependencies
        assert "Dependency 2" in dependencies

    def test_endpoint_extraction(self):
        """Test API endpoint extraction."""
        api_spec = """
        GET /api/users Get all users
        POST /api/users Create new user
        PUT /api/users/{id} Update user
        DELETE /api/users/{id} Delete user
        """

        endpoints = self.compiler._extract_endpoints(api_spec)

        assert len(endpoints) == 4
        assert endpoints[0]["method"] == "GET"
        assert endpoints[0]["path"] == "/api/users"
        assert "Get all users" in endpoints[0]["description"]

    def test_related_stories_formatting(self):
        """Test formatting of related stories."""
        stories = [
            {
                "id": "story-1",
                "title": "Authentication Base",
                "dev_notes": "Long development notes "
                * 50,  # Make it long to test truncation
            },
            {
                "id": "story-2",
                "title": "User Management",
                "dev_notes": None,
            },
        ]

        formatted = self.compiler._format_related_stories(stories)

        assert len(formatted) == 2
        assert formatted[0]["id"] == "story-1"
        assert len(formatted[0]["dev_notes_excerpt"]) <= 203  # 200 + "..."
        assert formatted[1]["dev_notes_excerpt"] is None


class TestConvenienceFunctions:
    """Test the convenience functions."""

    def test_compile_basic_dev_notes(self):
        """Test the compile_basic_dev_notes convenience function."""
        contexts = {
            "architecture": {"overview": "Test overview"},
            "implementation": {"files": ["test.py"]},
        }

        result = compile_basic_dev_notes(contexts)

        assert isinstance(result, str)
        dev_notes = json.loads(result)
        assert "architecture" in dev_notes
        assert dev_notes["_metadata"]["template_used"] == "basic"

    def test_compile_api_dev_notes(self):
        """Test the compile_api_dev_notes convenience function."""
        contexts = {
            "architecture": {"overview": "API overview"},
            "api": {"endpoints": [{"method": "GET", "path": "/test"}]},
        }

        result = compile_api_dev_notes(contexts)

        assert isinstance(result, str)
        dev_notes = json.loads(result)
        assert "api_specification" in dev_notes
        assert dev_notes["_metadata"]["template_used"] == "api_development"

    def test_create_context_from_documents(self):
        """Test the create_context_from_documents convenience function."""
        architecture = "# Overview\nTest architecture"
        api = "GET /test"
        stories = [{"id": "test", "title": "Test Story"}]

        context = create_context_from_documents(
            architecture_content=architecture,
            api_content=api,
            related_stories=stories,
        )

        assert "architecture" in context
        assert "api" in context
        assert "related" in context
