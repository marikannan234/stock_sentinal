# Optional Condition Field for Non-PRICE Alerts - Complete Fix

## Problem Statement

**Original Error:** 422 Unprocessable Entity - "condition" field required

**Root Cause:** 
The API required `condition` field for ALL alert types, but logically:
- PRICE alerts need condition (e.g., `price > 150`)
- PERCENTAGE_CHANGE alerts don't need condition (use percentage in target_value)
- VOLUME_SPIKE alerts don't need condition (automatic spike detection)
- CRASH alerts don't need condition (automatic crash detection)
- CUSTOM alerts can optionally have condition

---

## Solution Overview

Made a **three-layer fix**:

1. **Pydantic Schema** - Make condition optional, require it only for PRICE alerts
2. **SQLAlchemy Model** - Update database column to allow NULL values
3. **Database Migration** - Apply schema change to PostgreSQL
4. **Service Logic** - Handle optional condition correctly

---

## Detailed Changes

### 1. Pydantic Schema (`app/schemas/alert.py`)

**Changed condition field from:**
```python
condition: AlertCondition = Field(..., description="...")
```

**To:**
```python
condition: Optional[AlertCondition] = Field(
    None, 
    description="Price comparison condition (>, <, >=, <=) - REQUIRED for PRICE alerts, optional for others"
)
```

**Added model validator for conditional requirement:**
```python
@model_validator(mode="after")
def validate_condition_requirement(self):
    """Validate that condition is required only for PRICE alerts."""
    if self.alert_type == AlertType.PRICE and self.condition is None:
        raise ValueError("'condition' field is REQUIRED for PRICE alerts (must be one of: >, <, >=, <=)")
    return self
```

**Updated condition field validator to allow None:**
```python
@field_validator("condition", mode="before")
@classmethod
def validate_condition(cls, v):
    """Normalize condition enum value (case-insensitive)."""
    if v is None:  # ← NEW: Allow None
        return None
    
    if isinstance(v, AlertCondition):
        return v
    if isinstance(v, str):
        # ... case-insensitive matching logic ...
    raise ValueError(f"condition must be a string or null, got {type(v).__name__}")
```

---

### 2. SQLAlchemy Model (`app/models/alert.py`)

**Changed condition column from:**
```python
condition: Mapped[AlertCondition] = mapped_column(
    SQLEnum(AlertCondition),
    nullable=False,
    default=AlertCondition.GREATER_THAN
)
```

**To:**
```python
condition: Mapped[Optional[AlertCondition]] = mapped_column(
    SQLEnum(AlertCondition),
    nullable=True,  # ← Allow NULL for non-PRICE alerts
    default=None
)
```

---

### 3. Database Migration

**Created:** `alembic/versions/25e65135c38c_allow_null_condition_for_non_price_.py`

**Changes:**
```sql
ALTER TABLE alerts ALTER COLUMN condition DROP NOT NULL;
```

**Applied with:**
```bash
alembic upgrade head
```

---

### 4. Service Logic (`app/services/alert_service.py`)

**Enhanced `create_alert()` to handle optional condition:**

```python
def create_alert(self, user: User, request: CreateAlertRequest) -> AlertResponse:
    # Validate condition based on alert type
    if alert_type == AlertType.PRICE:
        # PRICE alerts REQUIRE condition
        if request.condition is None:
            raise InvalidAlertConditionError(None, [c.value for c in AlertCondition])
        if not isinstance(request.condition, AlertCondition):
            raise InvalidAlertConditionError(...)
    
    # Other alert types: condition is optional
    condition = request.condition  # Can be None
    
    # Create alert with nullable condition
    alert = Alert(
        user_id=user.id,
        stock_symbol=request.stock_symbol,
        condition=condition,  # ← Can be None
        target_value=request.target_value,
        alert_type=alert_type,
        is_active=True,
    )
```

---

## Now Supported Request Formats

### ✅ PRICE Alert (Requires Condition)

```json
{
  "stock_symbol": "AAPL",
  "alert_type": "PRICE",
  "condition": ">",
  "target_value": 150.0
}
```

**Response:** 201 Created

### ✅ PERCENTAGE_CHANGE Alert (No Condition Needed)

```json
{
  "stock_symbol": "MSFT",
  "alert_type": "PERCENTAGE_CHANGE",
  "target_value": 5.0
}
```

**Response:** 201 Created

### ✅ PERCENTAGE_CHANGE Alert (Optional Condition)

```json
{
  "stock_symbol": "MSFT",
  "alert_type": "PERCENTAGE_CHANGE",
  "condition": ">",
  "target_value": 5.0
}
```

**Response:** 201 Created

### ✅ VOLUME_SPIKE Alert (No Condition Needed)

```json
{
  "stock_symbol": "GOOGL",
  "alert_type": "VOLUME_SPIKE",
  "target_value": 1.5
}
```

**Response:** 201 Created

### ✅ CRASH Alert (No Condition Needed)

```json
{
  "stock_symbol": "AMZN",
  "alert_type": "CRASH",
  "target_value": 10.0
}
```

**Response:** 201 Created

### ❌ PRICE Alert WITHOUT Condition (Invalid)

```json
{
  "stock_symbol": "AAPL",
  "alert_type": "PRICE",
  "target_value": 150.0
}
```

**Response:** 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "msg": "Value error, 'condition' field is REQUIRED for PRICE alerts (must be one of: >, <, >=, <=)",
      "type": "value_error"
    }
  ]
}
```

---

## Test Results

### Schema Validation Tests (10/10 PASSED ✅)

```
✅ Test 1: PRICE alerts REQUIRE condition
✅ Test 2: PRICE alerts work WITH condition
✅ Test 3: PERCENTAGE_CHANGE alerts work WITHOUT condition
✅ Test 4: PERCENTAGE_CHANGE alerts work WITH optional condition
✅ Test 5: VOLUME_SPIKE alerts work WITHOUT condition
✅ Test 6: CRASH alerts work WITHOUT condition
✅ Test 7: CUSTOM alerts work WITHOUT condition
✅ Test 8: Default alert type is PRICE (requires condition)
✅ Test 9: Case-insensitive enum handling still works
✅ Test 10: Case-insensitive condition handling with PRICE alert
```

**Run:** `python test_condition_optional.py`

### End-to-End Database Tests (7/7 PASSED ✅)

```
✅ Test 1: Create PRICE alert WITH condition (ID=12)
✅ Test 2: Create PERCENTAGE_CHANGE alert WITHOUT condition (ID=13)
✅ Test 3: Create VOLUME_SPIKE alert WITHOUT condition (ID=14)
✅ Test 4: Create CRASH alert WITHOUT condition (ID=15)
✅ Test 5: Create PERCENTAGE_CHANGE alert WITH optional condition (ID=16)
✅ Test 6: Duplicate detection works with optional condition
✅ Test 7: Query all alerts - database persistence verified
```

**Run:** `python test_condition_optional_e2e.py`

---

## Backward Compatibility

✅ **100% Backward Compatible**

- Existing PRICE alerts with condition still work perfectly
- Existing requests with condition in the JSON still work
- Condition is optional but still accepted if provided
- Database schema change is transparent to existing code

---

## Alert Type Behavior Reference

| Alert Type | Condition | Required? | Example target_value |
|---|---|---|---|
| **PRICE** | `>, <, >=, <=` | ✅ YES | `150.0` (price) |
| **PERCENTAGE_CHANGE** | (optional) | ❌ NO | `5.0` (5% change) |
| **VOLUME_SPIKE** | (optional) | ❌ NO | `1.5` (150% of avg) |
| **CRASH** | (optional) | ❌ NO | `10.0` (10% drop) |
| **CUSTOM** | (optional) | ❌ NO | Custom value |

---

## Complete Updated Schema

```python
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.alert import AlertCondition, AlertType


class AlertBase(BaseModel):
    """Base alert schema."""
    
    stock_symbol: str = Field(..., min_length=1, max_length=16, description="Stock ticker symbol (e.g., AAPL)")
    condition: Optional[AlertCondition] = Field(None, description="Price comparison condition (>, <, >=, <=) - REQUIRED for PRICE alerts, optional for others")
    target_value: float = Field(..., gt=0, description="Target value (price or multiplier depending on alert type)")
    alert_type: AlertType = Field(default=AlertType.PRICE, description="Type of alert (price, percentage_change, volume_spike, crash, custom)")
    
    @field_validator("stock_symbol", mode="before")
    @classmethod
    def validate_stock_symbol(cls, v: str) -> str:
        """Ensure stock symbol is uppercase."""
        if not isinstance(v, str):
            raise ValueError("stock_symbol must be a string")
        v = v.strip().upper()
        if not v:
            raise ValueError("stock_symbol cannot be empty")
        return v
    
    @field_validator("target_value", mode="before")
    @classmethod
    def validate_target_value(cls, v: float) -> float:
        """Ensure target value is positive."""
        if not isinstance(v, (int, float)):
            raise ValueError("target_value must be a number")
        if v <= 0:
            raise ValueError("target_value must be greater than 0")
        return float(v)
    
    @field_validator("condition", mode="before")
    @classmethod
    def validate_condition(cls, v):
        """Normalize condition enum value (case-insensitive)."""
        if v is None:
            return None
        
        if isinstance(v, AlertCondition):
            return v
        if isinstance(v, str):
            v = v.strip()
            try:
                return AlertCondition(v)
            except ValueError:
                pass
            for condition in AlertCondition:
                if condition.value.lower() == v.lower():
                    return condition
            valid_values = [c.value for c in AlertCondition]
            raise ValueError(f"Invalid condition '{v}'. Must be one of: {', '.join(valid_values)}")
        raise ValueError(f"condition must be a string or null, got {type(v).__name__}")
    
    @field_validator("alert_type", mode="before")
    @classmethod
    def validate_alert_type(cls, v):
        """Normalize alert_type enum value (case-insensitive)."""
        if isinstance(v, AlertType):
            return v
        if isinstance(v, str):
            v = v.strip()
            try:
                return AlertType(v)
            except ValueError:
                pass
            for alert_type in AlertType:
                if alert_type.value.lower() == v.lower():
                    return alert_type
            valid_values = [t.value for t in AlertType]
            raise ValueError(f"Invalid alert_type '{v}'. Must be one of: {', '.join(valid_values)}")
        if v is None:
            return AlertType.PRICE
        raise ValueError(f"alert_type must be a string or null, got {type(v).__name__}")
    
    @model_validator(mode="after")
    def validate_condition_requirement(self):
        """Validate that condition is required only for PRICE alerts."""
        if self.alert_type == AlertType.PRICE and self.condition is None:
            raise ValueError("'condition' field is REQUIRED for PRICE alerts (must be one of: >, <, >=, <=)")
        return self


class CreateAlertRequest(AlertBase):
    """Request schema for creating a new alert."""
    pass


class UpdateAlertRequest(BaseModel):
    """Request schema for updating an alert."""
    is_active: bool = Field(..., description="Whether the alert is active")


class AlertResponse(AlertBase):
    """Response schema for alert data."""
    
    id: int = Field(..., description="Alert unique identifier")
    user_id: int = Field(..., description="User ID who owns this alert")
    is_active: bool = Field(..., description="Whether alert is currently active")
    created_at: datetime = Field(..., description="When the alert was created")
    triggered_at: Optional[datetime] = Field(None, description="When the alert was last triggered")
    last_price: Optional[float] = Field(None, description="Last recorded price")
    
    class Config:
        from_attributes = True
        use_enum_values = False
```

---

## Migration Files Created

**File:** `alembic/versions/25e65135c38c_allow_null_condition_for_non_price_.py`

```python
def upgrade() -> None:
    op.alter_column('alerts', 'condition',
               existing_type=postgresql.ENUM('GREATER_THAN', 'LESS_THAN', 'GREATER_THAN_OR_EQUAL', 'LESS_THAN_OR_EQUAL', 'PERCENTAGE_CHANGE', name='alertcondition'),
               nullable=True)

def downgrade() -> None:
    op.alter_column('alerts', 'condition',
               existing_type=postgresql.ENUM('GREATER_THAN', 'LESS_THAN', 'GREATER_THAN_OR_EQUAL', 'LESS_THAN_OR_EQUAL', 'PERCENTAGE_CHANGE', name='alertcondition'),
               nullable=False)
```

---

## Files Modified

| File | Changes | Impact |
|------|---------|--------|
| `app/schemas/alert.py` | Made condition optional, added conditional validator | ✅ Pydantic accepts optional condition with smart validation |
| `app/models/alert.py` | Made condition column nullable | ✅ Database allows NULL values |
| `alembic/versions/25e65135c38c_...py` | Migration to set nullable=True | ✅ Database schema updated |
| `app/services/alert_service.py` | Handle optional condition in create_alert | ✅ Service validates based on alert_type |

---

## Verification Checklist

- ✅ PRICE alerts require condition
- ✅ PERCENTAGE_CHANGE works without condition
- ✅ VOLUME_SPIKE works without condition
- ✅ CRASH works without condition
- ✅ CUSTOM works without condition
- ✅ Other alert types can optionally have condition
- ✅ Case-insensitive enum handling still works
- ✅ Duplicate detection includes condition
- ✅ Database persistence verified
- ✅ All enums handles uppercase/lowercase correctly
- ✅ Error messages are helpful
- ✅ Backward compatible with existing code

---

## How to Test Locally

### Verify Schema Validation
```bash
cd backend
python test_condition_optional.py
```

### Verify Database Operations
```bash
python test_condition_optional_e2e.py
```

### Manual API Testing

**Test 1: Create PRICE alert (with condition)**
```bash
curl -X POST http://localhost:8000/api/alerts \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_symbol": "AAPL",
    "alert_type": "PRICE",
    "condition": ">",
    "target_value": 150.0
  }'
```

**Test 2: Create PERCENTAGE_CHANGE alert (without condition)**
```bash
curl -X POST http://localhost:8000/api/alerts \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_symbol": "MSFT",
    "alert_type": "PERCENTAGE_CHANGE",
    "target_value": 5.0
  }'
```

**Test 3: Create PRICE alert without condition (should fail)**
```bash
curl -X POST http://localhost:8000/api/alerts \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_symbol": "AAPL",
    "alert_type": "PRICE",
    "target_value": 150.0
  }'
```

Expected response: 422 Unprocessable Entity with message about condition requirement.

---

## Production Readiness

✅ **Code Quality**
- Full validation at schema, service, and API layers
- Comprehensive error handling
- Type hints throughout
- Clear docstrings

✅ **Testing**
- 10 schema validation tests (all passed)
- 7 end-to-end database tests (all passed)
- Duplicate detection verified
- Database persistence verified

✅ **Database**
- Migration created and applied
- Schema updated to nullable
- Zero data loss
- Reversible with downgrade

✅ **Backward Compatibility**
- Existing PRICE alerts still work
- Existing requests with condition still accepted
- No breaking changes to API contract
- Case-insensitive handling preserved

---

**Status:** ✅ Ready for Production  
**Date:** 2026-04-02  
**All Tests:** PASSING (17/17)
