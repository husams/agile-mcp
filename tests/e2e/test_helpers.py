"""
Enhanced E2E Test Validation Utilities

Comprehensive JSON response validation with schema validation and MCP protocol compliance
for production server testing with real data.
"""

import json
import pytest
from typing import Dict, Any, Optional, Union, Type
from pydantic import BaseModel, ValidationError

from src.agile_mcp.models.response import (
    StoryResponse, EpicResponse, ArtifactResponse, DependencyResponse,
    StorySectionResponse, DependencyAddResponse, DoDChecklistResponse
)


def validate_json_response(response: str) -> dict:
    """
    Validate response is parseable JSON and return parsed data.
    
    Args:
        response: Raw response string from MCP tool execution
        
    Returns:
        dict: Parsed JSON response data
        
    Raises:
        pytest.fail: If response is not valid JSON with detailed error info
    """
    try:
        parsed = json.loads(response)
        if not isinstance(parsed, dict):
            pytest.fail(f"Response must be dict, got {type(parsed).__name__}: {response[:200]}...")
        return parsed
    except json.JSONDecodeError as e:
        # Check if this is a FastMCP error message format
        if response.startswith("Error calling tool"):
            # Parse FastMCP error message and convert to standard error format
            return parse_fastmcp_error_message(response)
        
        error_context = response[:200] if len(response) > 200 else response
        pytest.fail(
            f"Response is not valid JSON:\n"
            f"Error: {e}\n"
            f"Error position: line {e.lineno}, column {e.colno}\n"
            f"Response snippet: {error_context}..."
        )


def parse_fastmcp_error_message(error_text: str) -> dict:
    """
    Parse FastMCP error message format and convert to standard error response format.
    
    FastMCP errors look like: "Error calling tool 'toolName': Error message here..."
    
    Args:
        error_text: FastMCP error message text
        
    Returns:
        dict: Standardized error response format compatible with test expectations
    """
    import re
    
    # Extract tool name and error message using regex
    pattern = r"Error calling tool '([^']+)': (.+)"
    match = re.match(pattern, error_text)
    
    if match:
        tool_name = match.group(1)
        error_message = match.group(2)
        
        # Determine error type based on message content
        error_type = "unknown_error"
        if "validation error" in error_message.lower():
            error_type = "validation_error"
        elif "not found" in error_message.lower():
            error_type = "not_found_error"
        elif "invalid relation" in error_message.lower():
            error_type = "invalid_relation_error"
        elif "database error" in error_message.lower():
            error_type = "database_error"
            
        # Return standardized error format
        return {
            "success": False,
            "error": error_type,
            "message": error_message,
            "tool": tool_name,
            "source": "fastmcp_error_wrapper"
        }
    else:
        # Fallback for unrecognized error format
        return {
            "success": False,
            "error": "parse_error",
            "message": error_text,
            "source": "fastmcp_error_wrapper"
        }


def validate_tool_response_format(response_json: dict) -> dict:
    """
    Validate standardized tool response structure for production data.
    
    Args:
        response_json: Parsed JSON response from tool execution
        
    Returns:
        dict: Validated response data
        
    Raises:
        pytest.fail: If response doesn't follow expected tool format
    """
    # Tools return data directly, success field is not required for successful responses
    # Only validate success field exists if it's present (for error responses)
    required_fields = []
    
    for field in required_fields:
        if field not in response_json:
            pytest.fail(
                f"Tool response missing required field '{field}'\n"
                f"Response structure: {list(response_json.keys())}\n"
                f"Full response: {response_json}"
            )
    
    # Check if this is an error response format or direct data response
    if "success" in response_json:
        # MCPResponse format with success field
        success = response_json["success"]
        if not isinstance(success, bool):
            pytest.fail(
                f"Field 'success' must be boolean, got {type(success).__name__}: {success}\n"
                f"Response: {response_json}"
            )
        
        if success:
            if "data" not in response_json:
                pytest.fail(
                    f"Success response missing 'data' field\n"
                    f"Response: {response_json}"
                )
        else:
            missing_error_fields = []
            if "error" not in response_json:
                missing_error_fields.append("error")
            if "message" not in response_json:
                missing_error_fields.append("message")
            
            if missing_error_fields:
                pytest.fail(
                    f"Error response missing required fields: {missing_error_fields}\n"
                    f"Response: {response_json}"
                )
    else:
        # Direct data response format (no success field) - assume success
        # This is for tools that return data directly
        pass
    
    return response_json


def extract_response_data(response_json: dict) -> Any:
    """
    Extract response data from JSON-RPC format, handling both success and error cases.
    
    Args:
        response_json: Validated JSON response
        
    Returns:
        Any: The data payload from successful response
        
    Raises:
        pytest.fail: If response indicates error or data extraction fails
    """
    # Handle both MCPResponse format and direct data format
    if "success" in response_json:
        # MCPResponse format
        if not response_json["success"]:
            error_msg = response_json.get("message", "Unknown error")
            error_details = response_json.get("error", "No error details")
            pytest.fail(
                f"Tool execution failed with error:\n"
                f"Message: {error_msg}\n"
                f"Details: {error_details}\n"
                f"Full response: {response_json}"
            )
        # Return the data payload from success response
        data = response_json.get("data")
    else:
        # Direct data response format - return the entire response
        data = response_json
    if data is None:
        pytest.fail(
            f"Success response contains null or missing data\n"
            f"Response: {response_json}"
        )
    
    return data


def validate_error_response_format(response_json: dict) -> dict:
    """
    Validate error response format compliance for production error handling.
    
    Args:
        response_json: Parsed JSON error response
        
    Returns:
        dict: Validated error response
        
    Raises:
        pytest.fail: If error response format is invalid
    """
    if response_json.get("success", True):
        pytest.fail(
            f"Expected error response but got success=True\n"
            f"Response: {response_json}"
        )
    
    required_error_fields = ["error", "message"]
    missing_fields = [field for field in required_error_fields if field not in response_json]
    
    if missing_fields:
        pytest.fail(
            f"Error response missing required fields: {missing_fields}\n"
            f"Available fields: {list(response_json.keys())}\n"
            f"Response: {response_json}"
        )
    
    error_msg = response_json["message"]
    if not isinstance(error_msg, str) or not error_msg.strip():
        pytest.fail(
            f"Error message must be non-empty string, got: {repr(error_msg)}\n"
            f"Response: {response_json}"
        )
    
    return response_json


def validate_pydantic_model(
    data: Dict[str, Any], 
    model_class: Type[BaseModel], 
    context: str = ""
) -> BaseModel:
    """
    Validate data against Pydantic model with detailed error reporting.
    
    Args:
        data: Response data to validate
        model_class: Pydantic model class for validation
        context: Additional context for error messages
        
    Returns:
        BaseModel: Validated model instance
        
    Raises:
        pytest.fail: If validation fails with detailed error info
    """
    try:
        return model_class(**data)
    except ValidationError as e:
        error_details = []
        for error in e.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            error_details.append(f"  {field_path}: {error['msg']} (got: {error.get('input', 'N/A')})")
        
        context_str = f" ({context})" if context else ""
        pytest.fail(
            f"{model_class.__name__} validation failed{context_str}:\n"
            f"Validation errors:\n" + "\n".join(error_details) + "\n"
            f"Input data: {data}"
        )
    except TypeError as e:
        context_str = f" ({context})" if context else ""
        pytest.fail(
            f"{model_class.__name__} validation failed{context_str}:\n"
            f"Type error: {e}\n"
            f"Input data: {data}"
        )


def validate_story_response(response_data: dict) -> StoryResponse:
    """Validate response data matches StoryResponse schema for production story data."""
    return validate_pydantic_model(response_data, StoryResponse, "story response")


def validate_epic_response(response_data: dict) -> EpicResponse:
    """Validate response data matches EpicResponse schema for production epic data."""
    return validate_pydantic_model(response_data, EpicResponse, "epic response")


def validate_artifact_response(response_data: dict) -> ArtifactResponse:
    """Validate response data matches ArtifactResponse schema for production artifact data."""
    return validate_pydantic_model(response_data, ArtifactResponse, "artifact response")


def validate_dependency_response(response_data: dict) -> DependencyResponse:
    """Validate response data matches DependencyResponse schema for production dependency data."""
    return validate_pydantic_model(response_data, DependencyResponse, "dependency response")


def validate_story_section_response(response_data: dict) -> StorySectionResponse:
    """Validate response data matches StorySectionResponse schema."""
    return validate_pydantic_model(response_data, StorySectionResponse, "story section response")


def validate_dependency_add_response(response_data: dict) -> DependencyAddResponse:
    """Validate response data matches DependencyAddResponse schema."""
    return validate_pydantic_model(response_data, DependencyAddResponse, "dependency add response")


def validate_dod_checklist_response(response_data: dict) -> DoDChecklistResponse:
    """Validate response data matches DoDChecklistResponse schema for DoD checklist responses."""
    return validate_pydantic_model(response_data, DoDChecklistResponse, "DoD checklist response")


def validate_full_tool_response(
    response: str, 
    expected_model: Optional[Type[BaseModel]] = None,
    allow_error: bool = False
) -> Union[BaseModel, dict]:
    """
    Complete validation chain for MCP tool responses with production data support.
    
    Args:
        response: Raw response string from MCP tool
        expected_model: Optional Pydantic model class for data validation
        allow_error: If True, don't fail on error responses
        
    Returns:
        Union[BaseModel, dict]: Validated model instance or raw data
        
    Raises:
        pytest.fail: If any validation step fails
    """
    # Step 1: Validate JSON parsing
    response_json = validate_json_response(response)
    
    # Step 2: Validate tool response format
    response_json = validate_tool_response_format(response_json)
    
    # Step 3: Handle error responses
    # If no success field present, assume success (direct data response)
    # If success field present and False, it's an error
    is_error = "success" in response_json and not response_json["success"]
    if is_error:
        if allow_error:
            return validate_error_response_format(response_json)
        else:
            # This will raise pytest.fail
            extract_response_data(response_json)
    
    # Step 4: Extract and validate data
    data = extract_response_data(response_json)
    
    # Step 5: Optional schema validation
    if expected_model:
        return validate_pydantic_model(data, expected_model)
    
    return data


# Convenience functions for common validation patterns
def validate_story_tool_response(response: str) -> StoryResponse:
    """Complete validation for story tool responses."""
    return validate_full_tool_response(response, StoryResponse)


def validate_epic_tool_response(response: str) -> EpicResponse:
    """Complete validation for epic tool responses."""
    return validate_full_tool_response(response, EpicResponse)


def validate_artifact_tool_response(response: str) -> ArtifactResponse:
    """Complete validation for artifact tool responses."""
    return validate_full_tool_response(response, ArtifactResponse)


def validate_dependency_tool_response(response: str) -> DependencyResponse:
    """Complete validation for dependency tool responses."""
    return validate_full_tool_response(response, DependencyResponse)


def validate_dod_checklist_tool_response(response: str) -> DoDChecklistResponse:
    """Complete validation for DoD checklist tool responses."""
    return validate_full_tool_response(response, DoDChecklistResponse)


# JSON-RPC 2.0 Protocol Compliance Validators

def validate_jsonrpc_request_format(request_data: dict) -> dict:
    """
    Validate JSON-RPC 2.0 request format compliance.
    
    Args:
        request_data: Parsed JSON-RPC request
        
    Returns:
        dict: Validated request data
        
    Raises:
        pytest.fail: If request format is invalid
    """
    required_fields = ["jsonrpc", "method", "id"]
    missing_fields = [field for field in required_fields if field not in request_data]
    
    if missing_fields:
        pytest.fail(
            f"JSON-RPC request missing required fields: {missing_fields}\n"
            f"Available fields: {list(request_data.keys())}\n"
            f"Request: {request_data}"
        )
    
    # Validate jsonrpc version
    if request_data["jsonrpc"] != "2.0":
        pytest.fail(
            f"JSON-RPC version must be '2.0', got: {request_data['jsonrpc']}\n"
            f"Request: {request_data}"
        )
    
    # Validate method name
    method = request_data["method"]
    if not isinstance(method, str) or not method.strip():
        pytest.fail(
            f"JSON-RPC method must be non-empty string, got: {repr(method)}\n"
            f"Request: {request_data}"
        )
    
    # Validate id (can be string, number, or null, but not missing)
    request_id = request_data["id"]
    if not isinstance(request_id, (str, int, float, type(None))):
        pytest.fail(
            f"JSON-RPC id must be string, number, or null, got: {type(request_id).__name__}\n"
            f"Request: {request_data}"
        )
    
    return request_data


def validate_jsonrpc_response_format(response_data: dict) -> dict:
    """
    Validate JSON-RPC 2.0 response format compliance.
    
    Args:
        response_data: Parsed JSON-RPC response
        
    Returns:
        dict: Validated response data
        
    Raises:
        pytest.fail: If response format is invalid
    """
    required_fields = ["jsonrpc", "id"]
    missing_fields = [field for field in required_fields if field not in response_data]
    
    if missing_fields:
        pytest.fail(
            f"JSON-RPC response missing required fields: {missing_fields}\n"
            f"Available fields: {list(response_data.keys())}\n"
            f"Response: {response_data}"
        )
    
    # Validate jsonrpc version
    if response_data["jsonrpc"] != "2.0":
        pytest.fail(
            f"JSON-RPC version must be '2.0', got: {response_data['jsonrpc']}\n"
            f"Response: {response_data}"
        )
    
    # Must have either result or error, but not both
    has_result = "result" in response_data
    has_error = "error" in response_data
    
    if has_result and has_error:
        pytest.fail(
            f"JSON-RPC response cannot have both 'result' and 'error' fields\n"
            f"Response: {response_data}"
        )
    
    if not has_result and not has_error:
        pytest.fail(
            f"JSON-RPC response must have either 'result' or 'error' field\n"
            f"Available fields: {list(response_data.keys())}\n"
            f"Response: {response_data}"
        )
    
    # Validate error format if present
    if has_error:
        error = response_data["error"]
        if not isinstance(error, dict):
            pytest.fail(
                f"JSON-RPC error must be object, got: {type(error).__name__}\n"
                f"Response: {response_data}"
            )
        
        if "code" not in error or "message" not in error:
            pytest.fail(
                f"JSON-RPC error must have 'code' and 'message' fields\n"
                f"Error object: {error}\n"
                f"Response: {response_data}"
            )
        
        if not isinstance(error["code"], int):
            pytest.fail(
                f"JSON-RPC error code must be integer, got: {type(error['code']).__name__}\n"
                f"Response: {response_data}"
            )
        
        if not isinstance(error["message"], str):
            pytest.fail(
                f"JSON-RPC error message must be string, got: {type(error['message']).__name__}\n"
                f"Response: {response_data}"
            )
    
    return response_data


def validate_mcp_protocol_compliance(request_data: dict, response_data: dict) -> tuple:
    """
    Validate MCP protocol-specific compliance for request/response pair.
    
    Args:
        request_data: Parsed JSON-RPC request
        response_data: Parsed JSON-RPC response
        
    Returns:
        tuple: (validated_request, validated_response)
        
    Raises:
        pytest.fail: If MCP protocol compliance fails
    """
    # Validate basic JSON-RPC compliance first
    validated_request = validate_jsonrpc_request_format(request_data)
    validated_response = validate_jsonrpc_response_format(response_data)
    
    # Validate request/response ID matching
    if validated_request["id"] != validated_response["id"]:
        pytest.fail(
            f"Request and response IDs must match\n"
            f"Request ID: {validated_request['id']}\n"
            f"Response ID: {validated_response['id']}"
        )
    
    # Validate MCP method naming conventions
    method = validated_request["method"]
    valid_mcp_methods = [
        "createStory", "getStory", "updateStory", "deleteStory", "listStories",
        "createEpic", "getEpic", "updateEpic", "deleteEpic", "listEpics",
        "createArtifact", "getArtifact", "updateArtifact", "deleteArtifact", "listArtifacts",
        "addDependency", "removeDependency", "getDependencies", "listDependencies",
        "getBacklogSection", "updateBacklogSection", "listBacklogSections",
        "getNextReadyStory", "evaluateDoD"
    ]
    
    if method not in valid_mcp_methods:
        pytest.fail(
            f"Unknown MCP method: {method}\n"
            f"Valid methods: {valid_mcp_methods}\n"
            f"Request: {validated_request}"
        )
    
    # Validate parameter structure if present
    if "params" in validated_request:
        params = validated_request["params"]
        if not isinstance(params, (dict, list)):
            pytest.fail(
                f"MCP method parameters must be object or array, got: {type(params).__name__}\n"
                f"Request: {validated_request}"
            )
    
    return validated_request, validated_response


def validate_mcp_tool_response_complete(
    request: str, 
    response: str, 
    expected_model: Optional[Type[BaseModel]] = None
) -> Union[BaseModel, dict]:
    """
    Complete MCP protocol and tool response validation chain.
    
    Args:
        request: Raw JSON-RPC request string
        response: Raw JSON-RPC response string
        expected_model: Optional Pydantic model for response data validation
        
    Returns:
        Union[BaseModel, dict]: Validated response data or model
        
    Raises:
        pytest.fail: If any validation step fails
    """
    # Parse both request and response
    request_json = validate_json_response(request)
    response_json = validate_json_response(response)
    
    # Validate MCP protocol compliance
    validate_mcp_protocol_compliance(request_json, response_json)
    
    # Validate tool response format if response is successful
    if "result" in response_json:
        tool_response = response_json["result"]
        if isinstance(tool_response, str):
            # If result is string, parse it as tool response
            return validate_full_tool_response(tool_response, expected_model)
        elif isinstance(tool_response, dict):
            # If result is already parsed, validate directly
            validated_result = validate_tool_response_format(tool_response)
            if not validated_result.get("success", False):
                extract_response_data(validated_result)  # This will fail with error details
            
            data = extract_response_data(validated_result)
            if expected_model:
                return validate_pydantic_model(data, expected_model)
            return data
        else:
            pytest.fail(
                f"JSON-RPC result must be string or object, got: {type(tool_response).__name__}\n"
                f"Response: {response_json}"
            )
    else:
        # Handle JSON-RPC error response
        error = response_json["error"]
        pytest.fail(
            f"JSON-RPC request failed with error:\n"
            f"Code: {error['code']}\n"
            f"Message: {error['message']}\n"
            f"Data: {error.get('data', 'None')}"
        )