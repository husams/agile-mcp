"""
Unit tests for StoryParser utility class.
"""

import pytest

from src.agile_mcp.services.exceptions import SectionNotFoundError
from src.agile_mcp.utils.story_parser import StoryParser


@pytest.fixture
def sample_story_content():
    """Create sample story markdown content for testing."""
    return """# Story 1.1: Sample Story

## Status
Draft

## Story
**As a** user, **I want** to test, **so that** it works.

## Acceptance Criteria
1. First criterion
2. Second criterion

## Tasks / Subtasks
- [ ] Task 1
  - [ ] Subtask 1.1

## Dev Notes
These are development notes.

## Testing
This is the testing section.
"""


@pytest.fixture
def story_parser():
    """Create a StoryParser instance."""
    return StoryParser()


class TestStoryParser:
    """Test cases for StoryParser class."""

    def test_extract_section_success(self, story_parser, sample_story_content):
        """Test successful section extraction."""
        result = story_parser.extract_section(
            sample_story_content, "Acceptance Criteria"
        )
        assert "1. First criterion" in result
        assert "2. Second criterion" in result
        assert result.strip().endswith("2. Second criterion")

    def test_extract_section_case_insensitive(self, story_parser, sample_story_content):
        """Test case-insensitive section matching."""
        result = story_parser.extract_section(
            sample_story_content, "acceptance criteria"
        )
        assert "1. First criterion" in result
        assert "2. Second criterion" in result

    def test_extract_section_with_alias(self, story_parser, sample_story_content):
        """Test section extraction using aliases."""
        # Test AC alias for Acceptance Criteria
        result = story_parser.extract_section(sample_story_content, "ac")
        assert "1. First criterion" in result
        assert "2. Second criterion" in result

        # Test description alias for Story
        result = story_parser.extract_section(sample_story_content, "description")
        assert "**As a** user" in result

        # Test tasks alias for Tasks / Subtasks
        result = story_parser.extract_section(sample_story_content, "tasks")
        assert "- [ ] Task 1" in result

    def test_extract_section_not_found(self, story_parser, sample_story_content):
        """Test section not found error."""
        with pytest.raises(SectionNotFoundError) as exc_info:
            story_parser.extract_section(sample_story_content, "Nonexistent Section")

        assert "Section 'Nonexistent Section' not found" in str(exc_info.value)
        assert "Available sections:" in str(exc_info.value)

    def test_extract_section_empty_content(self, story_parser):
        """Test extraction with empty content."""
        with pytest.raises(ValueError) as exc_info:
            story_parser.extract_section("", "Status")

        assert "Content cannot be empty" in str(exc_info.value)

    def test_extract_section_empty_section_name(
        self, story_parser, sample_story_content
    ):
        """Test extraction with empty section name."""
        with pytest.raises(ValueError) as exc_info:
            story_parser.extract_section(sample_story_content, "")

        assert "Invalid section name" in str(exc_info.value)

    def test_extract_section_whitespace_section_name(
        self, story_parser, sample_story_content
    ):
        """Test extraction with whitespace-only section name."""
        with pytest.raises(ValueError) as exc_info:
            story_parser.extract_section(sample_story_content, "   ")

        assert "Invalid section name" in str(exc_info.value)

    def test_extract_section_with_empty_section_content(self, story_parser):
        """Test extraction of section with empty content."""
        content = """# Story 1.1: Sample Story

## Status

## Story
Content here
"""
        result = story_parser.extract_section(content, "Status")
        assert result == ""

    def test_normalize_section_name_valid(self, story_parser):
        """Test section name normalization with valid names."""
        assert story_parser.normalize_section_name("Status") == "Status"
        assert story_parser.normalize_section_name("  Status  ") == "Status"
        assert (
            story_parser.normalize_section_name("acceptance criteria")
            == "Acceptance Criteria"
        )
        assert story_parser.normalize_section_name("AC") == "Acceptance Criteria"

    def test_normalize_section_name_empty(self, story_parser):
        """Test section name normalization with empty name."""
        with pytest.raises(ValueError) as exc_info:
            story_parser.normalize_section_name("")

        assert "Section name cannot be empty" in str(exc_info.value)

    def test_normalize_section_name_whitespace(self, story_parser):
        """Test section name normalization with whitespace-only name."""
        with pytest.raises(ValueError) as exc_info:
            story_parser.normalize_section_name("   ")

        assert "Section name cannot be empty" in str(exc_info.value)

    def test_list_sections(self, story_parser, sample_story_content):
        """Test listing all available sections."""
        sections = story_parser.list_sections(sample_story_content)
        expected_sections = [
            "Status",
            "Story",
            "Acceptance Criteria",
            "Tasks / Subtasks",
            "Dev Notes",
            "Testing",
        ]
        assert sections == expected_sections

    def test_list_sections_empty_content(self, story_parser):
        """Test listing sections with empty content."""
        sections = story_parser.list_sections("")
        assert sections == []

    def test_extract_section_multiple_same_headers(self, story_parser):
        """Test extraction when multiple sections have similar headers."""
        content = """# Story 1.1: Sample Story

## Status
First status

## Status Notes
Status notes content

## Story
Story content
"""
        # Should extract the first Status section
        result = story_parser.extract_section(content, "Status")
        assert result == "First status"

        # Should extract the Status Notes section
        result = story_parser.extract_section(content, "Status Notes")
        assert result == "Status notes content"

    def test_extract_section_preserves_formatting(self, story_parser):
        """Test that section extraction preserves original formatting."""
        content = """# Story 1.1: Sample Story

## Tasks / Subtasks
- [ ] Task 1
  - [ ] Subtask 1.1
    - Additional details
  - [ ] Subtask 1.2
- [ ] Task 2

## Story
Next section
"""
        result = story_parser.extract_section(content, "Tasks / Subtasks")
        expected = """- [ ] Task 1
  - [ ] Subtask 1.1
    - Additional details
  - [ ] Subtask 1.2
- [ ] Task 2"""
        assert result == expected

    def test_find_sections_internal_method(self, story_parser, sample_story_content):
        """Test the internal _find_sections method."""
        lines = sample_story_content.split("\n")
        sections = story_parser._find_sections(lines)

        section_names = [name for name, _ in sections]
        expected_names = [
            "Status",
            "Story",
            "Acceptance Criteria",
            "Tasks / Subtasks",
            "Dev Notes",
            "Testing",
        ]
        assert section_names == expected_names

        # Check that line numbers are reasonable
        for name, line_num in sections:
            assert line_num >= 0
            assert line_num < len(lines)
            assert lines[line_num].startswith("## ")
