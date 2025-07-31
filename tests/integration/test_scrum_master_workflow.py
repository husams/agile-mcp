"""
Integration tests for the enhanced Scrum Master Agent workflow.

This module tests the complete end-to-end workflow of:
1. Document context retrieval and compilation
2. Story creation with rich dev_notes
3. Integration between document system and story creation
4. Backward compatibility with existing story creation
"""

import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.agile_mcp.models.epic import Base, Epic
from src.agile_mcp.models.story import Story
from src.agile_mcp.repositories.story_repository import StoryRepository
from src.agile_mcp.services.story_service import StoryService
from src.agile_mcp.utils.context_compiler import (
    ContextCompiler,
    compile_basic_dev_notes,
)
from src.agile_mcp.utils.document_integration import (
    DocumentContextBuilder,
    DocumentIntegrator,
    get_full_development_context,
)


@pytest.fixture
def integration_db():
    """Create an in-memory SQLite database for integration testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create a test epic for story relationships
    epic = Epic(
        id="scrum-master-epic-1",
        title="Scrum Master Workflow Epic",
        description="Epic for testing enhanced story creation workflow",
        status="In Progress",
    )
    session.add(epic)
    session.commit()

    yield session, epic
    session.close()


@pytest.fixture
def story_service(integration_db):
    """Create a story service with real database session."""
    session, epic = integration_db
    repository = StoryRepository(session)
    return StoryService(repository), session, epic


@pytest.fixture
def document_integrator():
    """Create a document integrator for testing."""
    return DocumentIntegrator()


@pytest.fixture
def context_compiler():
    """Create a context compiler for testing."""
    return ContextCompiler()


class TestScrumMasterWorkflowIntegration:
    """Integration tests for the complete Scrum Master workflow."""

    @pytest.mark.asyncio
    async def test_end_to_end_document_to_story_workflow(
        self, story_service, document_integrator, context_compiler
    ):
        """
        Test complete workflow: document retrieval -> context compilation ->
        story creation.
        """
        service, session, epic = story_service

        # Step 1: Retrieve context from documents
        document_context = await get_full_development_context(document_integrator)

        # Verify context was retrieved
        assert "architecture" in document_context
        assert "api" in document_context
        assert document_context["architecture"]["overview"] is not None

        # Step 2: Compile context into dev_notes
        dev_notes_json = compile_basic_dev_notes(document_context)
        dev_notes_data = json.loads(dev_notes_json)

        # Verify compilation quality
        assert "architecture" in dev_notes_data
        assert "implementation" in dev_notes_data
        assert "testing_guidance" in dev_notes_data
        assert "_metadata" in dev_notes_data

        # Step 3: Create story with compiled dev_notes
        story_result = service.create_story(
            title="Implement JWT Authentication System",
            description="As a user, I want secure JWT-based authentication",
            acceptance_criteria=[
                "User can login with email/password",
                "JWT token is generated and stored",
                "Token expires after configured time",
                "User can logout securely",
            ],
            epic_id=epic.id,
            dev_notes=dev_notes_json,
        )

        # Step 4: Verify story was created with full context
        assert story_result["title"] == "Implement JWT Authentication System"
        assert story_result["dev_notes"] is not None

        # Verify dev_notes contain rich context
        stored_dev_notes = json.loads(story_result["dev_notes"])
        assert (
            "microservices architecture"
            in stored_dev_notes["architecture"]["overview"].lower()
        )
        assert stored_dev_notes["_metadata"]["template_used"] == "basic"

        # Step 5: Verify story is stored in database
        stored_story = session.query(Story).filter_by(id=story_result["id"]).first()
        assert stored_story is not None
        assert stored_story.dev_notes == dev_notes_json
        assert stored_story.epic_id == epic.id

    @pytest.mark.asyncio
    async def test_multi_document_section_story_creation(
        self, story_service, document_integrator, context_compiler
    ):
        """Test story creation with context from multiple document sections."""
        service, session, epic = story_service

        # Create context builder for multiple sections
        builder = DocumentContextBuilder(document_integrator)

        # Add context from multiple documents and sections
        context = await (
            builder.add_architecture_context()  # architecture document
            .add_api_context()  # api-specs document
            .add_section(
                "coding-standards", "testing", "testing.standards"
            )  # coding standards
            .add_section(
                "coding-standards", "security", "constraints.security"
            )  # security constraints
            .build()
        )

        # Verify multi-document context
        assert "architecture" in context
        assert "api" in context
        assert "testing" in context
        assert "constraints" in context

        # Compile comprehensive dev_notes
        dev_notes_json = compile_basic_dev_notes(context)

        # Create story with comprehensive context
        story_result = service.create_story(
            title="Build API Endpoints with Security Standards",
            description=(
                "As a developer, I want secure API endpoints following " "standards"
            ),
            acceptance_criteria=[
                "API endpoints follow authentication patterns",
                "Security standards are implemented",
                "Testing standards are followed",
                "Architecture patterns are applied",
            ],
            epic_id=epic.id,
            dev_notes=dev_notes_json,
        )

        # Verify comprehensive context in story
        dev_notes_data = json.loads(story_result["dev_notes"])
        assert "architecture" in dev_notes_data
        assert "testing_guidance" in dev_notes_data
        assert dev_notes_data["_metadata"]["context_sources"] == [
            "architecture",
            "api",
            "testing",
            "constraints",
        ]

        # Verify quality of context
        validation_result = context_compiler.validate_dev_notes(dev_notes_json)
        assert validation_result["valid"] is True
        # Adequate quality due to comprehensive context
        assert validation_result["score"] >= 30

    def test_self_sufficient_story_context_verification(
        self, story_service, context_compiler
    ):
        """
        Test that created stories contain adequate development context for
        autonomy.
        """
        service, session, epic = story_service

        # Create a story with rich context
        rich_context = {
            "architecture": {
                "overview": "JWT authentication with Redis session storage",
                "patterns": ["Repository Pattern", "Service Layer", "Factory Pattern"],
                "dependencies": ["redis", "pyjwt", "sqlalchemy", "bcrypt"],
            },
            "implementation": {
                "files": [
                    "src/auth/auth_service.py",
                    "src/auth/token_manager.py",
                    "src/models/user.py",
                    "src/repositories/user_repository.py",
                ],
                "methods": [
                    "authenticate_user(email, password)",
                    "generate_jwt_token(user_id)",
                    "validate_token(token)",
                    "refresh_token(refresh_token)",
                ],
                "entry_points": [
                    "POST /api/auth/login",
                    "POST /api/auth/refresh",
                    "POST /api/auth/logout",
                ],
            },
            "constraints": {
                "technical": [
                    "Token expiry: 24 hours for access, 7 days for refresh",
                    "Password hashing: bcrypt with 12 rounds",
                    "Session cleanup: Every 4 hours",
                ],
                "business": [
                    "Password must contain: uppercase, lowercase, number, special char",
                    "Account lockout after 5 failed attempts",
                    "Password reset token expires in 1 hour",
                ],
            },
            "testing": {
                "unit": "Test all auth service methods with mocked dependencies",
                "integration": "Test full auth flow with real Redis and database",
                "e2e": "Test complete user authentication journey",
            },
        }

        dev_notes_json = compile_basic_dev_notes(rich_context)

        # Create story with rich context
        story_result = service.create_story(
            title="Complete Authentication System Implementation",
            description="As a system, I need comprehensive JWT authentication",
            acceptance_criteria=[
                "User registration and login",
                "Token generation and validation",
                "Session management with Redis",
                "Security constraints enforced",
                "Comprehensive test coverage",
            ],
            epic_id=epic.id,
            dev_notes=dev_notes_json,
        )

        # Validate story self-sufficiency
        validation_result = context_compiler.validate_dev_notes(
            story_result["dev_notes"]
        )

        # Story should be high quality and self-sufficient
        assert validation_result["valid"] is True
        assert validation_result["score"] >= 70  # High score for comprehensive context
        assert validation_result["quality_level"] in ["Good", "Excellent"]
        assert len(validation_result["recommendations"]) <= 2  # Minimal recommendations

        # Verify actionable information is present
        dev_notes_data = json.loads(story_result["dev_notes"])
        assert len(dev_notes_data["implementation"]["files_to_modify"]) >= 4
        assert len(dev_notes_data["implementation"]["key_methods"]) >= 4
        assert len(dev_notes_data["technical_constraints"]) >= 3

    def test_backward_compatibility_standard_story_creation(self, story_service):
        """Test that standard story creation (without dev_notes) still works."""
        service, session, epic = story_service

        # Create story without dev_notes (traditional way)
        story_result = service.create_story(
            title="Simple Story Without Dev Notes",
            description="As a user, I want basic functionality",
            acceptance_criteria=["Basic functionality works"],
            epic_id=epic.id,
            # No dev_notes parameter
        )

        # Verify story was created successfully
        assert story_result["title"] == "Simple Story Without Dev Notes"
        assert story_result["dev_notes"] is None
        assert story_result["epic_id"] == epic.id

        # Verify story is stored in database correctly
        stored_story = session.query(Story).filter_by(id=story_result["id"]).first()
        assert stored_story is not None
        assert stored_story.dev_notes is None
        assert stored_story.title == "Simple Story Without Dev Notes"

    def test_backward_compatibility_with_existing_stories(self, story_service):
        """Test that existing stories without dev_notes are handled correctly."""
        service, session, epic = story_service

        # Create a story in the old format (directly in database)
        legacy_story = Story(
            id="legacy-story-123",
            title="Legacy Story",
            description="Story created before dev_notes feature",
            acceptance_criteria=["Legacy functionality"],
            epic_id=epic.id,
            status="ToDo",
            # dev_notes is None by default
        )
        session.add(legacy_story)
        session.commit()

        # Retrieve the legacy story
        retrieved_story = service.get_story("legacy-story-123")

        # Verify legacy story works correctly
        assert retrieved_story["title"] == "Legacy Story"
        assert retrieved_story["dev_notes"] is None
        assert "dev_notes" in retrieved_story  # Field should be present but None

        # Update legacy story with dev_notes
        rich_dev_notes = json.dumps(
            {
                "architecture": {"overview": "Added context to legacy story"},
                "implementation": {"files": ["legacy_file.py"]},
            }
        )

        updated_story = service.update_story(
            story_id="legacy-story-123",
            dev_notes=rich_dev_notes,
        )

        # Verify legacy story can be enhanced with dev_notes
        assert updated_story["dev_notes"] == rich_dev_notes
        assert (
            json.loads(updated_story["dev_notes"])["architecture"]["overview"]
            == "Added context to legacy story"
        )

    @pytest.mark.asyncio
    async def test_document_integration_error_handling(
        self, story_service, document_integrator, context_compiler
    ):
        """Test workflow handles document integration errors gracefully."""
        service, session, epic = story_service

        # Test with missing document sections (should use placeholders)
        builder = DocumentContextBuilder(document_integrator)
        context = await (
            builder.add_section("nonexistent-doc", "missing-section", "missing.context")
            .add_architecture_context()  # This should work
            .build()
        )

        # Should have some context even with missing sections
        assert "architecture" in context
        # The missing section may not create a top-level key, but should be
        # handled gracefully

        # Compile dev_notes with partial context
        dev_notes_json = compile_basic_dev_notes(context)

        # Create story even with partial context
        story_result = service.create_story(
            title="Story with Partial Context",
            description="Story created despite missing document sections",
            acceptance_criteria=["Should handle missing context gracefully"],
            epic_id=epic.id,
            dev_notes=dev_notes_json,
        )

        # Verify story was created
        assert story_result["dev_notes"] is not None

        # Validate that missing context is indicated
        dev_notes_str = story_result["dev_notes"]
        assert "[Context not found:" in dev_notes_str

        # Story should still be valid despite missing context
        validation_result = context_compiler.validate_dev_notes(dev_notes_json)
        assert (
            validation_result["valid"] is True
        )  # Should be valid despite missing context
        assert (
            len(validation_result["recommendations"]) > 0
        )  # Should have recommendations

    def test_story_creation_with_invalid_dev_notes(self, story_service):
        """Test error handling for invalid dev_notes."""
        service, session, epic = story_service

        # Test with non-string dev_notes (this should fail)
        from src.agile_mcp.services.exceptions import StoryValidationError

        with pytest.raises(StoryValidationError, match="Dev notes must be a string"):
            service.create_story(
                title="Story with Non-String Dev Notes",
                description="This should fail",
                acceptance_criteria=["Should fail validation"],
                epic_id=epic.id,
                dev_notes={"invalid": "not a string"},
            )

        # Test with very long dev_notes (should fail)
        very_long_dev_notes = "x" * 10001  # Exceeds 10000 char limit
        with pytest.raises(
            StoryValidationError, match="Dev notes cannot exceed 10000 characters"
        ):
            service.create_story(
                title="Story with Long Dev Notes",
                description="This should also fail",
                acceptance_criteria=["Should fail validation"],
                epic_id=epic.id,
                dev_notes=very_long_dev_notes,
            )

    @pytest.mark.asyncio
    async def test_performance_with_large_context(
        self, story_service, document_integrator, context_compiler
    ):
        """Test workflow performance with large document context."""
        service, session, epic = story_service

        # Create large but manageable context (under 10000 char limit)
        large_context = {
            "architecture": {
                "overview": "Comprehensive microservices architecture using "
                "JWT authentication with Redis session storage",
                "patterns": [
                    "Pattern " + str(i) for i in range(10)
                ],  # Reasonable number
                "dependencies": [
                    "dep" + str(i) for i in range(20)
                ],  # Reasonable number
            },
            "implementation": {
                "files": [
                    "file" + str(i) + ".py" for i in range(15)
                ],  # Reasonable number
                "methods": [
                    "method" + str(i) + "()" for i in range(10)
                ],  # Reasonable number
                "entry_points": [
                    "/api/endpoint" + str(i) for i in range(8)
                ],  # Reasonable number
            },
            "testing": {
                "unit": "Comprehensive unit testing strategy with mocks and fixtures",
                "integration": "Detailed integration testing approach with database",
                "e2e": "End-to-end testing methodology with real user flows",
            },
        }

        # Compile large context (should handle efficiently)
        dev_notes_json = compile_basic_dev_notes(large_context)

        # Verify compilation succeeded
        assert dev_notes_json is not None
        dev_notes_data = json.loads(dev_notes_json)
        assert (
            "microservices architecture" in dev_notes_data["architecture"]["overview"]
        )
        assert len(dev_notes_json) < 10000  # Should be under the limit

        # Create story with large context (should complete in reasonable time)
        story_result = service.create_story(
            title="Story with Large Context",
            description="Testing performance with comprehensive context",
            acceptance_criteria=["Should handle large context efficiently"],
            epic_id=epic.id,
            dev_notes=dev_notes_json,
        )

        # Verify story was created successfully
        assert story_result["dev_notes"] is not None
        assert (
            len(story_result["dev_notes"]) > 1000
        )  # Should be substantial but under limit

        # Validate large dev_notes
        validation_result = context_compiler.validate_dev_notes(dev_notes_json)
        assert validation_result["valid"] is True
        assert (
            validation_result["score"] >= 65
        )  # Should score well due to comprehensive content

    @pytest.mark.asyncio
    async def test_context_template_selection_workflow(
        self, story_service, document_integrator, context_compiler
    ):
        """Test workflow with different context templates for different story types."""
        service, session, epic = story_service

        # Test API development template
        api_context = await get_full_development_context(document_integrator)
        api_context["api"] = {
            "endpoints": [{"method": "POST", "path": "/api/auth/login"}],
            "authentication": "JWT Bearer",
        }

        api_dev_notes = context_compiler.compile_dev_notes(
            api_context, "api_development"
        )

        api_story = service.create_story(
            title="API Development Story",
            description="Story focused on API development",
            acceptance_criteria=["API endpoints implemented"],
            epic_id=epic.id,
            dev_notes=api_dev_notes,
        )

        # Verify API template was used
        api_data = json.loads(api_story["dev_notes"])
        template_used = api_data["_metadata"]["template_used"]
        assert template_used == "api_development"
        assert "api_specification" in api_data

        # Test data model template
        model_context = {
            "database": {"tables": ["users", "sessions"]},
            "implementation": {"models": ["User", "Session"]},
        }

        model_dev_notes = context_compiler.compile_dev_notes(
            model_context, "data_model"
        )

        model_story = service.create_story(
            title="Data Model Story",
            description="Story focused on data modeling",
            acceptance_criteria=["Data models implemented"],
            epic_id=epic.id,
            dev_notes=model_dev_notes,
        )

        # Verify data model template was used
        model_data = json.loads(model_story["dev_notes"])
        assert model_data["_metadata"]["template_used"] == "data_model"
        assert "database_design" in model_data
