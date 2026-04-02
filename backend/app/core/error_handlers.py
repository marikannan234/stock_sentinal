"""
Global middleware and exception handlers for FastAPI application.

Provides:
  - Request/response logging
  - Global exception handling
  - Consistent error responses
  - Request timing and performance tracking
"""

import time
import traceback
import logging
from typing import Callable
from uuid import uuid4

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.core.exceptions import APIException
from app.schemas.error_responses import ErrorWrapper, ErrorResponse


logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for all unhandled exceptions.
    
    Catches:
      - APIException (custom domain exceptions)
      - Pydantic ValidationError
      - Generic exceptions
    
    Returns consistent JSON error response.
    """
    
    # Log the exception
    logger.error(
        f"Unhandled exception in {request.method} {request.url.path}",
        exc_info=exc,
        extra={"path": request.url.path, "method": request.method}
    )
    
    # Handle our custom API exceptions
    if isinstance(exc, APIException):
        error_response = ErrorWrapper(error=ErrorResponse(
            code=exc.code.value,
            message=exc.message,
            details=exc.details or None,
        ))
        return JSONResponse(
            status_code=exc.status_code,
            content=jsonable_encoder(error_response),
        )
    
    # Handle unexpected exceptions
    error_response = ErrorWrapper(error=ErrorResponse(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        details={"error_id": str(uuid4())} if logger.isEnabledFor(logging.DEBUG) else None,
    ))
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder(error_response),
    )


async def request_logging_middleware(
    request: Request,
    call_next: Callable,
) -> JSONResponse:
    """
    Middleware for logging HTTP requests and responses.
    
    Logs:
      - Request method, path, query parameters
      - Response status code and processing time
      - Errors and exceptions
    """
    
    # Generate request ID for tracking
    request_id = str(uuid4())[:8]
    
    # Skip logging for health checks
    if request.url.path == "/api/health":
        return await call_next(request)
    
    start_time = time.time()
    
    # Log incoming request
    logger.info(
        f"→ {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client": request.client.host if request.client else "unknown",
        }
    )
    
    try:
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        status_emoji = "✅" if 200 <= response.status_code < 300 else (
            "⚠️" if 300 <= response.status_code < 400 else (
            "❌" if 400 <= response.status_code < 500 else
            "💥"
        ))
        
        logger.info(
            f"← {status_emoji} {request.method} {request.url.path} - "
            f"{response.status_code} ({process_time*1000:.0f}ms)",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time": process_time,
            }
        )
        
        # Warn if response is slow
        if process_time > 1.0:
            logger.warning(
                f"Slow response: {request.method} {request.url.path} "
                f"took {process_time:.2f}s",
                extra={"path": request.url.path, "duration": process_time}
            )
        
        return response
    
    except Exception as exc:
        process_time = time.time() - start_time
        logger.error(
            f"✗ {request.method} {request.url.path} failed after {process_time:.2f}s",
            exc_info=exc,
            extra={
                "request_id": request_id,
                "error": str(exc),
                "process_time": process_time,
            }
        )
        raise


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Register exception handlers with FastAPI app.
    
    Call this during app startup before adding routes.
    
    Example:
        >>> app = FastAPI()
        >>> setup_exception_handlers(app)
        >>> app.include_router(...)
    """
    
    # Handle all exceptions
    app.add_exception_handler(Exception, http_exception_handler)
    app.add_exception_handler(APIException, http_exception_handler)


def setup_middleware(app: FastAPI) -> None:
    """
    Register middleware with FastAPI app.
    
    Call this during app startup before adding routes.
    
    Example:
        >>> app = FastAPI()
        >>> setup_middleware(app)
        >>> app.include_router(...)
    """
    
    # Add request logging middleware
    app.middleware("http")(request_logging_middleware)
