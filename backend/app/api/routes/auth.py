from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import Token
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserRead,
    UserUpdate,
    PasswordChange,
)
from app.config import settings


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db_session),
) -> User:
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_in.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
    
    # Check if WhatsApp phone already exists (if provided)
    if user_in.whatsapp_phone:
        existing_phone = db.query(User).filter(User.whatsapp_phone == user_in.whatsapp_phone).first()
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this WhatsApp phone number already exists",
            )

    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        password_hash=get_password_hash(user_in.password),
        whatsapp_phone=user_in.whatsapp_phone,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or phone number already exists",
        )
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db_session),
) -> Token:
    # Try to find user by email or phone number
    user = db.query(User).filter(
        (User.email == form_data.username) |
        (User.whatsapp_phone == form_data.username)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(subject=user.email, expires_delta=access_token_expires)
    return Token(access_token=access_token)


@router.post("/login-json", response_model=Token)
def login_json(
    login_data: UserLogin,
    db: Session = Depends(get_db_session),
) -> Token:
    # Try to find user by email or phone number
    query = db.query(User)
    if login_data.email:
        query = query.filter(User.email == login_data.email)
    elif login_data.phone:
        query = query.filter(User.whatsapp_phone == login_data.phone)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either email or phone must be provided",
        )
    
    user = query.first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(subject=user.email, expires_delta=access_token_expires)
    return Token(access_token=access_token)


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Return the currently authenticated user. Requires Bearer token."""
    return current_user


@router.patch("/me", response_model=UserRead)
def update_me(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> User:
    """Update the current user's profile."""
    if user_in.full_name is not None:
        current_user.full_name = user_in.full_name.strip() if user_in.full_name else None
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/change-password")
def change_password(
    body: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> dict:
    """Change the current user's password."""
    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    current_user.password_hash = get_password_hash(body.new_password)
    db.commit()
    return {"detail": "Password updated"}


# ---------------------------------------------------------------------------
# Password reset: DISABLED
#
# The previous implementation accepted a hardcoded OTP that was never
# delivered to the user, which allowed anyone to reset any account's
# password. Both endpoints now refuse every request without reading input
# or touching the database.
#
# TODO(security): before re-enabling, implement:
#   - a random 6-digit code generated with `secrets` (not `random`)
#   - store only a hash of the code (never the plaintext), in the database
#     so it works across workers/replicas
#   - 10-minute expiry, single use, invalidated on success
#   - a cap on verification attempts per code (e.g. 5), then invalidate
#   - rate limiting on both endpoints, per IP and per email
#   - delivery by email; the request endpoint must return the same response
#     whether or not the account exists (no account enumeration)
#   - invalidate existing sessions/tokens after a successful reset
# ---------------------------------------------------------------------------

_PASSWORD_RESET_DISABLED = "Password reset is temporarily unavailable. Please contact support."


@router.post("/forgot-password", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def forgot_password_request() -> dict:
    """Disabled until a secure reset flow exists (see TODO above)."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_PASSWORD_RESET_DISABLED)


@router.post("/forgot-password/verify", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def forgot_password_verify() -> dict:
    """Disabled until a secure reset flow exists (see TODO above)."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_PASSWORD_RESET_DISABLED)

