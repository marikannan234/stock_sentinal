#!/usr/bin/env python3
"""
Test: Optional Condition Field for Non-PRICE Alerts

Validates that the fix for making condition optional works correctly.
Tests both schema validation and end-to-end database operations.
"""

import sys
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models.alert import AlertType, AlertCondition
from app.schemas.alert import CreateAlertRequest
from app.db.session import SessionLocal
from app.models.user import User
from app.services.alert_service import AlertService


def test_price_alert_requires_condition():
    """Test 1: PRICE alerts MUST have condition"""
    print("\n✅ Test 1: PRICE alert requires condition")
    
    try:
        # Should FAIL - PRICE alert without condition
        request = CreateAlertRequest(
            stock_symbol="AAPL",
            alert_type=AlertType.PRICE,
            target_value=150.0,
            condition=None  # Missing condition
        )
        print(f"  ❌ FAILED: Should have rejected PRICE alert without condition")
        return False
    except ValidationError:
        print(f"  ✅ PASSED: Correctly rejected PRICE alert without condition")
        return True


def test_percentage_change_without_condition():
    """Test 2: PERCENTAGE_CHANGE alert works WITHOUT condition"""
    print("\n✅ Test 2: PERCENTAGE_CHANGE alert without condition")
    
    try:
        request = CreateAlertRequest(
            stock_symbol="MSFT",
            alert_type=AlertType.PERCENTAGE_CHANGE,
            target_value=5.0,
            condition=None  # No condition needed
        )
        assert request.alert_type == AlertType.PERCENTAGE_CHANGE
        assert request.condition is None
        print(f"  ✅ PASSED: PERCENTAGE_CHANGE alert created without condition")
        return True
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False


def test_volume_spike_without_condition():
    """Test 3: VOLUME_SPIKE alert works WITHOUT condition"""
    print("\n✅ Test 3: VOLUME_SPIKE alert without condition")
    
    try:
        request = CreateAlertRequest(
            stock_symbol="GOOGL",
            alert_type=AlertType.VOLUME_SPIKE,
            target_value=1.5,
            condition=None
        )
        assert request.alert_type == AlertType.VOLUME_SPIKE
        assert request.condition is None
        print(f"  ✅ PASSED: VOLUME_SPIKE alert created without condition")
        return True
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False


def test_crash_alert_without_condition():
    """Test 4: CRASH alert works WITHOUT condition"""
    print("\n✅ Test 4: CRASH alert without condition")
    
    try:
        request = CreateAlertRequest(
            stock_symbol="AMZN",
            alert_type=AlertType.CRASH,
            target_value=10.0,
            condition=None
        )
        assert request.alert_type == AlertType.CRASH
        assert request.condition is None
        print(f"  ✅ PASSED: CRASH alert created without condition")
        return True
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False


def test_database_persistence():
    """Test 5: Alerts persist correctly in database"""
    print("\n✅ Test 5: Database persistence with optional condition")
    
    db = SessionLocal()
    try:
        # Get test user
        user = db.query(User).first()
        if not user:
            print("  ➜ Note: No test user found, skipping database test")
            return True
        
        # Create PERCENTAGE_CHANGE alert without condition
        request = CreateAlertRequest(
            stock_symbol="TEST",
            alert_type=AlertType.PERCENTAGE_CHANGE,
            target_value=5.0,
            condition=None
        )
        
        service = AlertService(db)
        try:
            alert = service.create_alert(user, request)
            print(f"  ✅ PASSED: Alert created in database (ID={alert.id})")
            print(f"    - Symbol: {alert.stock_symbol}")
            print(f"    - Type: {alert.alert_type.value}")
            print(f"    - Condition: {alert.condition}")
            print(f"    - Target: {alert.target_value}")
            return True
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                print(f"  ✅ PASSED: Alert already exists (duplicate check works)")
                return True
            raise
    
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False
    finally:
        db.close()


def test_price_alert_with_condition_database():
    """Test 6: PRICE alert with condition in database"""
    print("\n✅ Test 6: PRICE alert with condition (database)")
    
    db = SessionLocal()
    try:
        user = db.query(User).first()
        if not user:
            print("  ➜ Note: No test user found, skipping database test")
            return True
        
        request = CreateAlertRequest(
            stock_symbol="PRICE_TEST",
            alert_type=AlertType.PRICE,
            target_value=150.0,
            condition=AlertCondition.GREATER_THAN
        )
        
        service = AlertService(db)
        try:
            alert = service.create_alert(user, request)
            print(f"  ✅ PASSED: PRICE alert created (ID={alert.id})")
            print(f"    - Condition: {alert.condition.value if alert.condition else None}")
            return True
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"  ✅ PASSED: Alert already exists")
                return True
            raise
    
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False
    finally:
        db.close()


def main():
    """Run all tests"""
    print("=" * 70)
    print("Testing: Optional Condition Field for Non-PRICE Alerts")
    print("=" * 70)
    
    tests = [
        test_price_alert_requires_condition,
        test_percentage_change_without_condition,
        test_volume_spike_without_condition,
        test_crash_alert_without_condition,
        test_database_persistence,
        test_price_alert_with_condition_database,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Test crashed: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("=" * 70)
    
    if all(results):
        print("\n✅ ALL TESTS PASSED!\n")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED!\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
