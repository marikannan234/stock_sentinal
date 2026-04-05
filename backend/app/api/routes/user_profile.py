"""
User profile and settings management endpoints.
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models.user import User
from app.models.trading import UserSettings
from app.schemas.user import UserRead, UserUpdate
from app.schemas.trading import (
    UserSettingsRead,
    UserSettingsUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/profile", response_model=UserRead)
def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> User:
    """Get current user profile."""
    return current_user


@router.put("/profile", response_model=UserRead)
def update_user_profile(
    profile_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> User:
    """Update user profile."""
    
    update_data = profile_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if value is not None:
            setattr(current_user, field, value)
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    logger.info(f"User {current_user.id} profile updated")
    return current_user


@router.get("/settings", response_model=UserSettingsRead)
def get_user_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> UserSettings:
    """Get user settings."""
    
    settings = db.query(UserSettings).filter(
        UserSettings.user_id == current_user.id
    ).first()
    
    if not settings:
        # Create default settings if not exists
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
        logger.info(f"Created default settings for user {current_user.id}")
    
    return settings


@router.put("/settings", response_model=UserSettingsRead)
def update_user_settings(
    settings_update: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> UserSettings:
    """Update user settings."""
    
    settings = db.query(UserSettings).filter(
        UserSettings.user_id == current_user.id
    ).first()
    
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    # Update only provided fields
    update_data = settings_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(settings, field, value)
    
    db.add(settings)
    db.commit()
    db.refresh(settings)
    
    logger.info(f"User {current_user.id} settings updated")
    return settings
