#!/usr/bin/env python
"""
Test script for SMTP email service.

Run with: python test_email_smtp.py

This tests the new synchronous SMTP email implementation.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
)

def test_smtp_email():
    """Test the SMTP email service."""
    from app.services.email_smtp import send_alert_notification
    from app.config import settings
    
    print("\n" + "="*80)
    print("TESTING SMTP EMAIL SERVICE")
    print("="*80)
    
    # Check email configuration
    print("\n📧 Email Configuration:")
    print(f"  - Enabled: {settings.ENABLE_EMAIL_NOTIFICATIONS}")
    print(f"  - SMTP Server: {settings.MAIL_SERVER}:{settings.MAIL_PORT}")
    print(f"  - From Address: {settings.MAIL_FROM}")
    print(f"  - Username: {settings.MAIL_USERNAME}")
    print(f"  - STARTTLS: {settings.MAIL_STARTTLS}")
    
    if not settings.ENABLE_EMAIL_NOTIFICATIONS:
        print("\n⚠️  EMAIL NOTIFICATIONS ARE DISABLED")
        print("   Set ENABLE_EMAIL_NOTIFICATIONS=true to enable")
        return False
    
    # Test recipient
    test_email = settings.MAIL_USERNAME or "test@example.com"
    
    print(f"\n📤 Sending test alert email to: {test_email}")
    
    # Send test email
    success = send_alert_notification(
        user_email=test_email,
        symbol="AAPL",
        current_price=175.50,
        condition=">",
        target_value=175.00,
        triggered_at="2025-01-16T10:30:45Z",
        alert_type="price",
    )
    
    if success:
        print("✅ Email sent successfully!")
        print("\n📧 If you don't see the email in your inbox:")
        print("   1. Check your spam/junk folder")
        print("   2. Verify SMTP credentials in .env")
        print("   3. Check backend logs for details")
        return True
    else:
        print("❌ Failed to send email")
        print("\n📋 Check the logs above for error details")
        return False


if __name__ == "__main__":
    try:
        success = test_smtp_email()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
