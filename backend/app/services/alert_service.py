"""
Alert service module for Stock Sentinel.

Provides business logic for alert management and price monitoring.
Handles:
  - Alert CRUD operations
  - Stock price fetching
  - Alert condition checking
  - Alert triggering and logging
  - Email notifications for triggered alerts
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, cast

import httpx
import yfinance as yf
from sqlalchemy.orm import Session

from app.core.exceptions import (
    AlertNotFoundError,
    AuthorizationError,
    DuplicateAlertError,
    InvalidAlertConditionError,
)
from app.config import settings
from app.models.alert import Alert, AlertCondition
from app.models.user import User
from app.schemas.alert import AlertResponse, CreateAlertRequest, UpdateAlertRequest

logger = logging.getLogger(__name__)


# ============================================================================
# Helper Functions for Async Operations from Sync Context
# ============================================================================

def send_alert_email_async(
    user_email: str,
    symbol: str,
    current_price: float,
    condition: str,
    target_value: float,
    triggered_at: str,
) -> None:
    """
    Send alert triggered email notification asynchronously from sync context.
    
    Since the scheduler runs synchronously, we need to handle async email sending
    carefully. This function attempts to run the async email function without
    blocking the scheduler.
    
    Args:
        user_email: User's email address
        symbol: Stock symbol
        current_price: Current stock price
        condition: Alert condition (e.g., ">", "<")
        target_value: Target price value
        triggered_at: When alert was triggered (ISO format string)
    """
    try:
        # Try to get existing event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No event loop in current thread, create new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Import here to avoid circular imports
        from app.services.email_service import send_alert_triggered_email
        
        # Create coroutine
        coro = send_alert_triggered_email(
            to_email=user_email,
            symbol=symbol,
            current_price=current_price,
            condition=condition,
            target_value=target_value,
            triggered_at=triggered_at,
        )
        
        # Try to run using the current loop if it's running
        # If loop is already running (in async context), schedule as task
        if loop.is_running():
            asyncio.create_task(coro)
        else:
            # If loop is not running, run until complete
            loop.run_until_complete(coro)
        
        logger.debug(
            f"Alert email scheduled for async sending",
            extra={"user_email": user_email, "symbol": symbol},
        )
        
    except Exception as e:
        logger.error(
            f"Failed to schedule alert email",
            extra={
                "user_email": user_email,
                "symbol": symbol,
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )

class AlertService:
    """Service for managing stock price alerts."""
    
    def __init__(self, db: Session):
        """
        Initialize alert service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    # ========================================================================
    # CRUD Operations
    # ========================================================================
    
    def create_alert(self, user: User, request: CreateAlertRequest) -> AlertResponse:
        """
        Create a new alert for a user.
        
        Supports multiple alert types:
        - PRICE: Simple price threshold comparison (requires condition)
        - PERCENTAGE_CHANGE: Monitor percentage change from last price (no condition needed)
        - VOLUME_SPIKE: Detect unusual volume spikes (no condition needed)
        - CRASH: Detect sudden price drops (no condition needed)
        - CUSTOM: Custom conditions (condition optional)
        
        Args:
            user: Authenticated user
            request: Alert creation request (includes alert_type)
            
        Returns:
            AlertResponse with created alert data
            
        Raises:
            DuplicateAlertError: If alert with same conditions already exists
            InvalidAlertConditionError: If condition is invalid for PRICE alerts
        """
        try:
            # Get alert type from request (defaults to PRICE)
            from app.models.alert import AlertType
            
            if not isinstance(request.alert_type, AlertType):
                logger.error(
                    f"Invalid alert_type",
                    extra={
                        "alert_type": request.alert_type,
                        "type": type(request.alert_type).__name__,
                    },
                )
                raise ValueError(
                    f"Invalid alert_type. Must be one of: {', '.join([t.value for t in AlertType])}"
                )
            alert_type = request.alert_type or AlertType.PRICE
            
            # Validate condition based on alert type
            # PRICE alerts require a condition
            # Other alert types don't need condition (optional)
            if alert_type == AlertType.PRICE:
                if request.condition is None:
                    raise InvalidAlertConditionError(
                        "<None>",
                        [c.value for c in AlertCondition],
                    )
                if not isinstance(request.condition, AlertCondition):
                    logger.error(
                        f"Invalid condition type for PRICE alert",
                        extra={
                            "condition": request.condition,
                            "type": type(request.condition).__name__,
                        },
                    )
                    raise InvalidAlertConditionError(
                        str(request.condition),
                        [c.value for c in AlertCondition],
                    )
            
            condition = request.condition
            
            logger.debug(
                f"Creating alert with normalized values",
                extra={
                    "user_id": user.id,
                    "symbol": request.stock_symbol,
                    "alert_type": alert_type.value,
                    "condition": condition.value if condition else None,
                    "target_value": request.target_value,
                },
            )
            
            # ===== DIAGNOSTIC LOGGING =====
            # Log alert_type immediately before DB insert to diagnose NULL issue
            logger.info(
                f"[ALERT_CREATE_DEBUG] About to insert alert with following values:",
                extra={
                    "alert_type": alert_type,
                    "alert_type_value": alert_type.value if alert_type else "NONE",
                    "alert_type_type": type(alert_type).__name__,
                    "is_alert_type_none": alert_type is None,
                    "user_id": user.id,
                    "stock_symbol": request.stock_symbol,
                    "condition": condition,
                    "target_value": request.target_value,
                },
            )
            # ===== END DIAGNOSTIC LOGGING =====
            
            # Check for duplicate alert (including alert_type and condition in uniqueness check)
            existing_alert = self.db.query(Alert).filter(
                Alert.user_id == user.id,
                Alert.stock_symbol == request.stock_symbol,
                Alert.alert_type == alert_type,
                Alert.condition == condition,
                Alert.target_value == request.target_value,
            ).first()
            
            if existing_alert:
                logger.warning(
                    f"Duplicate alert detected",
                    extra={
                        "user_id": user.id,
                        "alert_id": existing_alert.id,
                        "symbol": request.stock_symbol,
                        "alert_type": alert_type.value,
                    },
                )
                raise DuplicateAlertError(
                    request.stock_symbol,
                    condition.value if condition else "N/A",
                    request.target_value,
                )
            
            # Create new alert
            alert = Alert(
                user_id=user.id,
                stock_symbol=request.stock_symbol,
                condition=condition,
                target_value=request.target_value,
                alert_type=alert_type,
                is_active=True,
                last_price=None,  # Will be populated on first check
            )
            
            # === DIAGNOSTIC: Detailed logging before commit ===
            logger.info(
                f"[SERVICE_DEBUG_1] Alert object constructed, BEFORE adding to session",
                extra={
                    "alert.id": alert.id,
                    "alert.user_id": alert.user_id,
                    "alert.stock_symbol": alert.stock_symbol,
                    "alert.alert_type": alert.alert_type,
                    "alert.alert_type_type": type(alert.alert_type).__name__,
                    "alert.alert_type_is_none": alert.alert_type is None,
                    "alert.condition": alert.condition,
                    "alert.target_value": alert.target_value,
                    "alert.is_active": alert.is_active,
                },
            )
            # === END DIAGNOSTIC ===
            
            self.db.add(alert)
            
            logger.info(
                f"[SERVICE_DEBUG_2] Alert added to session, BEFORE commit",
                extra={
                    "alert.alert_type": alert.alert_type,
                    "session_new_count": len(self.db.new),
                },
            )
            
            self.db.commit()
            
            logger.info(
                f"[SERVICE_DEBUG_3] AFTER commit to database",
                extra={
                    "alert.id": alert.id,
                    "alert.alert_type": alert.alert_type,
                    "alert.alert_type_type": type(alert.alert_type).__name__,
                },
            )
            
            self.db.refresh(alert)
            
            logger.info(
                f"[SERVICE_DEBUG_4] AFTER refresh from database",
                extra={
                    "alert.id": alert.id,
                    "alert.alert_type": alert.alert_type,
                    "alert.alert_type_type": type(alert.alert_type).__name__,
                },
            )
            
            logger.info(
                f"Alert created successfully",
                extra={
                    "user_id": user.id,
                    "alert_id": alert.id,
                    "symbol": request.stock_symbol,
                    "alert_type": alert_type.value,
                    "condition": condition.value if condition else None,
                    "target_value": request.target_value,
                },
            )
            
            return AlertResponse.from_orm(alert)
        
        except (DuplicateAlertError, InvalidAlertConditionError):
            # Re-raise custom exceptions
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error creating alert",
                extra={
                    "user_id": user.id,
                    "symbol": request.stock_symbol,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            raise
    
    def get_alert(self, user: User, alert_id: int) -> AlertResponse:
        """
        Get a single alert by ID.
        
        Args:
            user: Authenticated user
            alert_id: Alert ID
            
        Returns:
            AlertResponse
            
        Raises:
            AlertNotFoundError: If alert doesn't exist
            AuthorizationError: If user doesn't own the alert
        """
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        
        if not alert:
            raise AlertNotFoundError(alert_id)
        
        if alert.user_id != user.id:
            raise AuthorizationError(
                message=f"You don't have permission to access alert {alert_id}"
            )
        
        return AlertResponse.from_orm(alert)
    
    def get_all_alerts_for_user(self, user: User) -> list[AlertResponse]:
        """
        Get all alerts for a specific user.
        
        Args:
            user: Authenticated user
            
        Returns:
            List of AlertResponse objects
        """
        alerts = self.db.query(Alert).filter(
            Alert.user_id == user.id
        ).order_by(Alert.created_at.desc()).all()
        
        return [AlertResponse.from_orm(alert) for alert in alerts]
    
    def get_active_alerts_for_user(self, user: User) -> list[AlertResponse]:
        """
        Get all active alerts for a user.
        
        Args:
            user: Authenticated user
            
        Returns:
            List of active AlertResponse objects
        """
        alerts = self.db.query(Alert).filter(
            Alert.user_id == user.id,
            Alert.is_active == True,
        ).all()
        
        return [AlertResponse.from_orm(alert) for alert in alerts]
    
    def get_alerts_by_symbol(self, user: User, symbol: str) -> list[AlertResponse]:
        """
        Get all alerts for a specific stock symbol.
        
        Args:
            user: Authenticated user
            symbol: Stock symbol
            
        Returns:
            List of AlertResponse objects for that symbol
        """
        alerts = self.db.query(Alert).filter(
            Alert.user_id == user.id,
            Alert.stock_symbol == symbol.upper(),
        ).order_by(Alert.created_at.desc()).all()
        
        return [AlertResponse.from_orm(alert) for alert in alerts]
    
    def delete_alert(self, user: User, alert_id: int) -> None:
        """
        Delete an alert.
        
        Args:
            user: Authenticated user
            alert_id: Alert ID to delete
            
        Raises:
            AlertNotFoundError: If alert doesn't exist
            AuthorizationError: If user doesn't own the alert
        """
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        
        if not alert:
            raise AlertNotFoundError(alert_id)
        
        if alert.user_id != user.id:
            raise AuthorizationError(
                message=f"You don't have permission to delete alert {alert_id}"
            )
        
        self.db.delete(alert)
        self.db.commit()
        
        logger.info(
            f"Alert deleted successfully",
            extra={
                "user_id": user.id,
                "alert_id": alert_id,
            },
        )
    
    def update_alert_status(
        self,
        user: User,
        alert_id: int,
        request: UpdateAlertRequest,
    ) -> AlertResponse:
        """
        Update alert active status (enable/disable).
        
        Args:
            user: Authenticated user
            alert_id: Alert ID to update
            request: Update request with new status
            
        Returns:
            Updated AlertResponse
            
        Raises:
            AlertNotFoundError: If alert doesn't exist
            AuthorizationError: If user doesn't own the alert
        """
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        
        if not alert:
            raise AlertNotFoundError(alert_id)
        
        if alert.user_id != user.id:
            raise AuthorizationError(
                message=f"You don't have permission to update alert {alert_id}"
            )
        
        alert.is_active = request.is_active
        self.db.commit()
        self.db.refresh(alert)
        
        status = "enabled" if request.is_active else "disabled"
        logger.info(
            f"Alert {status} successfully",
            extra={
                "user_id": user.id,
                "alert_id": alert_id,
                "is_active": request.is_active,
            },
        )
        
        return AlertResponse.from_orm(alert)
    
    # ========================================================================
    # Stock Price Fetching
    # ========================================================================
    
    @staticmethod
    async def fetch_stock_price(symbol: str, timeout: int = 10) -> Optional[float]:
        """
        Fetch current stock price using yfinance.
        
        Falls back to httpx for HTTP requests if needed.
        
        Args:
            symbol: Stock ticker symbol
            timeout: Request timeout in seconds
            
        Returns:
            Current stock price or None if fetch fails
        """
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period="1d")
            
            if data.empty:
                logger.warning(
                    f"No price data available for symbol",
                    extra={"symbol": symbol},
                )
                return None
            
            current_price = float(data["Close"].iloc[-1])
            logger.debug(
                f"Stock price fetched successfully",
                extra={"symbol": symbol, "price": current_price},
            )
            
            return current_price
            
        except Exception as e:
            logger.error(
                f"Failed to fetch stock price",
                extra={
                    "symbol": symbol,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            return None
    
    @staticmethod
    async def fetch_stock_price_with_httpx(
        symbol: str,
        timeout: int = 10,
    ) -> Optional[float]:
        """
        Fetch stock price using httpx and a free API endpoint.
        
        Fallback method if yfinance fails.
        
        Args:
            symbol: Stock ticker symbol
            timeout: Request timeout in seconds
            
        Returns:
            Current stock price or None if fetch fails
        """
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                # Using Alpha Vantage free API as example
                # Replace with your preferred API
                response = await client.get(
                    "https://www.alphavantage.co/query",
                    params={
                        "function": "GLOBAL_QUOTE",
                        "symbol": symbol,
                        "apikey": "demo",
                    },
                )
                response.raise_for_status()
                
                data = response.json()
                if "Global Quote" in data:
                    price_str = data["Global Quote"].get("05. price")
                    if price_str:
                        current_price = float(price_str)
                        logger.debug(
                            f"Stock price fetched via httpx",
                            extra={"symbol": symbol, "price": current_price},
                        )
                        return current_price
                
                logger.warning(
                    f"Invalid response format from API",
                    extra={"symbol": symbol, "response": data},
                )
                return None
                
        except Exception as e:
            logger.error(
                f"Failed to fetch stock price via httpx",
                extra={
                    "symbol": symbol,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            return None
    
    # ========================================================================
    # Alert Checking Logic
    # ========================================================================
    
    async def check_alert(
        self,
        alert: Alert,
        current_price: float,
        previous_price: Optional[float] = None,
    ) -> bool:
        """
        Check if alert condition is met and trigger if necessary.
        
        Args:
            alert: Alert to check
            current_price: Current stock price
            previous_price: Previous stock price (for percentage_change)
            
        Returns:
            True if alert was triggered, False otherwise
        """
        if not alert.is_active:
            return False
        
        try:
            # Check if condition matches
            condition_met = alert.matches_condition(current_price, previous_price)
            
            if condition_met and alert.triggered_at is None:
                # Mark as triggered
                alert.triggered_at = datetime.utcnow()
                self.db.commit()
                
                logger.info(
                    f"Alert triggered successfully",
                    extra={
                        "alert_id": alert.id,
                        "user_id": alert.user_id,
                        "symbol": alert.stock_symbol,
                        "condition": alert.condition.value if alert.condition else None,
                        "target_value": alert.target_value,
                        "current_price": current_price,
                    },
                )
                
                return True
            
            return condition_met and alert.triggered_at is not None
            
        except ValueError as e:
            logger.error(
                f"Error checking alert condition",
                extra={
                    "alert_id": alert.id,
                    "error": str(e),
                },
            )
            return False
    
    async def check_all_user_alerts(
        self,
        user: User,
    ) -> dict[int, bool]:
        """
        Check all active alerts for a user and trigger if necessary.
        
        Args:
            user: User whose alerts to check
            
        Returns:
            Dictionary mapping alert_id to whether it was triggered
        """
        alerts = self.db.query(Alert).filter(
            Alert.user_id == user.id,
            Alert.is_active == True,
        ).all()
        
        results = {}
        
        # Group alerts by symbol for efficient price fetching
        symbols = set(alert.stock_symbol for alert in alerts)
        prices = {}
        
        for symbol in symbols:
            price = await self.fetch_stock_price(symbol)
            if price:
                prices[symbol] = price
        
        # Check each alert
        for alert in alerts:
            if alert.stock_symbol in prices:
                current_price = prices[alert.stock_symbol]
                triggered = await self.check_alert(alert, current_price)
                results[alert.id] = triggered
            else:
                results[alert.id] = False
        
        logger.info(
            f"Completed alert check for user",
            extra={
                "user_id": user.id,
                "total_alerts": len(alerts),
                "triggered": sum(results.values()),
            },
        )
        
        return results
    
    async def check_all_alerts_for_symbol(
        self,
        symbol: str,
    ) -> dict[int, bool]:
        """
        Check all active alerts for a specific stock symbol.
        
        Useful for batch processing after price updates.
        
        Args:
            symbol: Stock symbol to check
            
        Returns:
            Dictionary mapping alert_id to whether it was triggered
        """
        alerts = self.db.query(Alert).filter(
            Alert.stock_symbol == symbol.upper(),
            Alert.is_active == True,
        ).all()
        
        results = {}
        current_price = await self.fetch_stock_price(symbol)
        
        if not current_price:
            logger.warning(
                f"Could not fetch price for symbol check",
                extra={"symbol": symbol, "alerts_count": len(alerts)},
            )
            return {alert.id: False for alert in alerts}
        
        for alert in alerts:
            triggered = await self.check_alert(alert, current_price)
            results[alert.id] = triggered
        
        logger.info(
            f"Completed alert check for symbol",
            extra={
                "symbol": symbol,
                "total_alerts": len(alerts),
                "triggered": sum(results.values()),
            },
        )
        
        return results


# ============================================================================
# Standalone Functions for Background Scheduler
# ============================================================================

def trigger_alert(db: Session, alert: Alert, current_price: float) -> bool:
    """
    Trigger an alert by marking it as inactive and setting triggered_at timestamp.
    
    This function is called when an alert condition is matched.
    It updates the alert in the database atomically, records alert history, and sends email notification.
    
    Production enhancements:
    - Sets is_triggered = True (prevents duplicate emails within cooldown period)
    - Records is_triggered not for 10-minute cooldown before re-arming
    - Creates AlertHistory entry for complete audit trail
    - Sends email with comprehensive alert details
    
    Args:
        db: Database session
        alert: Alert to trigger
        current_price: Current stock price that matched the condition
        
    Returns:
        True if alert was triggered successfully, False if already triggered
    """
    try:
        from app.models.alert import AlertHistory
        
        # Prevent duplicate triggers - check if already triggered recently (cooldown check)
        if not alert.is_active:
            logger.debug(
                f"Alert already triggered, skipping",
                extra={"alert_id": alert.id},
            )
            return False
        
        now = datetime.utcnow()
        
        # Mark alert as triggered and inactive
        alert.is_active = False
        alert.triggered_at = now
        alert.is_triggered = True  # NEW: Mark as triggered for cooldown period
        alert.last_triggered_at = now  # NEW: Record trigger timestamp for cooldown
        
        # Safe cast - we just assigned triggered_at above
        triggered_at_str = cast(datetime, alert.triggered_at).isoformat()
        
        # Prepare alert history entry (NEW: Complete audit trail)
        history_entry = AlertHistory(
            alert_id=alert.id,
            user_id=alert.user_id,
            triggered_at=now,
            stock_symbol=alert.stock_symbol,
            alert_type=alert.alert_type.value,
            price_at_trigger=current_price,
            target_value=alert.target_value,
            condition=alert.condition.value if alert.condition else None,
            message=f"Alert triggered: {alert.stock_symbol} price {current_price:.2f} matched condition",
            email_sent=False,  # Will update after email send attempt
            email_sent_at=None,
        )
        
        db.add(history_entry)
        db.commit()
        
        logger.warning(
            f"🔔 ALERT TRIGGERED",
            extra={
                "alert_id": alert.id,
                "user_id": alert.user_id,
                "symbol": alert.stock_symbol,
                "alert_type": alert.alert_type.value,
                "condition": alert.condition.value if alert.condition else None,
                "target_value": alert.target_value,
                "current_price": current_price,
                "triggered_at": alert.triggered_at,
                "history_id": history_entry.id,
            },
        )
        
        # Send email notification if enabled and user email is available
        email_sent = False
        if settings.ENABLE_EMAIL_NOTIFICATIONS and alert.user and alert.user.email:
            try:
                send_alert_email_async(
                    user_email=alert.user.email,
                    symbol=alert.stock_symbol,
                    current_price=current_price,
                    condition=alert.condition.value if alert.condition else "N/A",
                    target_value=alert.target_value,
                    triggered_at=triggered_at_str,
                )
                
                # Update history entry with email sent timestamp
                history_entry.email_sent = True
                history_entry.email_sent_at = now
                db.commit()
                email_sent = True
                
                logger.info(
                    f"Email notification queued for alert",
                    extra={
                        "alert_id": alert.id,
                        "user_email": alert.user.email,
                        "history_id": history_entry.id,
                    },
                )
            except Exception as e:
                # Don't fail alert trigger if email fails
                logger.warning(
                    f"Failed to queue email notification",
                    extra={
                        "alert_id": alert.id,
                        "history_id": history_entry.id,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
        
        logger.info(
            f"Alert trigger complete",
            extra={
                "alert_id": alert.id,
                "email_sent": email_sent,
                "history_recorded": True,
                "is_triggered": True,
            },
        )
        
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(
            f"Failed to trigger alert",
            extra={
                "alert_id": alert.id,
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        return False


def check_all_alerts() -> None:
    """
    Check all active alerts and trigger those whose conditions are met.
    
    This function is called by the background scheduler every 30 seconds.
    Supports multiple alert types:
      - PRICE: Simple price threshold (existing)
      - PERCENTAGE_CHANGE: Monitor percentage change from last price
      - VOLUME_SPIKE: Detect unusual volume spikes
      - CRASH: Detect sudden price drops
      - CUSTOM: Custom conditions (extensible)
    
    It:
      1. Fetches all active alerts from the database
      2. Groups them by stock symbol for efficient price/volume fetching
      3. Fetches current prices and volume data using yfinance
      4. Compares against alert conditions based on alert type
      5. Triggers matching alerts and updates last_price
      6. Handles errors gracefully without stopping other checks
    
    This function runs synchronously and is designed to not block the FastAPI event loop.
    All errors are logged but don't propagate to avoid scheduler failures.
    """
    db = None
    
    try:
        from app.db.session import SessionLocal
        from app.models.alert import AlertType
        
        # Create database session for this check
        db = SessionLocal()
        
        # Fetch all active alerts
        active_alerts = db.query(Alert).filter(Alert.is_active == True).all()
        
        if not active_alerts:
            logger.debug("No active alerts to check")
            return
        
        logger.info(
            f"Starting alert check cycle",
            extra={"total_alerts": len(active_alerts)},
        )
        
        # Group alerts by symbol for efficient fetching
        alerts_by_symbol = {}
        for alert in active_alerts:
            symbol = alert.stock_symbol.upper()
            if symbol not in alerts_by_symbol:
                alerts_by_symbol[symbol] = []
            alerts_by_symbol[symbol].append(alert)
        
        # Track results
        total_checked = 0
        total_triggered = 0
        symbols_with_errors = []
        stats_by_type = {alert_type.value: 0 for alert_type in AlertType}
        
        # Check each symbol
        for symbol, alerts in alerts_by_symbol.items():
            try:
                # Fetch stock data (price and volume)
                stock = yf.Ticker(symbol)
                data = stock.history(period="20d")  # Get 20 days for volume average
                
                if data.empty:
                    logger.warning(
                        f"No price data available",
                        extra={"symbol": symbol, "alerts_count": len(alerts)},
                    )
                    symbols_with_errors.append(symbol)
                    continue
                
                # Extract current values
                current_price = float(data["Close"].iloc[-1])
                current_volume = float(data["Volume"].iloc[-1])
                
                # Calculate average volume (20-day, excluding current)
                avg_volume = float(data["Volume"].iloc[:-1].mean()) if len(data) > 1 else current_volume
                
                logger.debug(
                    f"Fetched data for symbol",
                    extra={
                        "symbol": symbol,
                        "current_price": current_price,
                        "current_volume": current_volume,
                        "avg_volume": avg_volume,
                        "alerts_count": len(alerts),
                    },
                )
                
                # Check each alert for this symbol
                for alert in alerts:
                    try:
                        total_checked += 1
                        alert_type = alert.alert_type
                        should_trigger = False
                        
                        # Dispatch to appropriate check method based on alert type
                        if alert_type == AlertType.PRICE:
                            should_trigger = alert.check_alert(current_price)
                        
                        elif alert_type == AlertType.PERCENTAGE_CHANGE:
                            should_trigger = alert.check_alert(
                                current_price,
                                avg_volume=avg_volume,
                                current_volume=current_volume
                            )
                        
                        elif alert_type == AlertType.VOLUME_SPIKE:
                            should_trigger = alert.check_alert(
                                current_price,
                                avg_volume=avg_volume,
                                current_volume=current_volume
                            )
                        
                        elif alert_type == AlertType.CRASH:
                            should_trigger = alert.check_alert(current_price)
                        
                        elif alert_type == AlertType.CUSTOM:
                            should_trigger = alert.check_alert(current_price)
                        
                        # PRODUCTION: Implement cooldown and re-arm logic
                        # =============================================
                        cooldown_minutes = settings.ALERT_COOLDOWN_MINUTES
                        dev_mode = settings.ALERT_DEV_MODE
                        
                        if should_trigger:
                            # Condition is met - check if we're in cooldown period
                            if alert.is_triggered and alert.last_triggered_at:
                                # Check if cooldown period is still active (unless in dev mode)
                                time_since_trigger = datetime.utcnow() - alert.last_triggered_at
                                cooldown_seconds = cooldown_minutes * 60
                                
                                if not dev_mode and time_since_trigger.total_seconds() < cooldown_seconds:
                                    # Still in cooldown period - skip this trigger
                                    if settings.ALERT_LOG_COOLDOWN_CHECKS:
                                        logger.debug(
                                            f"Alert in cooldown period, skipping trigger",
                                            extra={
                                                "alert_id": alert.id,
                                                "seconds_until_rearm": cooldown_seconds - int(time_since_trigger.total_seconds()),
                                            },
                                        )
                                    should_trigger = False  # Don't trigger during cooldown
                                elif dev_mode and alert.is_triggered:
                                    # Dev mode: Allow re-trigger despite cooldown
                                    logger.info(
                                        f"Dev mode: Overriding cooldown, allowing trigger",
                                        extra={
                                            "alert_id": alert.id,
                                            "seconds_since_trigger": int(time_since_trigger.total_seconds()),
                                        },
                                    )
                        else:
                            # Condition NOT met - implement re-arm logic
                            if alert.is_triggered:
                                # Alert was previously triggered but condition is now false
                                # Reset is_triggered to allow triggering again after cooldown expires
                                logger.info(
                                    f"Re-arming alert (condition no longer met)",
                                    extra={
                                        "alert_id": alert.id,
                                        "alert_type": alert_type.value,
                                        "symbol": symbol,
                                    },
                                )
                                alert.is_triggered = False
                                alert.last_triggered_at = None
                                db.commit()
                        
                        # Trigger alert if condition met AND not in cooldown
                        if should_trigger:
                            if trigger_alert(db, alert, current_price):
                                total_triggered += 1
                                stats_by_type[alert_type.value] += 1
                        
                        # Update last_price for percentage change and crash alerts
                        if alert_type in [AlertType.PERCENTAGE_CHANGE, AlertType.CRASH]:
                            alert.last_price = current_price
                            db.commit()
                        
                    except Exception as e:
                        logger.error(
                            f"Error checking individual alert",
                            extra={
                                "alert_id": alert.id,
                                "alert_type": alert.alert_type.value,
                                "symbol": symbol,
                                "error": str(e),
                                "error_type": type(e).__name__,
                            },
                            exc_info=True,
                        )
                        continue
                
            except Exception as e:
                logger.error(
                    f"Error fetching data for symbol",
                    extra={
                        "symbol": symbol,
                        "alerts_count": len(alerts),
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                    exc_info=True,
                )
                symbols_with_errors.append(symbol)
                continue
        
        # Log detailed summary
        logger.info(
            f"Alert check cycle completed",
            extra={
                "total_alerts_checked": total_checked,
                "alerts_triggered": total_triggered,
                "symbols_processed": len(alerts_by_symbol),
                "symbols_with_errors": len(symbols_with_errors),
                "error_symbols": symbols_with_errors if symbols_with_errors else None,
                "triggers_by_type": stats_by_type,
            },
        )
        
    except Exception as e:
        logger.error(
            f"Fatal error in alert check cycle",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
    
    finally:
        # Always close the database session
        if db is not None:
            try:
                db.close()
            except Exception as e:
                logger.error(
                    f"Error closing database session",
                    extra={
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
