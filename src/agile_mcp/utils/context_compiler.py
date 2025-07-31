"""
Utilities for compiling context from various sources into structured dev_notes.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class ContextCompiler:
    """Utility class for compiling development context into structured dev_notes."""

    def __init__(self):
        """Initialize the context compiler with default templates."""
        self.templates = {
            "basic": self._get_basic_template(),
            "api_development": self._get_api_template(),
            "ui_component": self._get_ui_template(),
            "data_model": self._get_data_model_template(),
            "service_layer": self._get_service_template(),
        }

    def compile_dev_notes(
        self,
        contexts: Dict[str, Any],
        template_type: str = "basic",
        custom_template: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Compile various context sources into structured dev_notes.

        Args:
            contexts: Dictionary containing context from various sources
            template_type: Type of template to use ('basic', 'api_development', etc.)
            custom_template: Optional custom template to use instead

        Returns:
            JSON string containing compiled dev_notes
        """
        template = custom_template or self.templates.get(
            template_type, self.templates["basic"]
        )

        compiled_notes: Dict[str, Any] = {}

        # Process each section of the template
        for section, section_config in template.items():
            compiled_notes[section] = self._process_section(section_config, contexts)

        # Add metadata
        compiled_notes["_metadata"] = {
            "compiled_at": datetime.now(timezone.utc).isoformat(),
            "template_used": template_type,
            "context_sources": list(contexts.keys()),
        }

        return json.dumps(compiled_notes, indent=2)

    def _process_section(
        self, section_config: Dict[str, Any], contexts: Dict[str, Any]
    ) -> Any:
        """Process a single section of the template."""
        if isinstance(section_config, dict):
            result = {}
            for key, config in section_config.items():
                if isinstance(config, str) and config.startswith("$"):
                    # This is a context reference
                    result[key] = self._resolve_context_reference(config, contexts)
                elif isinstance(config, dict):
                    result[key] = self._process_section(config, contexts)
                elif isinstance(config, list):
                    result[key] = [
                        (
                            self._process_section(item, contexts)
                            if isinstance(item, dict)
                            else (
                                self._resolve_context_reference(item, contexts)
                                if isinstance(item, str) and item.startswith("$")
                                else item
                            )
                        )
                        for item in config
                    ]
                else:
                    result[key] = config
            return result
        elif isinstance(section_config, str) and section_config.startswith("$"):
            return self._resolve_context_reference(section_config, contexts)
        else:
            return section_config

    def _resolve_context_reference(
        self, reference: str, contexts: Dict[str, Any]
    ) -> Any:
        """Resolve a context reference like '$architecture.patterns' to actual data."""
        if not reference.startswith("$"):
            return reference

        path = reference[1:]  # Remove the $ prefix
        path_parts = path.split(".")

        try:
            current = contexts
            for part in path_parts:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return f"[Context not found: {reference}]"

            return (
                current if current is not None else f"[Context not found: {reference}]"
            )
        except (KeyError, TypeError, AttributeError):
            return f"[Context not found: {reference}]"

    def _get_basic_template(self) -> Dict[str, Any]:
        """Get the basic dev_notes template."""
        return {
            "architecture": {
                "overview": "$architecture.overview",
                "patterns": "$architecture.patterns",
                "dependencies": "$architecture.dependencies",
            },
            "implementation": {
                "files_to_modify": "$implementation.files",
                "key_methods": "$implementation.methods",
                "entry_points": "$implementation.entry_points",
            },
            "technical_constraints": "$constraints.technical",
            "business_rules": "$constraints.business",
            "related_stories": "$related.stories",
            "testing_guidance": {
                "unit_tests": "$testing.unit",
                "integration_tests": "$testing.integration",
                "e2e_tests": "$testing.e2e",
            },
        }

    def _get_api_template(self) -> Dict[str, Any]:
        """Get the API development template."""
        return {
            "architecture": {
                "overview": "$architecture.overview",
                "patterns": "$architecture.api_patterns",
                "dependencies": "$architecture.dependencies",
            },
            "api_specification": {
                "endpoints": "$api.endpoints",
                "request_models": "$api.request_models",
                "response_models": "$api.response_models",
                "authentication": "$api.authentication",
                "rate_limiting": "$api.rate_limiting",
            },
            "implementation": {
                "controller_files": "$implementation.controllers",
                "service_files": "$implementation.services",
                "model_files": "$implementation.models",
                "middleware": "$implementation.middleware",
            },
            "validation": {
                "input_validation": "$validation.input",
                "business_rules": "$validation.business",
                "security_checks": "$validation.security",
            },
            "testing_guidance": {
                "unit_tests": "$testing.unit",
                "integration_tests": "$testing.integration",
                "api_tests": "$testing.api",
            },
        }

    def _get_ui_template(self) -> Dict[str, Any]:
        """Get the UI component template."""
        return {
            "component_design": {
                "overview": "$design.overview",
                "component_type": "$design.type",
                "props_interface": "$design.props",
                "state_management": "$design.state",
            },
            "implementation": {
                "component_file": "$implementation.component",
                "style_files": "$implementation.styles",
                "test_files": "$implementation.tests",
                "story_files": "$implementation.stories",
            },
            "dependencies": {
                "ui_library": "$dependencies.ui",
                "utilities": "$dependencies.utils",
                "icons": "$dependencies.icons",
            },
            "accessibility": {
                "aria_labels": "$accessibility.aria",
                "keyboard_navigation": "$accessibility.keyboard",
                "screen_reader": "$accessibility.screen_reader",
            },
            "testing_guidance": {
                "unit_tests": "$testing.unit",
                "visual_tests": "$testing.visual",
                "accessibility_tests": "$testing.accessibility",
            },
        }

    def _get_data_model_template(self) -> Dict[str, Any]:
        """Get the data model template."""
        return {
            "database_design": {
                "overview": "$database.overview",
                "tables": "$database.tables",
                "relationships": "$database.relationships",
                "indexes": "$database.indexes",
            },
            "model_implementation": {
                "model_files": "$implementation.models",
                "migration_files": "$implementation.migrations",
                "repository_files": "$implementation.repositories",
            },
            "data_validation": {
                "field_validation": "$validation.fields",
                "business_rules": "$validation.business",
                "constraints": "$validation.constraints",
            },
            "performance": {
                "query_optimization": "$performance.queries",
                "caching_strategy": "$performance.caching",
                "indexing_strategy": "$performance.indexing",
            },
            "testing_guidance": {
                "model_tests": "$testing.models",
                "repository_tests": "$testing.repositories",
                "migration_tests": "$testing.migrations",
            },
        }

    def _get_service_template(self) -> Dict[str, Any]:
        """Get the service layer template."""
        return {
            "service_design": {
                "overview": "$service.overview",
                "responsibilities": "$service.responsibilities",
                "interfaces": "$service.interfaces",
                "dependencies": "$service.dependencies",
            },
            "implementation": {
                "service_files": "$implementation.services",
                "interface_files": "$implementation.interfaces",
                "dto_files": "$implementation.dtos",
                "exception_files": "$implementation.exceptions",
            },
            "business_logic": {
                "core_methods": "$business.methods",
                "validation_rules": "$business.validation",
                "error_handling": "$business.errors",
            },
            "integration": {
                "external_services": "$integration.external",
                "database_access": "$integration.database",
                "caching": "$integration.caching",
            },
            "testing_guidance": {
                "unit_tests": "$testing.unit",
                "integration_tests": "$testing.integration",
                "contract_tests": "$testing.contracts",
            },
        }

    def create_context_from_sources(
        self,
        architecture_docs: Optional[str] = None,
        api_specs: Optional[str] = None,
        related_stories: Optional[List[Dict[str, Any]]] = None,
        coding_standards: Optional[str] = None,
        business_requirements: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a structured context dictionary from various source materials.

        Args:
            architecture_docs: Architecture documentation content
            api_specs: API specification content
            related_stories: List of related story objects
            coding_standards: Coding standards content
            business_requirements: Business requirements content

        Returns:
            Structured context dictionary ready for compilation
        """
        context: Dict[str, Any] = {}

        if architecture_docs:
            context["architecture"] = self._parse_architecture_docs(architecture_docs)

        if api_specs:
            context["api"] = self._parse_api_specs(api_specs)

        if related_stories:
            context["related"] = {
                "stories": self._format_related_stories(related_stories)
            }

        if coding_standards:
            context["testing"] = self._parse_testing_guidance(coding_standards)
            context["constraints"] = self._parse_constraints(coding_standards)

        if business_requirements:
            context["business"] = self._parse_business_requirements(
                business_requirements
            )

        return context

    def _parse_architecture_docs(self, docs: str) -> Dict[str, Any]:
        """Parse architecture documentation into structured format."""
        # Simple parser - in production, this would be more sophisticated
        return {
            "overview": self._extract_section(docs, "overview"),
            "patterns": self._extract_list_section(docs, "patterns"),
            "dependencies": self._extract_list_section(docs, "dependencies"),
            "api_patterns": self._extract_list_section(docs, "api patterns"),
        }

    def _parse_api_specs(self, specs: str) -> Dict[str, Any]:
        """Parse API specifications into structured format."""
        return {
            "endpoints": self._extract_endpoints(specs),
            "request_models": self._extract_models(specs, "request"),
            "response_models": self._extract_models(specs, "response"),
            "authentication": self._extract_section(specs, "authentication"),
            "rate_limiting": self._extract_section(specs, "rate limiting"),
        }

    def _format_related_stories(
        self, stories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Format related stories for inclusion in dev_notes."""
        formatted: List[Dict[str, Any]] = []
        for story in stories:
            formatted.append(
                {
                    "id": story.get("id"),
                    "title": story.get("title"),
                    "relevance": (
                        f"Related implementation patterns in "
                        f"{story.get('title', 'unknown')}"
                    ),
                    "dev_notes_excerpt": (
                        story.get("dev_notes", "")[:200] + "..."
                        if story.get("dev_notes")
                        else None
                    ),
                }
            )
        return formatted

    def _parse_testing_guidance(self, standards: str) -> Dict[str, Any]:
        """Parse testing guidance from coding standards."""
        return {
            "unit": self._extract_section(standards, "unit test"),
            "integration": self._extract_section(standards, "integration test"),
            "e2e": self._extract_section(standards, "e2e test"),
            "api": self._extract_section(standards, "api test"),
            "visual": self._extract_section(standards, "visual test"),
            "accessibility": self._extract_section(standards, "accessibility test"),
        }

    def _parse_constraints(self, standards: str) -> Dict[str, Any]:
        """Parse technical and business constraints."""
        return {
            "technical": self._extract_list_section(standards, "technical constraint"),
            "business": self._extract_list_section(standards, "business rule"),
        }

    def _parse_business_requirements(self, requirements: str) -> Dict[str, Any]:
        """Parse business requirements."""
        return {
            "rules": self._extract_list_section(requirements, "business rule"),
            "constraints": self._extract_list_section(requirements, "constraint"),
        }

    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a named section from text."""
        # Simple extraction - in production, this would use proper parsing
        lines = text.split("\n")
        section_lines: List[str] = []
        in_section = False

        for line in lines:
            if section_name.lower() in line.lower() and line.strip().startswith("#"):
                in_section = True
                continue
            elif in_section and line.strip().startswith("#"):
                break
            elif in_section:
                section_lines.append(line)

        return "\n".join(section_lines).strip()

    def _extract_list_section(self, text: str, section_name: str) -> List[str]:
        """Extract a list from a named section."""
        section_text = self._extract_section(text, section_name)
        if not section_text:
            return []

        # Extract bullet points or numbered items
        items: List[str] = []
        for line in section_text.split("\n"):
            line = line.strip()
            if line.startswith("- ") or line.startswith("* "):
                items.append(line[2:])
            elif line and line[0].isdigit() and ". " in line:
                items.append(line.split(". ", 1)[1])

        return items

    def _extract_endpoints(self, specs: str) -> List[Dict[str, str]]:
        """Extract API endpoints from specifications."""
        # Simplified endpoint extraction
        endpoints: List[Dict[str, str]] = []
        lines = specs.split("\n")

        for line in lines:
            line = line.strip()
            if any(
                method in line.upper()
                for method in ["GET", "POST", "PUT", "DELETE", "PATCH"]
            ):
                parts = line.split()
                if len(parts) >= 2:
                    endpoints.append(
                        {
                            "method": parts[0].upper(),
                            "path": parts[1],
                            "description": (
                                " ".join(parts[2:]) if len(parts) > 2 else ""
                            ),
                        }
                    )

        return endpoints

    def _extract_models(self, specs: str, model_type: str) -> List[Dict[str, Any]]:
        """Extract data models from specifications."""
        # Simplified model extraction
        models: List[Dict[str, Any]] = []
        # This would be more sophisticated in production
        return models

    def validate_dev_notes(self, dev_notes: str) -> Dict[str, Any]:
        """
        Validate the compiled dev_notes for completeness and quality.

        Args:
            dev_notes: JSON string of compiled dev_notes

        Returns:
            Validation result with score and recommendations
        """
        try:
            notes = json.loads(dev_notes)
        except json.JSONDecodeError:
            return {
                "valid": False,
                "score": 0,
                "errors": ["Invalid JSON format"],
                "recommendations": ["Fix JSON syntax errors"],
            }

        score: int = 0
        recommendations: List[str] = []
        errors: List[str] = []

        # Check required sections
        required_sections = ["architecture", "implementation", "testing_guidance"]
        for section in required_sections:
            if section in notes:
                score += 20
            else:
                errors.append(f"Missing required section: {section}")
                recommendations.append(
                    f"Add {section} section with relevant information"
                )

        # Check for context not found markers
        notes_str = json.dumps(notes)
        not_found_count = notes_str.count("[Context not found:")
        if not_found_count > 0:
            score -= not_found_count * 5
            recommendations.append(
                f"Resolve {not_found_count} missing context references"
            )

        # Check for actionable content
        if "files_to_modify" in notes.get("implementation", {}):
            score += 10
        else:
            recommendations.append(
                "Add specific files to modify in implementation section"
            )

        if "key_methods" in notes.get("implementation", {}):
            score += 10
        else:
            recommendations.append("Add key methods to implement")

        # Ensure score is between 0 and 100
        score = max(0, min(100, score))

        return {
            "valid": len(errors) == 0,
            "score": score,
            "errors": errors,
            "recommendations": recommendations,
            "quality_level": (
                "Excellent"
                if score >= 90
                else "Good" if score >= 70 else "Adequate" if score >= 50 else "Poor"
            ),
        }


# Convenience functions for common use cases
def compile_basic_dev_notes(contexts: Dict[str, Any]) -> str:
    """Compile basic dev_notes from context sources."""
    compiler = ContextCompiler()
    return compiler.compile_dev_notes(contexts, "basic")


def compile_api_dev_notes(contexts: Dict[str, Any]) -> str:
    """Compile API-focused dev_notes from context sources."""
    compiler = ContextCompiler()
    return compiler.compile_dev_notes(contexts, "api_development")


def create_context_from_documents(
    architecture_content: Optional[str] = None,
    api_content: Optional[str] = None,
    related_stories: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Create context dictionary from document contents."""
    compiler = ContextCompiler()
    return compiler.create_context_from_sources(
        architecture_docs=architecture_content,
        api_specs=api_content,
        related_stories=related_stories,
    )
