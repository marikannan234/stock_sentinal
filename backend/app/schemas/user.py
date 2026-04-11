from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = Field(default=None, max_length=255)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
    whatsapp_phone: Optional[str] = Field(default=None, max_length=20, description="WhatsApp phone with country code (e.g., +919876543210)")


class UserLogin(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.email and not self.phone:
            raise ValueError('Either email or phone must be provided')


class UserRead(UserBase):
    id: int
    is_active: bool
    whatsapp_phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=255)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordVerify(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)
    new_password: str = Field(min_length=8, max_length=128)

