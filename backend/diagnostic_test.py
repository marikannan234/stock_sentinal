"""
Diagnostic test for alert_type NULL constraint error.

Run this to trace the complete flow with detailed logging.
Usage: python diagnostic_test.py
"""

import logging
import sys

# Enable SQLAlchemy SQL echo logging
logging.basicConfig(level=logging.DEBUG)
sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
sqlalchemy_logger.setLevel(logging.INFO)

# Create a handler to print SQL to console
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
sqlalchemy_logger.addHandler(handler)

# Now import app
from app.config import settings
from app.db.session import engine, SessionLocal
from app.models.alert import Alert, AlertType, AlertCondition
from app.models.user import User
from app.schemas.alert import CreateAlertRequest

# Create tables
from app.models.alert import Base as AlertBase
AlertBase.metadata.create_all(bind=engine)

print("=" * 80)
print("DIAGNOSTIC TEST: Alert Type NULL Constraint Error")
print("=" * 80)

# Get session
db = SessionLocal()

try:
    # Step 1: Create a test user
    print("\n[STEP 1] Creating test user...")
    user = User(
        email="test_alert@example.com",
        full_name="Test User",
        password_hash="hashed_password",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"✓ User created: ID={user.id}")

    # Step 2: Create alert request
    print("\n[STEP 2] Creating alert request...")
    alert_request = CreateAlertRequest(
        stock_symbol="AAPL",
        alert_type=AlertType.PERCENTAGE_CHANGE,  # Use enum value
        target_value=5.0
    )
    print(f"✓ Request created:")
    print(f"  - alert_type (raw): {alert_request.alert_type}")
    print(f"  - alert_type (type): {type(alert_request.alert_type).__name__}")
    print(f"  - alert_type (value): {alert_request.alert_type.value if hasattr(alert_request.alert_type, 'value') else 'N/A'}")

    # Step 3: Validate schema parsing
    print("\n[STEP 3] Validating Pydantic schema parsing...")
    print(f"  - model_dump(): {alert_request.model_dump()}")
    assert alert_request.alert_type is not None, "alert_type is None!"
    assert isinstance(alert_request.alert_type, AlertType), f"alert_type is not AlertType enum: {type(alert_request.alert_type)}"
    print(f"✓ Schema validation passed")

    # Step 4: Create Alert object directly (simulating service layer)
    print("\n[STEP 4] Creating Alert object directly (simulating service)...")
    alert_type = alert_request.alert_type or AlertType.PRICE
    print(f"  - alert_type variable: {alert_type}")
    print(f"  - alert_type type: {type(alert_type).__name__}")
    print(f"  - alert_type is None?: {alert_type is None}")

    alert = Alert(
        user_id=user.id,
        stock_symbol=alert_request.stock_symbol,
        alert_type=alert_type,
        condition=None,  # Not required for PERCENTAGE_CHANGE
        target_value=alert_request.target_value,
        is_active=True,
        last_price=None,
    )
    print(f"✓ Alert object created:")
    print(f"  - alert.alert_type: {alert.alert_type}")
    print(f"  - alert.alert_type type: {type(alert.alert_type).__name__}")
    print(f"  - alert.alert_type is None?: {alert.alert_type is None}")

    # Step 5: Add to session and check pending
    print("\n[STEP 5] Adding alert to session...")
    db.add(alert)
    print(f"✓ Alert added to session")
    print(f"  - Session.new count: {len(db.new)}")
    print(f"  - alert in session.new: {alert in db.new}")

    # Step 6: Commit and log SQL
    print("\n[STEP 6] Committing to database (SQL will be shown above)...")
    print("  Watching for INSERT query...")
    db.commit()
    print(f"✓ Commit successful")

    # Step 7: Refresh and verify
    print("\n[STEP 7] Refreshing from database...")
    db.refresh(alert)
    print(f"✓ Alert refreshed:")
    print(f"  - alert.id: {alert.id}")
    print(f"  - alert.alert_type: {alert.alert_type}")
    print(f"  - alert.alert_type type: {type(alert.alert_type).__name__}")

    # Step 8: Verify in database
    print("\n[STEP 8] Querying alert from database...")
    db_alert = db.query(Alert).filter(Alert.id == alert.id).first()
    
    if db_alert is None:
        print("❌ ERROR: Alert not found in database!")
    else:
        print(f"✓ Alert found in database:")
        print(f"  - id: {db_alert.id}")
        print(f"  - alert_type: {db_alert.alert_type}")
        print(f"  - alert_type value: {db_alert.alert_type.value if db_alert.alert_type else 'NULL'}")

        if db_alert.alert_type is None:
            print("\n❌ ERROR: alert_type is NULL in database!")
        else:
            print("\n✅ SUCCESS: alert_type correctly saved to database!")

except Exception as e:
    print(f"\n❌ Error during diagnostic test:")
    print(f"  - Error type: {type(e).__name__}")
    print(f"  - Error message: {str(e)}")
    import traceback
    traceback.print_exc()

finally:
    db.close()
    print("\n" + "=" * 80)
    print("Diagnostic test complete")
    print("=" * 80)
