"""
FastMCP tools for Epic management operations.
"""

import logging
from typing import Dict, Any, List
from fastmcp import FastMCP
from fastmcp.exceptions import McpError
from mcp.types import ErrorData

from ..database import get_db, create_tables
from ..repositories.epic_repository import EpicRepository
from ..services.epic_service import EpicService
from ..services.exceptions import EpicValidationError, DatabaseError


def register_epic_tools(mcp: FastMCP) -> None:
    """Register epic management tools with the FastMCP server."""
    
    logger = logging.getLogger(__name__)
    
    # Ensure database tables exist
    try:
        create_tables()
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
    
    @mcp.tool("backlog.createEpic")
    def create_epic(title: str, description: str) -> Dict[str, Any]:
        """
        Create a new epic with the specified title and description.
        
        Args:
            title: The name of the epic (max 200 characters)
            description: A detailed explanation of the epic's goal (max 2000 characters)
            
        Returns:
            Dict containing the created epic's id, title, description, and status
            
        Raises:
            McpError: If validation fails or database operation fails
        """
        try:
            db_session = get_db()
            try:
                epic_repository = EpicRepository(db_session)
                epic_service = EpicService(epic_repository)
                
                epic_dict = epic_service.create_epic(title, description)
                return epic_dict
                
            finally:
                db_session.close()
                
        except EpicValidationError as e:
            raise McpError(ErrorData(code=-32001, message=f"Validation error: {str(e)}"))
        except DatabaseError as e:
            raise McpError(ErrorData(code=-32001, message=f"Database error: {str(e)}"))
        except Exception as e:
            raise McpError(ErrorData(code=-32001, message=f"Unexpected error: {str(e)}"))
    
    @mcp.tool("backlog.findEpics")
    def find_epics() -> List[Dict[str, Any]]:
        """
        Retrieve a list of all existing epics.
        
        Returns:
            List of dictionaries, each containing an epic's id, title, description, and status
            
        Raises:
            McpError: If database operation fails
        """
        try:
            db_session = get_db()
            try:
                epic_repository = EpicRepository(db_session)
                epic_service = EpicService(epic_repository)
                
                epics_list = epic_service.find_epics()
                return epics_list
                
            finally:
                db_session.close()
                
        except DatabaseError as e:
            raise McpError(ErrorData(code=-32001, message=f"Database error: {str(e)}"))
        except Exception as e:
            raise McpError(ErrorData(code=-32001, message=f"Unexpected error: {str(e)}"))