"""Unit tests for MarkdownParser utility."""

from src.agile_mcp.utils.markdown_parser import MarkdownParser, MarkdownSection


class TestMarkdownSection:
    """Test cases for MarkdownSection class."""

    def test_markdown_section_creation(self):
        """Test creating a MarkdownSection instance."""
        section = MarkdownSection(
            title="Introduction",
            content="This is the introduction content.",
            level=1,
            order=0,
        )

        assert section.title == "Introduction"
        assert section.content == "This is the introduction content."
        assert section.level == 1
        assert section.order == 0

    def test_markdown_section_repr(self):
        """Test MarkdownSection string representation."""
        section = MarkdownSection(
            title="Introduction",
            content="Content",
            level=1,
            order=0,
        )

        repr_str = repr(section)
        assert "MarkdownSection" in repr_str
        assert "Introduction" in repr_str
        assert "level=1" in repr_str
        assert "order=0" in repr_str


class TestMarkdownParser:
    """Test cases for MarkdownParser class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = MarkdownParser()

    def test_parse_empty_content(self):
        """Test parsing empty content."""
        assert self.parser.parse("") == []
        assert self.parser.parse("   ") == []
        assert self.parser.parse(None) == []

    def test_parse_content_without_headings(self):
        """Test parsing content without any headings."""
        content = "This is some content without headings.\n\nIt has multiple lines."
        sections = self.parser.parse(content)

        assert len(sections) == 1
        assert sections[0].title == "Document Content"
        assert sections[0].content == content.strip()
        assert sections[0].level == 1
        assert sections[0].order == 0

    def test_parse_single_heading(self):
        """Test parsing content with a single heading."""
        content = "# Introduction\n\nThis is the introduction content."
        sections = self.parser.parse(content)

        assert len(sections) == 1
        assert sections[0].title == "Introduction"
        assert sections[0].content == "This is the introduction content."
        assert sections[0].level == 1
        assert sections[0].order == 0

    def test_parse_multiple_headings_same_level(self):
        """Test parsing content with multiple headings at the same level."""
        content = """# Introduction

This is the introduction.

# Methodology

This is the methodology.

# Conclusion

This is the conclusion."""

        sections = self.parser.parse(content)

        assert len(sections) == 3

        assert sections[0].title == "Introduction"
        assert sections[0].content == "This is the introduction."
        assert sections[0].level == 1
        assert sections[0].order == 0

        assert sections[1].title == "Methodology"
        assert sections[1].content == "This is the methodology."
        assert sections[1].level == 1
        assert sections[1].order == 1

        assert sections[2].title == "Conclusion"
        assert sections[2].content == "This is the conclusion."
        assert sections[2].level == 1
        assert sections[2].order == 2

    def test_parse_nested_headings(self):
        """Test parsing content with nested headings."""
        content = """# Introduction

This is the introduction.

## Background

This is background information.

## Objectives

These are the objectives.

# Methodology

This is the methodology.

## Data Collection

This is about data collection.

# Conclusion

This is the conclusion."""

        sections = self.parser.parse(content)

        assert len(sections) == 6

        # Check main sections
        assert sections[0].title == "Introduction"
        assert sections[0].level == 1
        assert sections[0].order == 0

        assert sections[1].title == "Background"
        assert sections[1].level == 2
        assert sections[1].order == 1

        assert sections[2].title == "Objectives"
        assert sections[2].level == 2
        assert sections[2].order == 2

        assert sections[3].title == "Methodology"
        assert sections[3].level == 1
        assert sections[3].order == 3

        assert sections[4].title == "Data Collection"
        assert sections[4].level == 2
        assert sections[4].order == 4

        assert sections[5].title == "Conclusion"
        assert sections[5].level == 1
        assert sections[5].order == 5

    def test_parse_different_heading_formats(self):
        """Test parsing different heading formats."""
        content = """# H1 Heading

Content for H1.

## H2 Heading

Content for H2.

### H3 Heading

Content for H3.

#### H4 Heading

Content for H4.

##### H5 Heading

Content for H5.

###### H6 Heading

Content for H6."""

        sections = self.parser.parse(content)

        assert len(sections) == 6

        for i, (expected_level, expected_title) in enumerate(
            [
                (1, "H1 Heading"),
                (2, "H2 Heading"),
                (3, "H3 Heading"),
                (4, "H4 Heading"),
                (5, "H5 Heading"),
                (6, "H6 Heading"),
            ]
        ):
            assert sections[i].level == expected_level
            assert sections[i].title == expected_title
            assert sections[i].order == i

    def test_parse_heading_with_extra_whitespace(self):
        """Test parsing headings with extra whitespace."""
        content = """#    Heading with spaces

Content here.

##   Another heading

More content."""

        sections = self.parser.parse(content)

        assert len(sections) == 2
        assert sections[0].title == "Heading with spaces"
        assert sections[1].title == "Another heading"

    def test_parse_content_with_code_blocks(self):
        """Test parsing content that includes code blocks."""
        content = """# Code Example

Here's some code:

```python
def hello():
    print("Hello, world!")
```

## Another Section

More content here."""

        sections = self.parser.parse(content)

        assert len(sections) == 2
        assert "```python" in sections[0].content
        assert "def hello():" in sections[0].content
        assert sections[1].title == "Another Section"

    def test_parse_removes_trailing_empty_lines(self):
        """Test that parsing removes trailing empty lines from sections."""
        content = """# Section 1

Content with trailing lines.


# Section 2

More content.


"""

        sections = self.parser.parse(content)

        assert len(sections) == 2
        assert sections[0].content == "Content with trailing lines."
        assert sections[1].content == "More content."

    def test_extract_metadata_with_h1_title(self):
        """Test extracting title and description from content with H1."""
        content = """# My Document Title

This is the description of the document.
It spans multiple lines.

## Section 1

Content here."""

        title, description = self.parser.extract_metadata(content)

        assert title == "My Document Title"
        assert "This is the description" in description
        assert "It spans multiple lines." in description

    def test_extract_metadata_without_h1(self):
        """Test extracting metadata from content without H1."""
        content = """This is the first line that becomes the title.
This is the second line.
This is the third line.

## Section 1

Content here."""

        title, description = self.parser.extract_metadata(content)

        assert title == "This is the first line that becomes the title."
        assert "This is the second line." in description

    def test_extract_metadata_empty_content(self):
        """Test extracting metadata from empty content."""
        title, description = self.parser.extract_metadata("")

        assert title == "Untitled Document"
        assert description == ""

    def test_extract_metadata_long_description(self):
        """Test extracting metadata with long description gets truncated."""
        long_description = "x" * 600
        content = f"# Title\n\n{long_description}"

        title, description = self.parser.extract_metadata(content)

        assert title == "Title"
        assert len(description) <= 503  # 500 + "..."
        assert description.endswith("...")

    def test_extract_metadata_long_title(self):
        """Test extracting metadata with long title gets truncated."""
        long_title = "x" * 150
        content = f"# {long_title}\n\nDescription here."

        title, description = self.parser.extract_metadata(content)

        assert len(title) == 100  # Limited in extract_metadata method
        assert title == long_title[:100]

    def test_validate_content_valid(self):
        """Test content validation with valid content."""
        assert self.parser.validate_content("# Valid markdown content") is True
        assert self.parser.validate_content("Regular text content") is True

    def test_validate_content_invalid(self):
        """Test content validation with invalid content."""
        assert self.parser.validate_content("") is False
        assert self.parser.validate_content("   ") is False
        assert self.parser.validate_content(None) is False
        assert self.parser.validate_content(123) is False

    def test_validate_content_too_large(self):
        """Test content validation with content that's too large."""
        large_content = "x" * (10_000_001)  # Exceed 10MB limit
        assert self.parser.validate_content(large_content) is False

    def test_parse_complex_document(self):
        """Test parsing a complex document with various markdown elements."""
        content = """# Main Title

Introduction paragraph.

## Section A

### Subsection A.1

Content with **bold** and *italic* text.

- List item 1
- List item 2

### Subsection A.2

More content.

## Section B

Final section content.

```
Code block here
```

End of document."""

        sections = self.parser.parse(content)

        # Verify we get all expected sections
        expected_titles = [
            "Main Title",
            "Section A",
            "Subsection A.1",
            "Subsection A.2",
            "Section B",
        ]
        assert len(sections) == len(expected_titles)

        for i, expected_title in enumerate(expected_titles):
            assert sections[i].title == expected_title
            assert sections[i].order == i

        # Verify content preservation
        assert "**bold**" in sections[2].content  # Subsection A.1
        assert "List item 1" in sections[2].content
        assert "```" in sections[4].content  # Section B
