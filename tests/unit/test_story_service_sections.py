"""
Unit tests for Story Service story section retrieval functionality.
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, mock_open
from src.agile_mcp.services.story_service import StoryService
from src.agile_mcp.services.exceptions import (
    StoryValidationError, 
    StoryNotFoundError, 
    SectionNotFoundError, 
    DatabaseError
)


@pytest.fixture
def mock_repository():
    """Create a mock Story repository."""
    return Mock()


@pytest.fixture
def story_service(mock_repository):
    """Create Story service with mock repository."""
    return StoryService(mock_repository)


@pytest.fixture
def sample_story_markdown():
    """Sample story markdown content for testing."""
    return '''# Story 1.1: Test Story

## Status
Done

## Story
**As a** test user, **I want** functionality, **so that** tests pass.

## Acceptance Criteria
1. First acceptance criterion
2. Second acceptance criterion

## Tasks / Subtasks
- [x] Task 1
  - [x] Subtask 1.1
'''


class TestStoryServiceSections:
    """Test cases for StoryService section retrieval functionality."""
    
    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_story_section_success(self, mock_file, mock_listdir, mock_exists, story_service, sample_story_markdown):
        """Test successful story section retrieval."""
        # Setup mocks
        mock_exists.return_value = True
        mock_listdir.return_value = ["1.1.test-story.md", "1.2.other-story.md"]
        mock_file.return_value.read.return_value = sample_story_markdown
        
        # Test service call
        result = story_service.get_story_section("1.1", "Acceptance Criteria")
        
        # Verify result
        assert "1. First acceptance criterion" in result
        assert "2. Second acceptance criterion" in result
        
        # Verify mocks were called correctly
        mock_exists.assert_called_once_with(os.path.join("docs", "stories"))
        mock_listdir.assert_called_once_with(os.path.join("docs", "stories"))
        mock_file.assert_called_once_with(os.path.join("docs", "stories", "1.1.test-story.md"), 'r', encoding='utf-8')
    
    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_story_section_case_insensitive(self, mock_file, mock_listdir, mock_exists, story_service, sample_story_markdown):
        """Test case-insensitive section matching."""
        # Setup mocks
        mock_exists.return_value = True
        mock_listdir.return_value = ["1.1.test-story.md"]
        mock_file.return_value.read.return_value = sample_story_markdown
        
        # Test with lowercase section name
        result = story_service.get_story_section("1.1", "acceptance criteria")
        
        # Verify result
        assert "1. First acceptance criterion" in result
        assert "2. Second acceptance criterion" in result
    
    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_story_section_with_alias(self, mock_file, mock_listdir, mock_exists, story_service, sample_story_markdown):
        """Test section retrieval using aliases."""
        # Setup mocks
        mock_exists.return_value = True
        mock_listdir.return_value = ["1.1.test-story.md"]
        mock_file.return_value.read.return_value = sample_story_markdown
        
        # Test with AC alias
        result = story_service.get_story_section("1.1", "ac")
        
        # Verify result
        assert "1. First acceptance criterion" in result
        assert "2. Second acceptance criterion" in result
    
    def test_get_story_section_empty_story_id(self, story_service):
        """Test error handling for empty story ID."""
        with pytest.raises(StoryValidationError) as exc_info:
            story_service.get_story_section("", "Status")
        
        assert "Story ID cannot be empty" in str(exc_info.value)
    
    def test_get_story_section_whitespace_story_id(self, story_service):
        """Test error handling for whitespace-only story ID."""
        with pytest.raises(StoryValidationError) as exc_info:
            story_service.get_story_section("   ", "Status")
        
        assert "Story ID cannot be empty" in str(exc_info.value)
    
    def test_get_story_section_empty_section_name(self, story_service):
        """Test error handling for empty section name."""
        with pytest.raises(StoryValidationError) as exc_info:
            story_service.get_story_section("1.1", "")
        
        assert "Section name cannot be empty" in str(exc_info.value)
    
    def test_get_story_section_whitespace_section_name(self, story_service):
        """Test error handling for whitespace-only section name."""
        with pytest.raises(StoryValidationError) as exc_info:
            story_service.get_story_section("1.1", "   ")
        
        assert "Section name cannot be empty" in str(exc_info.value)
    
    @patch('os.path.exists')
    def test_get_story_section_stories_directory_not_found(self, mock_exists, story_service):
        """Test error handling when stories directory doesn't exist."""
        mock_exists.return_value = False
        
        with pytest.raises(StoryNotFoundError) as exc_info:
            story_service.get_story_section("1.1", "Status")
        
        assert "Stories directory" in str(exc_info.value)
        assert "not found" in str(exc_info.value)
    
    @patch('os.path.exists')
    @patch('os.listdir')
    def test_get_story_section_story_file_not_found(self, mock_listdir, mock_exists, story_service):
        """Test error handling when story file is not found."""
        mock_exists.return_value = True
        mock_listdir.return_value = ["2.1.other-story.md", "3.1.another-story.md"]
        
        with pytest.raises(StoryNotFoundError) as exc_info:
            story_service.get_story_section("1.1", "Status")
        
        assert "Story file for ID '1.1' not found" in str(exc_info.value)
    
    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_story_section_empty_file(self, mock_file, mock_listdir, mock_exists, story_service):
        """Test error handling when story file is empty."""
        mock_exists.return_value = True
        mock_listdir.return_value = ["1.1.test-story.md"]
        mock_file.return_value.read.return_value = ""
        
        with pytest.raises(StoryNotFoundError) as exc_info:
            story_service.get_story_section("1.1", "Status")
        
        assert "is empty" in str(exc_info.value)
    
    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_story_section_section_not_found(self, mock_file, mock_listdir, mock_exists, story_service, sample_story_markdown):
        """Test error handling when section is not found."""
        mock_exists.return_value = True
        mock_listdir.return_value = ["1.1.test-story.md"]
        mock_file.return_value.read.return_value = sample_story_markdown
        
        with pytest.raises(SectionNotFoundError) as exc_info:
            story_service.get_story_section("1.1", "Nonexistent Section")
        
        assert "Section 'Nonexistent Section' not found" in str(exc_info.value)
    
    @patch('os.path.exists')
    @patch('os.listdir')
    def test_get_story_section_file_operation_error(self, mock_listdir, mock_exists, story_service):
        """Test error handling for file operation failures."""
        mock_exists.return_value = True
        mock_listdir.return_value = ["1.1.test-story.md"]
        
        # Mock open to raise an OSError
        with patch('builtins.open', side_effect=OSError("Permission denied")):
            with pytest.raises(DatabaseError) as exc_info:
                story_service.get_story_section("1.1", "Status")
            
            assert "File operation failed" in str(exc_info.value)
            assert "Permission denied" in str(exc_info.value)
    
    @patch('os.path.exists')
    @patch('os.listdir')
    def test_get_story_section_listdir_error(self, mock_listdir, mock_exists, story_service):
        """Test error handling for directory listing failures."""
        mock_exists.return_value = True
        mock_listdir.side_effect = OSError("Directory access denied")
        
        with pytest.raises(DatabaseError) as exc_info:
            story_service.get_story_section("1.1", "Status")
        
        assert "File operation failed" in str(exc_info.value)
        assert "Directory access denied" in str(exc_info.value)
    
    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_story_section_parser_validation_error(self, mock_file, mock_listdir, mock_exists, story_service):
        """Test handling of parser validation errors."""
        mock_exists.return_value = True
        mock_listdir.return_value = ["1.1.test-story.md"]
        mock_file.return_value.read.return_value = "valid content"
        
        # Mock the parser to raise a ValueError
        with patch.object(story_service.story_parser, 'extract_section', side_effect=ValueError("Parser error")):
            with pytest.raises(StoryValidationError) as exc_info:
                story_service.get_story_section("1.1", "Status")
            
            assert "Section parsing error" in str(exc_info.value)
            assert "Parser error" in str(exc_info.value)
    
    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_story_section_strips_whitespace_parameters(self, mock_file, mock_listdir, mock_exists, story_service, sample_story_markdown):
        """Test that parameters are properly stripped of whitespace."""
        mock_exists.return_value = True
        mock_listdir.return_value = ["1.1.test-story.md"]
        mock_file.return_value.read.return_value = sample_story_markdown
        
        # Test with whitespace around parameters
        result = story_service.get_story_section("  1.1  ", "  Status  ")
        
        # Should still work and find the section
        assert "Done" in result
        
        # Verify the correct file was opened (without whitespace)
        mock_file.assert_called_once_with(os.path.join("docs", "stories", "1.1.test-story.md"), 'r', encoding='utf-8')
    
    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_story_section_unexpected_error(self, mock_file, mock_listdir, mock_exists, story_service, sample_story_markdown):
        """Test handling of unexpected errors."""
        mock_exists.return_value = True
        mock_listdir.return_value = ["1.1.test-story.md"]
        mock_file.return_value.read.return_value = sample_story_markdown
        
        # Mock the parser to raise an unexpected exception
        with patch.object(story_service.story_parser, 'extract_section', side_effect=RuntimeError("Unexpected error")):
            with pytest.raises(DatabaseError) as exc_info:
                story_service.get_story_section("1.1", "Status")
            
            assert "Unexpected error while processing story section" in str(exc_info.value)
            assert "Unexpected error" in str(exc_info.value)