"""
Custom exception classes for Stock Sentinel API.

Provides:
  - Domain-specific exceptions
  - Consistent error handling
  - Automatic HTTP status code mapping
"""

from enum import Enum
from typing import Optional, Dict, Any


class ErrorCode(str, Enum):
    """Standard error codes for the API."""
    
    # Validation errors (400)
    INVALID_INPUT = "INVALID_INPUT"
    INVALID_TICKER = "INVALID_TICKER"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INVALID_ALERT_CONDITION = "INVALID_ALERT_CONDITION"
    
    # Authentication errors (401)
    UNAUTHORIZED = "UNAUTHORIZED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    
    # Authorization errors (403)
    FORBIDDEN = "FORBIDDEN"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    
    # Not found errors (404)
    NOT_FOUND = "NOT_FOUND"
    STOCK_NOT_FOUND = "STOCK_NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    ALERT_NOT_FOUND = "ALERT_NOT_FOUND"
    
    # Conflict errors (409)
    ALREADY_EXISTS = "ALREADY_EXISTS"
    DUPLICATE_ENTRY = "DUPLICATE_ENTRY"
    DUPLICATE_ALERT = "DUPLICATE_ALERT"
    
    # External API errors (502)
    EXTERNAL_API_ERROR = "EXTERNAL_API_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    
    # Server errors (500)
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"


class APIException(Exception):
    """
    Base exception for all API-level errors.
    
    This exception should be caught by the global exception handler
    and converted to a JSON response.
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        code: ErrorCode = ErrorCode.INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize API exception.
        
        Args:
            message: Human-readable error message
            status_code: HTTP status code (default: 500)
            code: Machine-readable error code
            details: Additional error details/context
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        return {
            "error": {
                "code": self.code.value,
                "message": self.message,
                "details": self.details,
            }
        }


class ValidationError(APIException):
    """
    Raised when request validation fails.
    
    Example:
        raise ValidationError(
            message="Invalid email format",
            details={"field": "email"}
        )
    """
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INVALID_INPUT,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=400,
            code=code,
            details=details,
        )


class StockNotFoundError(ValidationError):
    """Raised when a stock ticker is not found."""
    
    def __init__(self, ticker: str):
        super().__init__(
            message=f"Stock '{ticker}' not found",
            code=ErrorCode.STOCK_NOT_FOUND,
            details={"ticker": ticker},
        )


class InvalidTickerError(ValidationError):
    """Raised when ticker format is invalid."""
    
    def __init__(self, ticker: str):
        super().__init__(
            message=f"Invalid ticker format: '{ticker}'",
            code=ErrorCode.INVALID_TICKER,
            details={"ticker": ticker},
        )


class RateLimitError(ValidationError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(
            message=detail,
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
        )
        self.status_code = 429


class AuthenticationError(APIException):
    """
    Raised when authentication fails.
    
    Example:
        raise AuthenticationError(
            message="Invalid credentials",
            details={"reason": "wrong_password"}
        )
    """
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.UNAUTHORIZED,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=401,
            code=code,
            details=details,
        )


class TokenExpiredError(AuthenticationError):
    """Raised when JWT token has expired."""
    
    def __init__(self):
        super().__init__(
            message="Token has expired",
            code=ErrorCode.TOKEN_EXPIRED,
        )


class InvalidCredentialsError(AuthenticationError):
    """Raised when credentials are invalid."""
    
    def __init__(self):
        super().__init__(
            message="Invalid email or password",
            code=ErrorCode.INVALID_CREDENTIALS,
        )


class AuthorizationError(APIException):
    """
    Raised when user lacks required permissions.
    
    Example:
        raise AuthorizationError(
            message="You don't have permission to access this resource"
        )
    """
    
    def __init__(
        self,
        message: str = "Insufficient permissions",
        code: ErrorCode = ErrorCode.FORBIDDEN,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=403,
            code=code,
            details=details,
        )


class NotFoundError(APIException):
    """
    Raised when a requested resource is not found.
    
    Example:
        raise NotFoundError(
            message="User not found",
            details={"user_id": 123}
        )
    """
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.NOT_FOUND,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=404,
            code=code,
            details=details,
        )


class ConflictError(APIException):
    """
    Raised when there's a conflict (e.g., duplicate entry).
    
    Example:
        raise ConflictError(
            message="User with this email already exists",
            details={"field": "email"}
        )
    """
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.ALREADY_EXISTS,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=409,
            code=code,
            details=details,
        )


class ExternalAPIError(APIException):
    """
    Raised when an external API call fails.
    
    Example:
        raise ExternalAPIError(
            message="Failed to fetch data from YFinance",
            details={"service": "yfinance", "status_code": 503}
        )
    """
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.EXTERNAL_API_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=502,
            code=code,
            details=details,
        )


class DatabaseError(APIException):
    """
    Raised when database operations fail.
    
    Example:
        raise DatabaseError(
            message="Failed to save changes to database",
            details={"operation": "INSERT"}
        )
    """
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.DATABASE_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=500,
            code=code,
            details=details,
        )


# ============================================================================
# Alert-Specific Exceptions
# ============================================================================


class AlertNotFoundError(NotFoundError):
    """Raised when an alert is not found."""
    
    def __init__(self, alert_id: int):
        super().__init__(
            message=f"Alert with ID {alert_id} not found",
            code=ErrorCode.ALERT_NOT_FOUND,
            details={"alert_id": alert_id},
        )


class DuplicateAlertError(ConflictError):
    """Raised when attempting to create a duplicate alert."""
    
    def __init__(self, symbol: str, condition: str, target_value: float):
        super().__init__(
            message=f"Alert already exists for {symbol} {condition} {target_value}",
            code=ErrorCode.DUPLICATE_ALERT,
            details={
                "symbol": symbol,
                "condition": condition,
                "target_value": target_value,
            },
        )


class InvalidAlertConditionError(ValidationError):
    """Raised when an invalid alert condition is provided."""
    
    def __init__(self, condition: str, valid_conditions: list):
        super().__init__(
            message=f"Invalid alert condition: '{condition}'. Valid conditions are: {', '.join(valid_conditions)}",
            code=ErrorCode.INVALID_ALERT_CONDITION,
            details={
                "provided": condition,
                "valid_options": valid_conditions,
            },
        )
