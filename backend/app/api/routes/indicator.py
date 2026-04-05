"""
Technical Indicators API Routes

Endpoints for technical indicator calculations:
- GET /api/indicators/sma - Simple Moving Average
- GET /api/indicators/rsi - Relative Strength Index
- GET /api/indicators/ema - Exponential Moving Average
"""

import logging
from fastapi import APIRouter, HTTPException, Query

from app.core.exceptions import ValidationError, StockNotFoundError
from app.schemas.indicator import SMAResponse, RSIResponse, EMAResponse
from app.services.indicator_service import calculate_sma, calculate_rsi, calculate_ema

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", summary="Indicators overview")
def get_indicator_overview() -> dict:
    """Return indicator endpoint metadata with safe defaults for frontend integration."""
    logger.info("Indicators overview requested")
    return {
        "default_symbol": "AAPL",
        "available_endpoints": ["sma", "ema", "rsi", "combined"],
        "defaults": {"sma_period": 14, "ema_period": 20, "rsi_period": 14},
    }


@router.get(
    "/sma",
    response_model=SMAResponse,
    summary="Calculate Simple Moving Average",
    description="Calculate the Simple Moving Average (SMA) for a given stock symbol.",
)
def get_sma(
    symbol: str = Query(
        default="AAPL",
        min_length=1,
        max_length=10,
        description="Stock ticker symbol (e.g., AAPL, MSFT)"
    ),
    period: int = Query(
        default=14,
        ge=2,
        le=500,
        description="SMA period in days (2-500, default: 14)"
    ),
) -> SMAResponse:
    """
    Calculate Simple Moving Average for a stock symbol.
    
    Args:
        symbol: Stock ticker symbol (e.g., AAPL)
        period: Number of days for SMA calculation (default: 14)
    
    Returns:
        SMAResponse with symbol, period, SMA value, and current price
    
    Raises:
        HTTPException 400: Invalid parameters
        HTTPException 404: Symbol not found
        HTTPException 500: Server error
    """
    try:
        logger.info(f"SMA request - symbol: {symbol}, period: {period}")
        
        # Call service layer
        result = calculate_sma(
            symbol=symbol.upper(),
            period=period
        )
        
        logger.info(f"SMA calculated - symbol: {symbol}, sma: {result['sma']}")
        
        return SMAResponse(**result)
    
    except StockNotFoundError as e:
        logger.warning(f"Stock not found - symbol: {symbol}")
        raise HTTPException(
            status_code=404,
            detail={"error": "StockNotFound", "message": str(e)}
        )
    
    except ValidationError as e:
        logger.warning(f"Validation error - symbol: {symbol}, error: {e.message}")
        raise HTTPException(
            status_code=400,
            detail={"error": "InvalidParameter", "message": e.message}
        )
    
    except Exception as e:
        logger.error(f"Unexpected error - symbol: {symbol}, error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalServerError", "message": "An unexpected error occurred"}
        )


@router.get(
    "/rsi",
    response_model=RSIResponse,
    summary="Calculate Relative Strength Index",
    description="Calculate the Relative Strength Index (RSI) for a given stock symbol.",
)
def get_rsi(
    symbol: str = Query(
        default="AAPL",
        min_length=1,
        max_length=10,
        description="Stock ticker symbol (e.g., AAPL, MSFT)"
    ),
    period: int = Query(
        default=14,
        ge=2,
        le=100,
        description="RSI period in days (2-100, default: 14)"
    ),
) -> RSIResponse:
    """
    Calculate Relative Strength Index for a stock symbol.
    
    RSI ranges from 0 to 100:
    - RSI > 70: Overbought (potential sell signal)
    - RSI < 30: Oversold (potential buy signal)
    - 30-70: Neutral zone
    
    Args:
        symbol: Stock ticker symbol (e.g., AAPL)
        period: Number of days for RSI calculation (default: 14)
    
    Returns:
        RSIResponse with symbol, period, RSI value, and current price
    
    Raises:
        HTTPException 400: Invalid parameters
        HTTPException 404: Symbol not found
        HTTPException 500: Server error
    """
    try:
        logger.info(f"RSI request - symbol: {symbol}, period: {period}")
        
        # Call service layer
        result = calculate_rsi(
            symbol=symbol.upper(),
            period=period
        )
        
        logger.info(f"RSI calculated - symbol: {symbol}, rsi: {result['rsi']}")
        
        return RSIResponse(**result)
    
    except StockNotFoundError as e:
        logger.warning(f"Stock not found - symbol: {symbol}")
        raise HTTPException(
            status_code=404,
            detail={"error": "StockNotFound", "message": str(e)}
        )
    
    except ValidationError as e:
        logger.warning(f"Validation error - symbol: {symbol}, error: {e.message}")
        raise HTTPException(
            status_code=400,
            detail={"error": "InvalidParameter", "message": e.message}
        )
    
    except Exception as e:
        logger.error(f"Unexpected error - symbol: {symbol}, error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalServerError", "message": "An unexpected error occurred"}
        )


@router.get(
    "/ema",
    response_model=EMAResponse,
    summary="Calculate Exponential Moving Average",
    description="Calculate the Exponential Moving Average (EMA) for a given stock symbol.",
)
def get_ema(
    symbol: str = Query(
        default="AAPL",
        min_length=1,
        max_length=10,
        description="Stock ticker symbol (e.g., AAPL, MSFT)"
    ),
    period: int = Query(
        default=20,
        ge=2,
        le=500,
        description="EMA period in days (2-500, default: 20)"
    ),
) -> EMAResponse:
    """
    Calculate Exponential Moving Average for a stock symbol.
    
    EMA gives more weight to recent prices, making it more responsive to price changes.
    
    Args:
        symbol: Stock ticker symbol (e.g., AAPL)
        period: Number of days for EMA calculation (default: 20)
    
    Returns:
        EMAResponse with symbol, period, EMA value, and current price
    
    Raises:
        HTTPException 400: Invalid parameters
        HTTPException 404: Symbol not found
        HTTPException 500: Server error
    """
    try:
        logger.info(f"EMA request - symbol: {symbol}, period: {period}")
        
        # Call service layer
        result = calculate_ema(
            symbol=symbol.upper(),
            period=period
        )
        
        logger.info(f"EMA calculated - symbol: {symbol}, ema: {result['ema']}")
        
        return EMAResponse(**result)
    
    except StockNotFoundError as e:
        logger.warning(f"Stock not found - symbol: {symbol}")
        raise HTTPException(
            status_code=404,
            detail={"error": "StockNotFound", "message": str(e)}
        )
    
    except ValidationError as e:
        logger.warning(f"Validation error - symbol: {symbol}, error: {e.message}")
        raise HTTPException(
            status_code=400,
            detail={"error": "InvalidParameter", "message": e.message}
        )
    
    except Exception as e:
        logger.error(f"Unexpected error - symbol: {symbol}, error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalServerError", "message": "An unexpected error occurred"}
        )


@router.get("/combined", summary="Get combined technical indicators")
def get_combined_indicators(
    symbol: str = Query(
        default="AAPL",
        min_length=1,
        max_length=10,
        description="Stock ticker symbol (e.g., AAPL, MSFT)"
    ),
) -> dict:
    """Return SMA, EMA, and RSI in a single response for the frontend dashboard."""
    normalized_symbol = symbol.upper()
    logger.info(f"Combined indicators request - symbol: {normalized_symbol}")
    try:
        return {
            "symbol": normalized_symbol,
            "sma": calculate_sma(symbol=normalized_symbol, period=14),
            "ema": calculate_ema(symbol=normalized_symbol, period=20),
            "rsi": calculate_rsi(symbol=normalized_symbol, period=14),
        }
    except StockNotFoundError as e:
        logger.warning(f"Stock not found for combined indicators - symbol: {normalized_symbol}")
        raise HTTPException(
            status_code=404,
            detail={"error": "StockNotFound", "message": str(e)}
        )
    except ValidationError as e:
        logger.warning(f"Validation error for combined indicators - symbol: {normalized_symbol}, error: {e.message}")
        raise HTTPException(
            status_code=400,
            detail={"error": "InvalidParameter", "message": e.message}
        )
    except Exception as e:
        logger.error(f"Unexpected combined indicators error - symbol: {normalized_symbol}, error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalServerError", "message": "An unexpected error occurred"}
        )
