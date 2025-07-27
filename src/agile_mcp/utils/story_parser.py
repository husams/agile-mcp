"""
Utility for parsing story markdown sections.
"""

import re
from typing import Dict, List


class StoryParser:
    """Utility class for parsing sections from story markdown content."""

    # Section aliases mapping
    SECTION_ALIASES = {
        "ac": "Acceptance Criteria",
        "acceptance criteria": "Acceptance Criteria",
        "description": "Story",
        "story": "Story",
        "tasks": "Tasks / Subtasks",
        "tasks / subtasks": "Tasks / Subtasks",
        "status": "Status",
        "dev notes": "Dev Notes",
        "testing": "Testing",
        "change log": "Change Log",
    }

    def normalize_section_name(self, section_name: str) -> str:
        """
        Normalize and validate section name, supporting aliases.

        Args:
            section_name: The section name to normalize

        Returns:
            str: The normalized section name

        Raises:
            ValueError: If section name is empty or invalid
        """
        if not section_name or not section_name.strip():
            raise ValueError("Section name cannot be empty")

        normalized = section_name.strip().lower()

        # Check if it's an alias
        if normalized in self.SECTION_ALIASES:
            return self.SECTION_ALIASES[normalized]

        # Return title case version for non-aliases
        return section_name.strip()

    def extract_section(self, content: str, section_name: str) -> str:
        """
        Extract a specific section from story markdown content.

        Args:
            content: The full markdown content of the story
            section_name: The name of the section to extract

        Returns:
            str: The content of the requested section

        Raises:
            SectionNotFoundError: If the section is not found
            ValueError: If parameters are invalid
        """
        if not content or not content.strip():
            raise ValueError("Content cannot be empty")

        # Normalize the section name
        try:
            normalized_section = self.normalize_section_name(section_name)
        except ValueError as e:
            raise ValueError(f"Invalid section name: {e}")

        # Split content into lines for processing
        lines = content.split("\n")

        # Find all section headers and their positions
        sections = self._find_sections(lines)

        # Look for the requested section (case-insensitive)
        target_section = None
        for section_header, start_line in sections:
            if section_header.lower() == normalized_section.lower():
                target_section = (section_header, start_line)
                break

        if not target_section:
            # Import here to avoid circular import
            from ..services.exceptions import SectionNotFoundError

            available_sections = [header for header, _ in sections]
            raise SectionNotFoundError(
                f"Section '{section_name}' not found. Available sections: {', '.join(available_sections)}"
            )

        # Extract content between this section and the next
        section_header, start_line = target_section
        end_line = len(lines)

        # Find the next section header to determine where this section ends
        for other_header, other_start in sections:
            if other_start > start_line and other_start < end_line:
                end_line = other_start

        # Extract the section content (excluding the header)
        section_lines = lines[start_line + 1 : end_line]

        # Remove trailing empty lines
        while section_lines and not section_lines[-1].strip():
            section_lines.pop()

        # Join lines and return content
        section_content = "\n".join(section_lines)

        if not section_content.strip():
            return ""

        return section_content

    def _find_sections(self, lines: List[str]) -> List[tuple]:
        """
        Find all section headers in the markdown content.

        Args:
            lines: List of lines from the markdown content

        Returns:
            List[tuple]: List of (section_name, line_number) tuples
        """
        sections = []
        section_header_pattern = re.compile(r"^## (.+)$")

        for i, line in enumerate(lines):
            match = section_header_pattern.match(line.strip())
            if match:
                section_name = match.group(1).strip()
                sections.append((section_name, i))

        return sections

    def list_sections(self, content: str) -> List[str]:
        """
        List all available sections in the story content.

        Args:
            content: The full markdown content of the story

        Returns:
            List[str]: List of available section names
        """
        if not content or not content.strip():
            return []

        lines = content.split("\n")
        sections = self._find_sections(lines)
        return [header for header, _ in sections]
