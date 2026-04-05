#!/usr/bin/env powershell
<#
QUICK START: Real-Time Indicators & Live Charts

This guide will help you test the complete real-time indicator system.
#>

# ============================================
# 1. START THE BACKEND
# ============================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "STEP 1: Starting FastAPI Backend" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Commands:"
Write-Host "  cd backend"
Write-Host "  python -m uvicorn app.main:app --reload"
Write-Host ""
Write-Host "Expected output:"
Write-Host "  INFO:     Uvicorn running on http://127.0.0.1:8000"
Write-Host "  INFO:     Application startup complete"
Write-Host ""

# ============================================
# 2. START THE FRONTEND
# ============================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "STEP 2: Starting Next.js Frontend (NEW TERMINAL)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Commands:"
Write-Host "  cd frontend"
Write-Host "  npm run dev"
Write-Host ""
Write-Host "Expected output:"
Write-Host "  ✓ Ready in 2.5s"
Write-Host "  ▲ http://localhost:3000"
Write-Host ""

# ============================================
# 3. TEST THE SYSTEM
# ============================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "STEP 3: Test Real-Time Indicators" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Open browser: http://localhost:3000"
Write-Host ""
Write-Host "2. Navigate to: /charts?symbol=AAPL"
Write-Host ""
Write-Host "3. You should see:"
Write-Host "   ✓ 🔴 LIVE badge (red pulse)"
Write-Host "   ✓ Price updates every 3-5 seconds"
Write-Host "   ✓ Price animates when it updates (zoom scale)"
Write-Host "   ✓ Main chart with 3 lines:"
Write-Host "     - Green line: Current price"
Write-Host "     - Blue line: SMA (Simple Moving Average)"
Write-Host "     - Orange line: EMA (Exponential Moving Average)"
Write-Host "   ✓ RSI chart below (0-100 range)"
Write-Host "   ✓ 3 indicator cards showing:"
Write-Host "     - SMA(20) with Above/Below status"
Write-Host "     - EMA(12) with Above/Below status"
Write-Host "     - RSI(14) with Overbought/Oversold/Neutral status"
Write-Host ""

# ============================================
# 4. CHECK WEBSOCKET CONNECTION
# ============================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "STEP 4: Verify WebSocket Connection" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Open browser console (F12) and check:"
Write-Host "   - No red errors"
Write-Host "   - '[WebSocket] Connected to AAPL' in console"
Write-Host ""
Write-Host "API Endpoint to check:"
Write-Host "   http://localhost:8000/ws/status"
Write-Host "   Should show active connections and streams"
Write-Host ""

# ============================================
# 5. TEST FEATURES
# ============================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "STEP 5: Interactive Testing" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Feature Tests:"
Write-Host ""
Write-Host "1. TOGGLE INDICATORS:"
Write-Host "   - Uncheck 'SMA 20': Blue line disappears"
Write-Host "   - Uncheck 'EMA 12': Orange line disappears"
Write-Host "   - Uncheck 'RSI': RSI chart disappears"
Write-Host ""
Write-Host "2. TIMEFRAME SELECTOR:"
Write-Host "   - Click '1D', '1W', '1M', '1Y' buttons"
Write-Host "   - Chart reloads with mock historical data"
Write-Host "   - Indicators recalculate for selected period"
Write-Host ""
Write-Host "3. PRICE FLASH EFFECT:"
Write-Host "   - Watch the price badge"
Write-Host "   - When price updates, it scales up slightly"
Write-Host "   - Scales back down smoothly (300ms animation)"
Write-Host ""
Write-Host "4. MOBILE RESPONSIVE:"
Write-Host "   - Open DevTools (F12)"
Write-Host "   - Click device toolbar (mobile view)"
Write-Host "   - Charts should stack responsively"
Write-Host ""

# ============================================
# 6. MONITOR PERFORMANCE
# ============================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "STEP 6: Performance Monitoring" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Open DevTools (F12) Performance Tab:"
Write-Host ""
Write-Host "1. Click Record (red dot)"
Write-Host "2. Wait 5-10 seconds"
Write-Host "3. Stop recording"
Write-Host ""
Write-Host "Expected metrics:"
Write-Host "   - Update frequency: ~1 per second (throttled)"
Write-Host "   - Frame rate: Smooth 60fps"
Write-Host "   - Memory: Stable (no growth)"
Write-Host "   - CPU: <5% between updates"
Write-Host ""

# ============================================
# 7. INSPECT WEBSOCKET MESSAGES
# ============================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "STEP 7: Inspect WebSocket Messages" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "In DevTools (F12):"
Write-Host "  1. Open Network tab"
Write-Host "  2. Filter: WS (WebSocket)"
Write-Host "  3. Click the connection"
Write-Host "  4. See Messages tab"
Write-Host ""
Write-Host "Each message should contain:"
Write-Host '{
  "symbol": "AAPL",
  "price": 180.25,
  "high": 182.50,
  "low": 179.80,
  "volume": 52000000,
  "timestamp": "2026-01-01T12:00:00Z",
  "sma": 178.10,
  "ema": 179.00,
  "rsi": 65.5
}'
Write-Host ""

# ============================================
# 8. TROUBLESHOOTING
# ============================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TROUBLESHOOTING" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Issue: No price updates"
Write-Host "Solution:"
Write-Host "  1. Check backend log for errors"
Write-Host "  2. Verify yfinance can fetch prices: python -c 'import yfinance; yfinance.Ticker('AAPL').history()'"
Write-Host "  3. Check WebSocket connection in browser console"
Write-Host ""
Write-Host "Issue: Indicators show as '—'"
Write-Host "Solution:"
Write-Host "  1. Wait 20-30 seconds for enough history"
Write-Host "  2. RSI needs 14 prices, SMA needs 20, EMA needs 12"
Write-Host "  3. Check backend logs for calculation errors"
Write-Host ""
Write-Host "Issue: High memory usage"
Write-Host "Solution:"
Write-Host "  1. Close other browser tabs"
Write-Host "  2. Check DevTools Memory for leaks"
Write-Host "  3. Verify chart data limited to 100 points"
Write-Host ""
Write-Host "Issue: High CPU usage"
Write-Host "Solution:"
Write-Host "  1. Check throttling is working (max 1 update/sec)"
Write-Host "  2. Verify Recharts animation disabled"
Write-Host "  3. Check browser DevTools for inefficient renders"
Write-Host ""

# ============================================
# 9. API ENDPOINTS
# ============================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "API ENDPOINTS (Backend)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "WebSocket Endpoints:"
Write-Host "  ws://localhost:8000/ws/stocks/{SYMBOL}"
Write-Host "  Example: ws://localhost:8000/ws/stocks/AAPL"
Write-Host ""
Write-Host "HTTP Endpoints:"
Write-Host "  GET http://localhost:8000/ws/status"
Write-Host "  Response: { 'AAPL': 3, 'MSFT': 1 } (connection counts)"
Write-Host ""

# ============================================
# 10. TESTING MULTIPLE SYMBOLS
# ============================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ADVANCED: Multiple Symbols" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Open multiple chart tabs:"
Write-Host "  /charts?symbol=AAPL"
Write-Host "  /charts?symbol=MSFT"
Write-Host "  /charts?symbol=GOOGL"
Write-Host ""
Write-Host "Each should:"
Write-Host "  - Connect to separate WebSocket"
Write-Host "  - Stream independently"
Write-Host "  - Have own active connection in /ws/status"
Write-Host ""

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
