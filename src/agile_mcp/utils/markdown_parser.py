"""Markdown parser utility for extracting document sections."""

import re
from typing import List, Tuple


class MarkdownSection:
    """Represents a section in a Markdown document."""

    def __init__(self, title: str, content: str, level: int, order: int):
        """Initialize a Markdown section."""
        self.title = title
        self.content = content
        self.level = level
        self.order = order

    def __repr__(self) -> str:
        """Return string representation of MarkdownSection."""
        return (
            f"<MarkdownSection(title='{self.title}', level={self.level}, "
            f"order={self.order})>"
        )


class MarkdownParser:
    """Parser for extracting structured sections from Markdown content."""

    def __init__(self):
        """Initialize the Markdown parser."""
        # Regex pattern to match Markdown headings (# ## ### etc.)
        self.heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

    def parse(self, content: str) -> List[MarkdownSection]:
        """
        Parse Markdown content into structured sections.

        Args:
            content: The Markdown content to parse

        Returns:
            List of MarkdownSection objects representing the document structure
        """
        if not content or not content.strip():
            return []

        sections = []
        lines = content.split("\n")

        # Find all headings and their positions
        headings = []
        for i, line in enumerate(lines):
            match = self.heading_pattern.match(line)
            if match:
                level = len(match.group(1))  # Count # characters
                title = match.group(2).strip()
                headings.append((i, level, title))

        # If no headings found, treat entire content as single section
        if not headings:
            section = MarkdownSection(
                title="Document Content", content=content.strip(), level=1, order=0
            )
            sections.append(section)
            return sections

        # Extract content for each section
        for order, (line_idx, level, title) in enumerate(headings):
            # Find the start and end of this section's content
            start_idx = line_idx + 1  # Start after the heading line

            # Find the next heading at the same or higher level
            end_idx = len(lines)
            for next_line_idx, next_level, _ in headings[order + 1 :]:
                if next_level <= level:
                    end_idx = next_line_idx
                    break

            # Extract content between headings
            section_lines = lines[start_idx:end_idx]

            # Remove leading and trailing empty lines
            while section_lines and not section_lines[0].strip():
                section_lines.pop(0)
            while section_lines and not section_lines[-1].strip():
                section_lines.pop()

            section_content = "\n".join(section_lines)

            section = MarkdownSection(
                title=title, content=section_content, level=level, order=order
            )
            sections.append(section)

        return sections

    def extract_metadata(self, content: str) -> Tuple[str, str]:
        """
        Extract document title and description from Markdown content.

        Args:
            content: The Markdown content to analyze

        Returns:
            Tuple of (title, description) - title from first H1, description
            from content after first H1
        """
        if not content or not content.strip():
            return "Untitled Document", ""

        lines = content.split("\n")
        title = "Untitled Document"
        description = ""

        # Look for first H1 heading as title
        for i, line in enumerate(lines):
            match = self.heading_pattern.match(line)
            if match and len(match.group(1)) == 1:  # H1 heading
                title = match.group(2).strip()
                if len(title) > 100:
                    title = title[:100]  # Limit title length

                # Extract description from content after title until next heading or reasonable limit
                desc_lines = []
                for desc_line in lines[i + 1 :]:
                    if self.heading_pattern.match(desc_line):
                        break
                    desc_lines.append(desc_line)
                    if len(desc_lines) >= 5:  # Limit description length
                        break

                # Clean up description
                description = "\n".join(desc_lines).strip()
                if len(description) > 500:
                    description = description[:500] + "..."
                break

        # If no H1 found, use filename or first few lines as title/description
        if title == "Untitled Document":
            first_lines = [line.strip() for line in lines[:3] if line.strip()]
            if first_lines:
                title = first_lines[0]
                if len(title) > 100:
                    title = title[:100]  # Limit title length
                if len(first_lines) > 1:
                    description = " ".join(first_lines[1:])[:500]

        return title, description

    def validate_content(self, content: str) -> bool:
        """
        Validate that the content is parseable Markdown.

        Args:
            content: The content to validate

        Returns:
            True if content is valid, False otherwise
        """
        if not isinstance(content, str):
            return False

        # Basic validation - check for reasonable content
        if not content.strip():
            return False

        # Content should not be excessively large
        if len(content) > 10_000_000:  # 10MB limit
            return False

        return True
