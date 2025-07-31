"""Document management tools for the Agile Management MCP Server."""

from typing import Any, Dict, Optional

from fastmcp import FastMCP
from fastmcp.exceptions import McpError
from mcp.types import ErrorData
from pydantic import BaseModel, Field

from ..database import get_db
from ..models.response import DocumentResponse, DocumentSectionResponse
from ..repositories.document_repository import DocumentRepository
from ..repositories.project_repository import ProjectRepository
from ..services.document_service import DocumentService, DocumentValidationError
from ..services.exceptions import DatabaseError, ProjectValidationError
from ..utils.logging_config import create_request_context, get_logger


class DocumentIngestRequest(BaseModel):
    """Request model for document ingestion."""

    project_id: str = Field(
        ..., description="ID of the project to ingest document into"
    )
    file_path: str = Field(..., description="Path to the original file")
    content: str = Field(..., description="Markdown content to parse and ingest")
    title: Optional[str] = Field(
        None, description="Optional custom title for the document"
    )


class DocumentGetSectionRequest(BaseModel):
    """Request model for retrieving document sections."""

    section_id: Optional[str] = Field(
        None, description="ID of the specific section to retrieve"
    )
    title: Optional[str] = Field(None, description="Title to search for in sections")
    document_id: Optional[str] = Field(
        None, description="ID of document to search within"
    )
    project_id: Optional[str] = Field(
        None, description="ID of project to search within"
    )


def documents_ingest(
    project_id: str,
    file_path: str,
    content: str,
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Ingest a document by parsing its Markdown content into structured sections.

    This tool accepts a file's content, parses it into sections based on Markdown headings,
    and saves it to the database linked to a specific project.

    Args:
        project_id: ID of the project to ingest document into
        file_path: Path to the original file
        content: Markdown content to parse and ingest
        title: Optional custom title for the document

    Returns:
        Dict[str, Any]: Document data response

    Raises:
        McpError: For validation and database errors
    """
    logger = get_logger(__name__)
    request_id = "doc-ingest"  # In real implementation, this would be generated

    try:
        logger.info(
            "Processing document ingest request",
            **create_request_context(
                request_id=request_id, tool_name="documents.ingest"
            ),
            project_id=project_id,
            file_path=file_path[:100],  # Truncate for logging
        )

        # Get database session
        db_session = get_db()
        try:
            # Initialize repositories and service
            document_repository = DocumentRepository(db_session)
            project_repository = ProjectRepository(db_session)
            document_service = DocumentService(document_repository, project_repository)

            # Ingest document
            document_data = document_service.ingest_document(
                project_id=project_id,
                file_path=file_path,
                content=content,
                title=title,
            )

            # Convert to response model
            document_response = DocumentResponse(**document_data)

            logger.info(
                "Document ingest request completed successfully",
                **create_request_context(
                    request_id=request_id, tool_name="documents.ingest"
                ),
                document_id=document_data["id"],
                sections_count=len(document_data["sections"]),
            )

            return document_response.model_dump()

        except (DocumentValidationError, ProjectValidationError) as e:
            logger.error(
                "Document validation error in ingest",
                **create_request_context(
                    request_id=request_id, tool_name="documents.ingest"
                ),
                error_type=type(e).__name__,
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Validation error: {str(e)}")
            )
        except DatabaseError as e:
            logger.error(
                "Database error in document ingest",
                **create_request_context(
                    request_id=request_id, tool_name="documents.ingest"
                ),
                error_type="DatabaseError",
                error_message=str(e),
                mcp_error_code=-32002,
            )
            raise McpError(ErrorData(code=-32002, message=f"Database error: {str(e)}"))
        finally:
            db_session.close()

    except McpError:
        raise  # Re-raise MCP errors
    except Exception as e:
        logger.error(
            "Unexpected error in document ingest",
            **create_request_context(
                request_id=request_id, tool_name="documents.ingest"
            ),
            error_type=type(e).__name__,
            error_message=str(e),
            mcp_error_code=-32000,
        )
        raise McpError(ErrorData(code=-32000, message=f"Internal error: {str(e)}"))


def documents_getSection(
    section_id: Optional[str] = None,
    title: Optional[str] = None,
    document_id: Optional[str] = None,
    project_id: Optional[str] = None,
):
    """
    Retrieve document sections by ID or title.

    This tool can retrieve a specific section by its ID, or search for sections
    by title within a document or project.

    Args:
        section_id: ID of the specific section to retrieve
        title: Title to search for in sections (case-insensitive)
        document_id: ID of document to search within (optional)
        project_id: ID of project to search within (optional)

    Returns:
        Dict[str, Any]: Section data response

    Raises:
        McpError: For validation and database errors
    """
    logger = get_logger(__name__)
    request_id = "doc-get-section"  # In real implementation, this would be generated

    try:
        logger.info(
            "Processing get section request",
            **create_request_context(
                request_id=request_id, tool_name="documents.getSection"
            ),
            section_id=section_id,
            title=title,
            document_id=document_id,
            project_id=project_id,
        )

        # Ensure at least one search parameter is provided
        if not section_id and not title:
            raise McpError(
                ErrorData(
                    code=-32001,
                    message="Must provide either section_id or title to search for sections",
                )
            )

        # Get database session
        db_session = get_db()
        try:
            # Initialize repositories and service
            document_repository = DocumentRepository(db_session)
            project_repository = ProjectRepository(db_session)
            document_service = DocumentService(document_repository, project_repository)

            # Retrieve section(s)
            if section_id:
                # Get specific section by ID
                section_data = document_service.get_section_by_id(section_id)
                if not section_data:
                    raise McpError(
                        ErrorData(
                            code=-32003,
                            message=f"Section with ID '{section_id}' not found",
                        )
                    )

                section_response = DocumentSectionResponse(**section_data)

                logger.info(
                    "Section retrieved successfully",
                    **create_request_context(
                        request_id=request_id, tool_name="documents.getSection"
                    ),
                    section_id=section_data["id"],
                )

                return section_response.model_dump()
            else:
                # Search sections by title
                sections_data = document_service.get_sections_by_title(
                    title=title,
                    document_id=document_id,
                    project_id=project_id,
                )

                if not sections_data:
                    search_context = []
                    if document_id:
                        search_context.append(f"document '{document_id}'")
                    if project_id:
                        search_context.append(f"project '{project_id}'")

                    context_str = (
                        " within " + " and ".join(search_context)
                        if search_context
                        else ""
                    )

                    raise McpError(
                        ErrorData(
                            code=-32003,
                            message=(
                                f"No sections found with title containing "
                                f"'{title}'{context_str}"
                            ),
                        )
                    )

                sections_response = [
                    DocumentSectionResponse(**section_data)
                    for section_data in sections_data
                ]

                logger.info(
                    "Sections retrieved successfully",
                    **create_request_context(
                        request_id=request_id, tool_name="documents.getSection"
                    ),
                    sections_count=len(sections_data),
                )

                return [section.model_dump() for section in sections_response]

        except (DocumentValidationError, ProjectValidationError) as e:
            logger.error(
                "Document validation error in get section",
                **create_request_context(
                    request_id=request_id, tool_name="documents.getSection"
                ),
                error_type=type(e).__name__,
                error_message=str(e),
                mcp_error_code=-32001,
            )
            raise McpError(
                ErrorData(code=-32001, message=f"Validation error: {str(e)}")
            )
        except DatabaseError as e:
            logger.error(
                "Database error in get section",
                **create_request_context(
                    request_id=request_id, tool_name="documents.getSection"
                ),
                error_type="DatabaseError",
                error_message=str(e),
                mcp_error_code=-32002,
            )
            raise McpError(ErrorData(code=-32002, message=f"Database error: {str(e)}"))
        finally:
            db_session.close()

    except McpError:
        raise  # Re-raise MCP errors
    except Exception as e:
        logger.error(
            "Unexpected error in get section",
            **create_request_context(
                request_id=request_id, tool_name="documents.getSection"
            ),
            error_type=type(e).__name__,
            error_message=str(e),
            mcp_error_code=-32000,
        )
        raise McpError(ErrorData(code=-32000, message=f"Internal error: {str(e)}"))


def register_document_tools(mcp: FastMCP) -> None:
    """Register document management tools with the FastMCP server."""
    logger = get_logger(__name__)

    @mcp.tool("documents.ingest")
    def ingest_document(
        project_id: str,
        file_path: str,
        content: str,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Ingest a document by parsing its Markdown content into structured sections.

        This tool accepts a file's content, parses it into sections based on Markdown headings,
        and saves it to the database linked to a specific project.

        Args:
            project_id: ID of the project to ingest document into
            file_path: Path to the original file
            content: Markdown content to parse and ingest
            title: Optional custom title for the document

        Returns:
            Dict[str, Any]: Success response with document data or error response
        """
        return documents_ingest(project_id, file_path, content, title)

    @mcp.tool("documents.getSection")
    def get_section(
        section_id: Optional[str] = None,
        title: Optional[str] = None,
        document_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve document sections by ID or title.

        This tool can retrieve a specific section by its ID, or search for sections
        by title within a document or project.

        Args:
            section_id: ID of the specific section to retrieve
            title: Title to search for in sections (case-insensitive)
            document_id: ID of document to search within (optional)
            project_id: ID of project to search within (optional)

        Returns:
            Dict[str, Any]: Success response with section data or error response
        """
        return documents_getSection(section_id, title, document_id, project_id)

    logger.info("Document management tools registered successfully")
