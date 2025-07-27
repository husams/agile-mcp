import json
from typing import Any, Dict, Optional
from datetime import datetime


class MCPResponse:
    """
    Utility class for standardized MCP JSON response formatting.
    
    Ensures all tool responses return valid JSON strings that can be parsed
    by MCP clients without JSONDecodeError issues.
    """
    
    @staticmethod
    def success(data: Any = None, message: str = "Operation completed successfully") -> str:
        """
        Create a standardized success response.
        
        Args:
            data: The response data (will be serialized to JSON)
            message: Success message
            
        Returns:
            JSON string with standardized success format
        """
        response = {
            "success": True,
            "data": data,
            "message": message
        }
        return json.dumps(response, default=str)
    
    @staticmethod
    def error(error_type: str, message: str, details: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a standardized error response.
        
        Args:
            error_type: Type of error (e.g., "circular_dependency", "story_not_found")
            message: Error message
            details: Optional additional error details
            
        Returns:
            JSON string with standardized error format
        """
        response = {
            "success": False,
            "error": error_type,
            "message": message
        }
        if details:
            response["details"] = details
            
        return json.dumps(response, default=str)