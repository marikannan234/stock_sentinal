"""
Standardized error response schemas for all API endpoints.

All error responses will follow this format:
    {
        "error": {
            "code": "ERROR_CODE",
            "message": "Human readable message",
            "details": {...}
        }
    }
"""

from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Error detail for field-level validation errors."""
    
    field: str = Field(..., description="Field name that caused the error")
    message: str = Field(..., description="Error message for this field")


class ErrorResponse(BaseModel):
    """
    Standard error response format for all endpoints.
    
    Example:
        {
            "error": {
                "code": "INVALID_INPUT",
                "message": "Invalid email format",
                "details": {"field": "email"}
            }
        }
    """
    
    code: str = Field(
        ...,
        description="Machine-readable error code (e.g., INVALID_INPUT, NOT_FOUND)"
    )
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error context/details"
    )


class ErrorWrapper(BaseModel):
    """Wrapper for error response."""
    
    error: ErrorResponse = Field(..., description="Error information")


class ValidationErrorResponse(BaseModel):
    """Validation error response with field-level details."""
    
    code: str = Field(
        default="VALIDATION_ERROR",
        description="Always 'VALIDATION_ERROR' for these responses"
    )
    message: str = Field(
        default="Validation failed",
        description="General validation error message"
    )
    details: List[ErrorDetail] = Field(
        ...,
        description="List of field-level errors"
    )


class ValidationErrorWrapper(BaseModel):
    """Wrapper for validation error response."""
    
    error: ValidationErrorResponse = Field(
        ...,
        description="Validation error information"
    )


# ============================================
# Response examples for different error types
# ============================================

INVALID_INPUT_EXAMPLE = {
    "error": {
        "code": "INVALID_INPUT",
        "message": "Invalid request data",
        "details": {"field": "email", "reason": "not_a_valid_email"}
    }
}

NOT_FOUND_EXAMPLE = {
    "error": {
        "code": "NOT_FOUND",
        "message": "Stock not found",
        "details": {"ticker": "INVALID123"}
    }
}

UNAUTHORIZED_EXAMPLE = {
    "error": {
        "code": "UNAUTHORIZED",
        "message": "Invalid credentials",
        "details": {"reason": "wrong_password"}
    }
}

RATE_LIMIT_EXAMPLE = {
    "error": {
        "code": "RATE_LIMIT_EXCEEDED",
        "message": "Rate limit exceeded",
        "details": {"retry_after": 60}
    }
}

EXTERNAL_API_ERROR_EXAMPLE = {
    "error": {
        "code": "EXTERNAL_API_ERROR",
        "message": "Failed to fetch data from external service",
        "details": {"service": "yfinance", "status_code": 503}
    }
}

INTERNAL_SERVER_ERROR_EXAMPLE = {
    "error": {
        "code": "INTERNAL_SERVER_ERROR",
        "message": "An unexpected error occurred",
        "details": {}
    }
}
