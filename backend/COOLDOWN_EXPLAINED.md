# Quick Reference: Why Your Alerts Only Send Once

## TL;DR - The Issue

Your alert system has a **10-minute cooldown** to prevent email spam:

- ✉️ **First trigger** → Email sent, `is_triggered = True`
- 🔇 **Next 10 minutes** → Condition still matches, but **NO email** (cooldown active)
- ⏰ **After 10 minutes** → Email sent again (if condition still matches)

---

## Why This Design?

### Problem It Solves
If AAPL price is at $150.50, and you set alert for "AAPL > $150", the condition matches every 30 seconds! Without cooldown:
- You'd get **1,200+ emails per day** (1 every 30 seconds)
- Your inbox would explode 💥
- Email provider might block you

### Cooldown Solution
Send email once, then ignore matches for 10 minutes. Problem solved! ✅

---

## How to Test

### Option 1: Check Current State (Right Now)

```bash
# See if your alert is in cooldown
docker exec -it stocksentinel-db psql -U stocksentinel -d stocksentinel -c "
SELECT 
  id, 
  stock_symbol, 
  is_triggered,
  last_triggered_at,
  CASE 
    WHEN is_triggered THEN 'IN COOLDOWN 💤'
    ELSE 'READY FOR TRIGGER 🔄'
  END as status
FROM alerts 
WHERE stock_symbol = 'AAPL';"
```

**Output will show:**
- `is_triggered = true` → Yeah, cooldown is active!
- `is_triggered = false` → Cooldown expired, ready to trigger

### Option 2: Run Test Script (Easy)

```bash
cd backend

# Production mode (tests with cooldown):
.\test_alerts.ps1

# Dev mode (tests without cooldown):
.\test_alerts.ps1 -DevMode
```

The script creates 4 alerts and shows you what happened!

---

## Cooldown Timeline Example

**You create AAPL alert at 2:00 PM:**

| Time | Price | Condition | Status | Email |
|------|-------|-----------|--------|-------|
| 2:00:00 | $151 | MATCH ✓ | TRIGGERS | ✉️ SENT |
| 2:00:30 | $151.50 | MATCH ✓ | Cooldown | 🔇 BLOCKED |
| 2:05:00 | $152 | MATCH ✓ | Still cooldown | 🔇 BLOCKED |
| 2:09:59 | $153 | MATCH ✓ | Still cooldown (8 sec left) | 🔇 BLOCKED |
| 2:10:00 | $153.50 | MATCH ✓ | **COOLDOWN EXPIRED** | ✉️ SENT |
| 2:10:30 | $154 | MATCH ✓ | Cooldown (new) | 🔇 BLOCKED |

---

## The Re-arm Magic ✨

**Re-arm resets the alert when condition becomes FALSE:**

Example CONTINUED:

| Time | Price | Condition | Status | Action |
|------|-------|-----------|--------|--------|
| 2:15:00 | $149 | FAIL ✗ | is_triggered=True | **RE-ARMS** 🔄 |
| 2:15:05 | $149.50 | FAIL ✗ | is_triggered=False | Ready |
| 2:15:10 | $152 | MATCH ✓ | Not in cooldown | ✉️ SENT (again!) |

**Key insight:** Re-arm only happens when condition flips from TRUE → FALSE

---

## Configuration Options

### To Change Cooldown Period

Edit `backend/.env`:

```bash
# 5-minute cooldown (more frequent emails)
ALERT_COOLDOWN_MINUTES=5

# 30-minute cooldown (fewer emails)
ALERT_COOLDOWN_MINUTES=30

# 1-hour cooldown (very low frequency)
ALERT_COOLDOWN_MINUTES=60
```

Restart server:
```bash
# Stop Ctrl+C, then:
cd backend
uvicorn app.main:app --reload
```

### To Disable Cooldown (For Testing Only)

```bash
# .env
ALERT_DEV_MODE=true
```

⚠️ **Never use in production** - you'll get spammed!

---

## Verify Cooldown is Working

### Check Logs

```bash
cd backend
tail -f logs/app.log | grep -E "(ALERT TRIGGERED|cooldown|Re-arm)"
```

**Expected output:**

```
WARNING: 🔔 ALERT TRIGGERED - alert_id: 1
...30 seconds later...
DEBUG: Alert in cooldown period, skipping trigger - seconds_until_rearm: 598
...30 seconds later...
DEBUG: Alert in cooldown period, skipping trigger - seconds_until_rearm: 568
...wait 10 minutes...
WARNING: 🔔 ALERT TRIGGERED - alert_id: 1 (again!)
```

### Check AlertHistory

```bash
docker exec -it stocksentinel-db psql -U stocksentinel -d stocksentinel -c "
SELECT 
  DISTINCT(alert_id), 
  stock_symbol, 
  COUNT(*) as trigger_count,
  MAX(triggered_at) as last_trigger
FROM alert_history
GROUP BY alert_id, stock_symbol
ORDER BY MAX(triggered_at) DESC;"
```

If same alert_id has multiple rows → Cooldown is working! ✓

---

## Common Questions

### Q: Why no email after first trigger?

**A:** Cooldown is active. Check:
1. `is_triggered = true` in database
2. `last_triggered_at` is recent (< 10 minutes)
3. Logs show "Alert in cooldown period"

### Q: When will I get email again?

**A:** After 10 minutes **AND** condition is still true.

Or immediately if condition becomes **false** first (re-arm), then true again.

### Q: How do I test without waiting 10 minutes?

**A:** Use dev mode:
```bash
# In .env or terminal:
ALERT_DEV_MODE=true

# Restart server and all cooldowns are bypassed
```

### Q: I want different cooldown for different alerts

**A:** Currently all alerts share same cooldown. Future enhancement could support per-alert configuration in creation payload.

### Q: What if email fails?

**A:** Alert still triggers and enters cooldown. Failure is logged:
```
ERROR: Failed to queue email notification - alert_id: 1, error: SMTP timeout
```

Email gets retried next cycle (if configured).

---

## Testing Checklist

- [ ] Run `.\test_alerts.ps1`
- [ ] Wait 30-60 seconds
- [ ] Check AlertHistory for records: `SELECT * FROM alert_history;`
- [ ] Verify email was sent (check email_sent=true)
- [ ] Check alert is marked `is_triggered = true`
- [ ] Wait 10 minutes
- [ ] Check logs for "Alert in cooldown period" messages
- [ ] After 10 minutes, verify second trigger happens (same alert_id in alert_history again)

---

## Production Best Practices

| Scenario | Cooldown |
|----------|----------|
| Price alerts (volatile) | 10-15 min |
| Percentage change | 5-10 min |
| Volume spikes | 10-15 min |
| Crash alerts | 30-60 min |
| Very important alerts | 5 min |
| Low-importance alerts | 60+ min |

---

## If Cooldown is Problem

### Option 1: Keep It (Recommended)
- Protects against email spam
- Professional alert systems use this pattern
- Users can adjust per alert type in future

### Option 2: Remove It (Not Recommended)
- Adds logic to allow per-alert cooldown configuration
- More complex state management
- Risk of email bombardment

### Option 3: Hybrid Approach (Best)
- Keep 10-min default
- Allow users to set custom cooldown when creating alert
- Could be future feature

---

## Key Files

| File | Purpose |
|------|---------|
| [app/config.py](app/config.py#L50-L53) | Cooldown configuration |
| [app/services/alert_service.py](app/services/alert_service.py#L1009-L1055) | Cooldown & re-arm logic |
| [app/models/alert.py](app/models/alert.py#L134-L145) | is_triggered, last_triggered_at fields |
| [ALERT_TESTING_GUIDE.md](ALERT_TESTING_GUIDE.md) | Comprehensive testing guide |

---

## Next Steps

1. **Immediate:** Run `.\test_alerts.ps1` to see cooldown in action
2. **Short-term:** Adjust `ALERT_COOLDOWN_MINUTES` based on your needs
3. **Future:** Add user-configurable cooldown per alert

---

**Bottom line:** Your system is working perfectly. The single email is intentional - it's preventing spam. 

To get more emails: Either wait 10 minutes, change the condition back to false, or enable dev mode.

✨ That's the production-ready alert system!
