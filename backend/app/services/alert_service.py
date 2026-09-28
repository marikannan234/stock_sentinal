"""
Alert service module for Stock Sentinel.

Alert CRUD for the API, plus `check_all_alerts`, the scheduler's entry point.
Evaluation (market data, per-type checkers, notifications) lives in
app.services.alerts.
"""

import logging

from sqlalchemy.orm import Session

from app.core.exceptions import (
    AlertNotFoundError,
    AuthorizationError,
    DuplicateAlertError,
)
from app.models.alert import Alert
from app.models.user import User
from app.schemas.alert import AlertResponse, CreateAlertRequest, UpdateAlertRequest
from app.services.alerts import run_alert_checks

logger = logging.getLogger(__name__)

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
        Create an alert. `request` has already been validated for its type
        (see app.schemas.alert), so every parameter the type needs is present
        and unused ones are None.

        Raises:
            DuplicateAlertError: If the user already has an identical alert
        """
        alert_type = request.alert_type
        parameters = {
            "condition": request.condition,
            "target_value": request.target_value,
            "sma_period": request.sma_period,
            "ema_period": request.ema_period,
            "rsi_period": request.rsi_period,
        }

        duplicate = self.db.query(Alert).filter(
            Alert.user_id == user.id,
            Alert.stock_symbol == request.stock_symbol,
            Alert.alert_type == alert_type,
            *[
                getattr(Alert, name).is_(None) if value is None else getattr(Alert, name) == value
                for name, value in parameters.items()
            ],
        ).first()
        if duplicate:
            raise DuplicateAlertError(
                request.stock_symbol,
                request.condition.value if request.condition else alert_type.value,
                request.target_value if request.target_value is not None else 0,
            )

        alert = Alert(
            user_id=user.id,
            stock_symbol=request.stock_symbol,
            alert_type=alert_type,
            is_active=True,
            is_triggered=False,
            last_price=None,  # recorded on the first check
            **parameters,
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)

        logger.info(
            "Alert created",
            extra={"user_id": user.id, "alert_id": alert.id, "symbol": alert.stock_symbol, "alert_type": alert_type.value},
        )
        return AlertResponse.model_validate(alert)
    
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
        
        return AlertResponse.model_validate(alert)
    
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
        
        return [AlertResponse.model_validate(alert) for alert in alerts]
    
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
        
        return [AlertResponse.model_validate(alert) for alert in alerts]
    
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
        
        return [AlertResponse.model_validate(alert) for alert in alerts]
    
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
        
        if request.is_active and not alert.is_active:
            # Re-arm: alerts are one-shot, so enabling one starts a fresh
            # watch. Clear the fired flag and the recorded reference/previous
            # values so percent/crash/crossover rules re-baseline.
            alert.is_triggered = False
            alert.last_price = None
            alert.last_ema = None
            alert.last_rsi = None
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
        
        return AlertResponse.model_validate(alert)


def check_all_alerts() -> None:
    """Scheduler entry point: run one alert check cycle (see app.services.alerts)."""
    run_alert_checks()
