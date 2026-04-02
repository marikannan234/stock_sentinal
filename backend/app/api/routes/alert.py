"""
Alert API routes for Stock Sentinel.

Provides endpoints for managing price alerts.

Endpoints:
  POST   /alerts                - Create new alert
  GET    /alerts                - Get all alerts for user
  GET    /alerts/{id}           - Get single alert
  DELETE /alerts/{id}           - Delete alert
  PATCH  /alerts/{id}           - Toggle alert status
  GET    /alerts/symbol/{symbol} - Get alerts for specific stock
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.core.exceptions import (
    AlertNotFoundError,
    AuthorizationError,
    DuplicateAlertError,
    InvalidAlertConditionError,
)
from app.models.user import User
from app.schemas.alert import AlertResponse, CreateAlertRequest, UpdateAlertRequest
from app.services.alert_service import AlertService

# Note: tags are applied in main.py's include_router() call to avoid duplication
router = APIRouter(prefix="/alerts")


# ============================================================================
# CREATE Alert
# ============================================================================


@router.post(
    "",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new alert",
    description="Create a new price alert for a stock. Prevents duplicate alerts.",
)
def create_alert(
    request: CreateAlertRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> AlertResponse:
    """
    Create a new stock price alert for the authenticated user.
    
    ** Schema Behavior:**
    - For PRICE alerts: condition is REQUIRED (>, <, >=, <=)
    - For other alert types: condition is OPTIONAL (omit it in the request)
    
    ** Alert Types:**
    - PRICE: Simple price threshold comparison (e.g., price > $100)
    - PERCENTAGE_CHANGE: Monitor % change from baseline (no condition needed)
    - VOLUME_SPIKE: Detect unusual volume spikes (no condition needed)
    - CRASH: Detect sudden price drops (no condition needed)
    
    **Request Body:**
    - `stock_symbol`: Stock ticker symbol (e.g., "AAPL"), will be converted to uppercase
    - `condition`: (ONLY for PRICE alerts) Price comparison operator (>, <, >=, <=)
    - `target_value`: Target value for comparison or trigger threshold (must be positive)
    - `alert_type`: (Optional) Type of alert (default: price)
    
    **Returns:** Created alert with ID and timestamps (201 Created)
    
    **Errors:**
    - 400: Invalid input (negative price, invalid symbol, invalid enum values, missing condition for PRICE, etc.)
    - 409: Duplicate alert already exists
    - 500: Server error processing alert
    
    **Examples:**
    
    1. PRICE alert (condition REQUIRED):
    ```json
    {
        "stock_symbol": "aapl",
        "alert_type": "price",
        "condition": ">",
        "target_value": 150.50
    }
    ```
    
    2. PERCENTAGE_CHANGE alert (condition NOT included):
    ```json
    {
        "stock_symbol": "aapl",
        "alert_type": "percentage_change",
        "target_value": 5.0
    }
    ```
    
    3. VOLUME_SPIKE alert (condition NOT included):
    ```json
    {
        "stock_symbol": "msft",
        "alert_type": "volume_spike",
        "target_value": 1.5
    }
    ```
    
    4. CRASH alert (condition NOT included):
    ```json
    {
        "stock_symbol": "googl",
        "alert_type": "crash",
        "target_value": 10.0
    }
    ```
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # ===== DIAGNOSTIC: Log incoming request =====
        logger.info(
            f"[ROUTE_DEBUG_1] Received alert creation request",
            extra={
                "request_dict": request.model_dump(),
                "alert_type_raw": request.alert_type,
                "alert_type_type": type(request.alert_type).__name__,
                "alert_type_value": getattr(request.alert_type, 'value', str(request.alert_type)),
            },
        )
        # ===== END DIAGNOSTIC =====
        
        logger.debug(
            f"Creating alert for user",
            extra={
                "user_id": current_user.id,
                "symbol": request.stock_symbol,
                "alert_type": getattr(request.alert_type, 'value', request.alert_type),
                "condition": getattr(request.condition, 'value', request.condition),
            },
        )
        
        service = AlertService(db)
        alert = service.create_alert(current_user, request)
        
        # ===== DIAGNOSTIC: Log returned alert object =====
        logger.info(
            f"[ROUTE_DEBUG_2] Alert created, returned from service",
            extra={
                "alert_id": alert.id,
                "alert_type_from_response": alert.alert_type,
                "alert_type_type": type(alert.alert_type).__name__ if alert.alert_type else "None",
            },
        )
        # ===== END DIAGNOSTIC =====
        
        logger.info(
            f"Alert created successfully via API",
            extra={
                "user_id": current_user.id,
                "alert_id": alert.id,
                "symbol": request.stock_symbol,
            },
        )
        
        return alert
    
    except DuplicateAlertError as e:
        logger.warning(
            f"Duplicate alert detected",
            extra={
                "user_id": current_user.id,
                "symbol": request.stock_symbol,
                "error": e.message,
            },
        )
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        )
    
    except InvalidAlertConditionError as e:
        logger.warning(
            f"Invalid alert condition",
            extra={
                "user_id": current_user.id,
                "condition": request.condition,
                "error": e.message,
            },
        )
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        )
    
    except ValueError as e:
        logger.warning(
            f"Validation error creating alert",
            extra={
                "user_id": current_user.id,
                "symbol": request.stock_symbol,
                "error": str(e),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input: {str(e)}",
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error creating alert",
            extra={
                "user_id": current_user.id,
                "symbol": request.stock_symbol,
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create alert: {str(e)}",
        )


# ============================================================================
# READ Alerts
# ============================================================================


@router.get(
    "",
    response_model=List[AlertResponse],
    summary="Get all alerts",
    description="Retrieve all alerts for the authenticated user.",
)
def get_all_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> List[AlertResponse]:
    """
    Get all alerts for the authenticated user.
    
    **Returns:** List of user's alerts, ordered by creation date (newest first)
    
    **Example Response:**
    ```json
    [
        {
            "id": 1,
            "user_id": 123,
            "stock_symbol": "AAPL",
            "condition": ">",
            "target_value": 150.50,
            "is_active": true,
            "created_at": "2024-01-15T10:30:00",
            "triggered_at": null
        }
    ]
    ```
    """
    service = AlertService(db)
    alerts = service.get_all_alerts_for_user(current_user)
    return alerts


@router.get(
    "/symbol/{symbol}",
    response_model=List[AlertResponse],
    summary="Get alerts for stock",
    description="Get all alerts for a specific stock symbol.",
)
def get_alerts_by_symbol(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> List[AlertResponse]:
    """
    Get all alerts for a specific stock symbol.
    
    **Path Parameters:**
    - `symbol`: Stock ticker symbol (e.g., "AAPL")
    
    **Returns:** List of alerts for the symbol, ordered by creation date
    
    **Example Response:**
    ```json
    [
        {
            "id": 1,
            "user_id": 123,
            "stock_symbol": "AAPL",
            "condition": ">",
            "target_value": 150.00,
            "is_active": true,
            "created_at": "2024-01-15T10:30:00",
            "triggered_at": null
        },
        {
            "id": 2,
            "user_id": 123,
            "stock_symbol": "AAPL",
            "condition": "<",
            "target_value": 140.00,
            "is_active": true,
            "created_at": "2024-01-15T11:00:00",
            "triggered_at": null
        }
    ]
    ```
    """
    service = AlertService(db)
    alerts = service.get_alerts_by_symbol(current_user, symbol)
    return alerts


@router.get(
    "/{alert_id}",
    response_model=AlertResponse,
    summary="Get single alert",
    description="Retrieve a specific alert by ID.",
)
def get_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> AlertResponse:
    """
    Get a specific alert by ID.
    
    **Path Parameters:**
    - `alert_id`: Alert unique identifier
    
    **Returns:** Alert details if it belongs to the authenticated user
    
    **Errors:**
    - 404: Alert not found
    - 403: Unauthorized (alert belongs to another user)
    """
    try:
        service = AlertService(db)
        alert = service.get_alert(current_user, alert_id)
        return alert
    except AlertNotFoundError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        )


# ============================================================================
# UPDATE Alert
# ============================================================================


@router.patch(
    "/{alert_id}",
    response_model=AlertResponse,
    summary="Toggle alert status",
    description="Enable or disable an alert.",
)
def update_alert(
    alert_id: int,
    request: UpdateAlertRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> AlertResponse:
    """
    Enable or disable an alert.
    
    **Path Parameters:**
    - `alert_id`: Alert unique identifier
    
    **Request Body:**
    - `is_active`: Boolean flag to enable (true) or disable (false) the alert
    
    **Returns:** Updated alert
    
    **Errors:**
    - 404: Alert not found
    - 403: Unauthorized (alert belongs to another user)
    
    **Example:**
    ```json
    {
        "is_active": false
    }
    ```
    """
    try:
        service = AlertService(db)
        alert = service.update_alert_status(current_user, alert_id, request)
        return alert
    except AlertNotFoundError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        )


# ============================================================================
# DELETE Alert
# ============================================================================


@router.delete(
    "/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete alert",
    description="Delete an alert permanently.",
)
def delete_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> None:
    """
    Delete an alert permanently.
    
    **Path Parameters:**
    - `alert_id`: Alert unique identifier
    
    **Returns:** 204 No Content (success with no body)
    
    **Errors:**
    - 404: Alert not found
    - 403: Unauthorized (alert belongs to another user)
    """
    try:
        service = AlertService(db)
        service.delete_alert(current_user, alert_id)
    except AlertNotFoundError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        )
