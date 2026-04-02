"""
Example route demonstrating proper error handling and logging.

This file shows best practices for:
  - Validating inputs
  - Catching exceptions
  - Returning consistent error responses
  - Logging important events
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field, field_validator

from app.api.deps import get_current_user
from app.models.user import User
from app.core.exceptions import (
    StockNotFoundError,
    InvalidTickerError,
    ValidationError,
    ExternalAPIError,
)


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/example", tags=["example"])


# ============================================
# Request/Response Models
# ============================================

class ExampleStockRequest(BaseModel):
    """Request body for getting stock example."""
    
    ticker: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Stock ticker symbol (e.g., RELIANCE, INFY)"
    )
    
    @field_validator('ticker')
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        """Validate ticker format."""
        v = v.strip().upper()
        
        # Check if ticker contains only alphanumeric and hyphens
        if not v.isalnum() and not all(c.isalnum() or c == '-' for c in v):
            raise ValueError("Ticker must contain only letters, numbers, and hyphens")
        
        return v


class StockExampleResponse(BaseModel):
    """Response model for stock example."""
    
    ticker: str = Field(..., description="Stock ticker")
    price: float = Field(..., gt=0, description="Current stock price")
    message: str = Field(..., description="Success message")


# ============================================
# Route Examples
# ============================================

@router.get(
    "/stock/{ticker}/simple",
    response_model=StockExampleResponse,
    summary="Get basic stock information",
    description="Demonstrates basic error handling and logging"
)
async def get_stock_simple(
    ticker: str = Field(..., min_length=1, max_length=10),
    current_user: User = Depends(get_current_user),
) -> StockExampleResponse:
    """
    Get basic stock information.
    
    This endpoint demonstrates:
      - Input validation
      - Exception handling
      - Proper logging
      - Consistent error responses
    
    Raises:
      - InvalidTickerError: If ticker format is invalid
      - StockNotFoundError: If stock not found
      - ExternalAPIError: If external API fails
    """
    
    # 1. Validate ticker
    ticker = ticker.strip().upper()
    logger.info(f"Fetching stock info for {ticker}", extra={"ticker": ticker})
    
    if not ticker or len(ticker) > 10:
        raise InvalidTickerError(ticker)
    
    try:
        # 2. Simulate stock data fetching (replace with actual API call)
        logger.debug(f"Querying database for {ticker}")
        
        # Example: Simulate not found error
        if ticker == "INVALID":
            logger.warning(f"Stock not found: {ticker}")
            raise StockNotFoundError(ticker)
        
        # Example: Simulate API error
        if ticker == "API_ERROR":
            logger.error(f"External API failed for {ticker}")
            raise ExternalAPIError(
                message=f"Failed to fetch data for {ticker}",
                details={"service": "yfinance", "status_code": 503}
            )
        
        # 3. Success case
        logger.info(f"Successfully fetched {ticker}", extra={"ticker": ticker})
        
        return StockExampleResponse(
            ticker=ticker,
            price=2850.50,
            message=f"Retrieved data for {ticker}"
        )
    
    except (StockNotFoundError, InvalidTickerError, ExternalAPIError):
        # Re-raise our custom exceptions (will be caught by global handler)
        raise
    
    except Exception as exc:
        # Catch unexpected exceptions and log them
        logger.error(
            f"Unexpected error fetching {ticker}: {str(exc)}",
            exc_info=exc,
            extra={"ticker": ticker}
        )
        raise ExternalAPIError(
            message=f"Failed to fetch data for {ticker}",
            details={"error": str(exc)}
        )


@router.post(
    "/stock/validate",
    response_model=dict,
    summary="Validate stock ticker",
    description="Demonstrates request validation"
)
async def validate_stock(
    request: ExampleStockRequest,
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Validate stock ticker.
    
    This endpoint demonstrates:
      - Pydantic model validation
      - Field validators
      - Error details in response
    
    Returns:
      - Validation result
    """
    
    logger.info(f"Validating ticker: {request.ticker}")
    
    # Validation happens automatically via Pydantic
    # If invalid, returns 422 with validation errors
    
    return {
        "valid": True,
        "ticker": request.ticker,
        "message": f"Ticker {request.ticker} is valid"
    }


@router.get(
    "/stock/{ticker}/with-retry",
    response_model=StockExampleResponse,
    summary="Get stock with retry logic",
    description="Demonstrates error recovery and retry logic"
)
async def get_stock_with_retry(
    ticker: str,
    max_retries: int = Query(default=3, ge=1, le=5),
    current_user: User = Depends(get_current_user),
) -> StockExampleResponse:
    """
    Get stock information with automatic retry.
    
    This endpoint demonstrates:
      - Retry logic
      - Graceful degradation
      - Detailed error logging
    
    Args:
      - ticker: Stock ticker symbol
      - max_retries: Maximum retry attempts (1-5)
    """
    
    ticker = ticker.strip().upper()
    logger.info(f"Fetching {ticker} with retry (max_retries={max_retries})")
    
    last_error = None
    
    # Retry logic
    for attempt in range(1, max_retries + 1):
        try:
            logger.debug(f"Attempt {attempt}/{max_retries} for {ticker}")
            
            if ticker == "INVALID":
                raise StockNotFoundError(ticker)
            
            logger.info(f"Successfully fetched {ticker} on attempt {attempt}")
            
            return StockExampleResponse(
                ticker=ticker,
                price=2850.50,
                message=f"Retrieved after {attempt} attempt(s)"
            )
        
        except StockNotFoundError:
            # Don't retry for validation errors
            raise
        
        except Exception as exc:
            last_error = exc
            logger.warning(
                f"Attempt {attempt} failed for {ticker}: {str(exc)}",
                extra={"ticker": ticker, "attempt": attempt}
            )
            
            if attempt < max_retries:
                # Log retry
                logger.info(f"Retrying {ticker}...")
                continue
    
    # All retries failed
    logger.error(f"All {max_retries} attempts failed for {ticker}")
    raise ExternalAPIError(
        message=f"Failed to fetch {ticker} after {max_retries} attempts",
        details={"last_error": str(last_error), "attempts": max_retries}
    )


@router.delete(
    "/stock/{ticker}",
    response_model=dict,
    summary="Delete stock from watchlist",
    description="Demonstrates successful deletion logging"
)
async def delete_stock(
    ticker: str,
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Delete stock from watchlist.
    
    This endpoint demonstrates:
      - Logging successful operations
      - Audit trails
      - User action tracking
    """
    
    ticker = ticker.strip().upper()
    
    logger.info(
        f"Deleting {ticker} from watchlist",
        extra={
            "ticker": ticker,
            "user_id": current_user.id,
            "action": "delete"
        }
    )
    
    # Simulate deletion
    logger.info(
        f"Successfully deleted {ticker}",
        extra={"ticker": ticker, "status": "deleted"}
    )
    
    return {
        "success": True,
        "ticker": ticker,
        "message": f"Deleted {ticker} from watchlist"
    }


# ============================================
# Error Handling Best Practices
# ============================================

"""
Error Handling Patterns:

1. Input Validation Errors (400):
   ✓ Use ValidationError or specific subclass
   ✓ Log at INFO level with details
   ✓ Include field names in response

2. Resource Not Found (404):
   ✓ Use StockNotFoundError or NotFoundError
   ✓ Log at INFO level with resource ID
   ✓ Include resource identifier in response

3. Authentication/Authorization (401/403):
   ✓ Use AuthenticationError or AuthorizationError
   ✓ Log at WARNING level (security sensitive)
   ✓ Don't include sensitive details in response

4. External API Failures (502):
   ✓ Use ExternalAPIError
   ✓ Log at ERROR level with service name
   ✓ Include retry info if applicable

5. Database Errors (500):
   ✓ Use DatabaseError
   ✓ Log at ERROR level with context
   ✓ Don't expose internal SQL details

6. Unexpected Errors (500):
   ✓ Log at CRITICAL level with stack trace
   ✓ Return generic error to user
   ✓ Include error tracking ID for support

Logging Levels Guide:
  - DEBUG: Detailed trace info (very verbose)
  - INFO: Confirmatory/audit events (normal operations)
  - WARNING: Warning conditions that need attention
  - ERROR: Error conditions (failures, retries)
  - CRITICAL: Critical errors (app may crash)
"""
