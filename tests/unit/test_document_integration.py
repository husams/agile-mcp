"""
Unit tests for the DocumentIntegrator utility.
"""

from unittest.mock import AsyncMock

import pytest

from src.agile_mcp.utils.document_integration import (
    DocumentContextBuilder,
    DocumentIntegrationError,
    DocumentIntegrator,
    get_api_context,
    get_architecture_context,
    get_full_development_context,
)


class TestDocumentIntegrator:
    """Test cases for the DocumentIntegrator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.integrator = DocumentIntegrator()

    @pytest.mark.asyncio
    async def test_get_section_content_with_mock_data(self):
        """Test getting section content using mock data."""
        content = await self.integrator.get_section_content(
            document_id="architecture",
            section_name="overview",
        )

        assert content is not None
        assert "microservices architecture" in content.lower()
        assert "jwt authentication" in content.lower()

    @pytest.mark.asyncio
    async def test_get_section_content_not_found(self):
        """Test getting section content that doesn't exist."""
        content = await self.integrator.get_section_content(
            document_id="nonexistent",
            section_name="missing",
        )

        assert content is None

    @pytest.mark.asyncio
    async def test_get_section_content_with_client(self):
        """Test getting section content with a mock client."""
        mock_client = AsyncMock()
        mock_client.get_section.return_value = {"content": "Test section content"}

        integrator = DocumentIntegrator(document_client=mock_client)

        content = await integrator.get_section_content(
            document_id="test-doc",
            section_name="test-section",
            project_id="project-123",
        )

        assert content == "Test section content"
        mock_client.get_section.assert_called_once_with(
            document_id="test-doc",
            section_name="test-section",
            project_id="project-123",
        )

    @pytest.mark.asyncio
    async def test_get_section_content_client_error(self):
        """Test handling client errors."""
        mock_client = AsyncMock()
        mock_client.get_section.side_effect = Exception("Client error")

        integrator = DocumentIntegrator(document_client=mock_client)

        with pytest.raises(
            DocumentIntegrationError, match="Failed to retrieve section"
        ):
            await integrator.get_section_content(
                document_id="test-doc",
                section_name="test-section",
            )

    @pytest.mark.asyncio
    async def test_get_multiple_sections(self):
        """Test getting multiple sections."""
        sections = [
            {"document_id": "architecture", "section_name": "overview"},
            {"document_id": "architecture", "section_name": "patterns"},
            {"document_id": "api-specs", "section_name": "authentication"},
        ]

        results = await self.integrator.get_multiple_sections(sections)

        assert len(results) == 3
        assert "architecture.overview" in results
        assert "architecture.patterns" in results
        assert "api-specs.authentication" in results

        # Check content quality
        overview_content = results["architecture.overview"].lower()
        patterns_content = results["architecture.patterns"].lower()
        auth_content = results["api-specs.authentication"].lower()
        assert "microservices" in overview_content
        assert "repository pattern" in patterns_content
        assert "authentication endpoints" in auth_content

    @pytest.mark.asyncio
    async def test_get_multiple_sections_with_errors(self):
        """Test getting multiple sections with some errors."""
        mock_client = AsyncMock()
        # First call succeeds, second call fails
        mock_client.get_section.side_effect = [
            {"content": "Success content"},
            Exception("Client error"),
        ]

        integrator = DocumentIntegrator(document_client=mock_client)

        sections = [
            {"document_id": "test-doc", "section_name": "good-section"},
            {"document_id": "test-doc", "section_name": "bad-section"},
        ]

        results = await integrator.get_multiple_sections(sections)

        assert len(results) == 2
        assert results["test-doc.good-section"] == "Success content"
        assert "[Error retrieving section:" in results["test-doc.bad-section"]

    def test_create_context_from_document_sections(self):
        """Test creating context from section contents."""
        section_contents = {
            "architecture.overview": "System overview content",
            "architecture.patterns": "Design patterns content",
            "api.authentication": "API auth content",
        }

        context_mapping = {
            "architecture.overview": "architecture.overview",
            "architecture.patterns": "architecture.patterns",
            "api.authentication": "api.auth_endpoints",
        }

        context = self.integrator.create_context_from_document_sections(
            section_contents=section_contents,
            context_mapping=context_mapping,
        )

        assert "architecture" in context
        assert "api" in context
        assert context["architecture"]["overview"] == "System overview content"
        assert context["architecture"]["patterns"] == "Design patterns content"
        assert context["api"]["auth_endpoints"] == "API auth content"

    def test_create_context_with_default_mapping(self):
        """Test creating context with default mapping."""
        section_contents = {
            "architecture.overview": "System overview",
            "api-specs.authentication": "Auth endpoints",
        }

        context = self.integrator.create_context_from_document_sections(
            section_contents=section_contents
        )

        assert "architecture" in context
        assert "api" in context
        assert context["architecture"]["overview"] == "System overview"
        assert context["api"]["auth_endpoints"] == "Auth endpoints"

    @pytest.mark.asyncio
    async def test_validate_document_access(self):
        """Test validating document access."""
        document_ids = ["architecture", "api-specs", "nonexistent"]

        results = await self.integrator.validate_document_access(document_ids)

        assert len(results) == 3
        assert results["architecture"] is True
        # This might fail due to no "overview" section
        assert results["api-specs"] is True
        assert results["nonexistent"] is False

    def test_create_section_request_batch(self):
        """Test creating section request batch."""
        document_sections = {
            "architecture": ["overview", "patterns"],
            "api-specs": ["authentication"],
        }

        requests = self.integrator.create_section_request_batch(document_sections)

        assert len(requests) == 3

        # Check that all expected combinations are present
        expected = [
            {"document_id": "architecture", "section_name": "overview"},
            {"document_id": "architecture", "section_name": "patterns"},
            {"document_id": "api-specs", "section_name": "authentication"},
        ]

        for expected_request in expected:
            assert expected_request in requests


class TestDocumentContextBuilder:
    """Test cases for the DocumentContextBuilder class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.integrator = DocumentIntegrator()
        self.builder = DocumentContextBuilder(self.integrator)

    def test_add_section(self):
        """Test adding a section to the builder."""
        builder = self.builder.add_section(
            document_id="test-doc",
            section_name="test-section",
            context_path="test.path",
        )

        # Should return self for chaining
        assert builder is self.builder

        # Check internal state
        assert len(self.builder.section_requests) == 1
        assert self.builder.section_requests[0] == {
            "document_id": "test-doc",
            "section_name": "test-section",
        }
        assert self.builder.context_mapping["test-doc.test-section"] == "test.path"

    def test_add_architecture_context(self):
        """Test adding architecture context."""
        self.builder.add_architecture_context()

        # Should have added multiple architecture sections
        assert len(self.builder.section_requests) >= 4

        # Check specific sections
        section_docs = [req["document_id"] for req in self.builder.section_requests]
        section_names = [req["section_name"] for req in self.builder.section_requests]

        assert "architecture" in section_docs
        assert "overview" in section_names
        assert "patterns" in section_names

    def test_add_api_context(self):
        """Test adding API context."""
        self.builder.add_api_context()

        # Should have added API sections
        assert len(self.builder.section_requests) >= 2

        # Check specific sections
        section_docs = [req["document_id"] for req in self.builder.section_requests]
        section_names = [req["section_name"] for req in self.builder.section_requests]

        assert "api-specs" in section_docs
        assert "authentication" in section_names

    def test_add_custom_sections(self):
        """Test adding custom sections for architecture and API."""
        self.builder.add_architecture_context(
            document_id="custom-arch",
            sections=["overview", "database"],
        )

        self.builder.add_api_context(
            document_id="custom-api",
            sections=["authentication"],
        )

        # Check that custom document IDs are used
        section_docs = [req["document_id"] for req in self.builder.section_requests]
        assert "custom-arch" in section_docs
        assert "custom-api" in section_docs

    @pytest.mark.asyncio
    async def test_build_context(self):
        """Test building the context."""
        self.builder.add_architecture_context()

        context = await self.builder.build()

        assert "architecture" in context
        assert "overview" in context.get("architecture", {})
        assert "patterns" in context.get("architecture", {})

    @pytest.mark.asyncio
    async def test_build_empty_context(self):
        """Test building context with no sections."""
        context = await self.builder.build()

        assert context == {}

    def test_method_chaining(self):
        """Test that methods can be chained."""
        result = (
            self.builder.add_architecture_context()
            .add_api_context()
            .add_section("custom", "section", "custom.path")
        )

        # Should return the same builder instance
        assert result is self.builder

        # Should have added all sections
        assert len(self.builder.section_requests) >= 7


class TestConvenienceFunctions:
    """Test the convenience functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.integrator = DocumentIntegrator()

    @pytest.mark.asyncio
    async def test_get_architecture_context(self):
        """Test the get_architecture_context convenience function."""
        context = await get_architecture_context(self.integrator)

        assert "architecture" in context
        assert context["architecture"].get("overview") is not None

    @pytest.mark.asyncio
    async def test_get_api_context(self):
        """Test the get_api_context convenience function."""
        context = await get_api_context(self.integrator)

        assert "api" in context
        assert context["api"].get("auth_endpoints") is not None

    @pytest.mark.asyncio
    async def test_get_full_development_context(self):
        """Test the get_full_development_context convenience function."""
        context = await get_full_development_context(self.integrator)

        assert "architecture" in context
        assert "api" in context
        assert "testing" in context
        assert "constraints" in context

        # Check that it includes comprehensive context
        assert context["architecture"].get("overview") is not None
        assert context["api"].get("auth_endpoints") is not None
        assert context["testing"].get("standards") is not None
        assert context["constraints"].get("security") is not None
