#!/usr/bin/env python3
"""
Stock Sentinel - REAL RUNTIME COMPREHENSIVE TEST
Tests all actual APIs with correct endpoints
"""

import requests
import json
import time
from typing import Dict, List, Tuple, Optional
import sys

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3001"
TIMEOUT = 10

# Results
results = {
    "test_summary": {"total": 0, "passed": 0, "failed": 0, "warnings": 0},
    "apis": {},
    "failures": [],
    "performance": {},
}

class C:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def test(method, path, name, data=None, expect_status=200, expect_in_response=None):
    """Test an endpoint"""
    results["test_summary"]["total"] += 1
    url = f"{BASE_URL}{path}"
    start = time.time()
    
    try:
        if method == "GET":
            r = requests.get(url, timeout=TIMEOUT)
        elif method == "POST":
            r = requests.post(url, json=data, timeout=TIMEOUT)
        else:
            r = requests.request(method, url, json=data, timeout=TIMEOUT)
        
        elapsed = (time.time() - start) * 1000
        results["performance"][name] = {"ms": elapsed, "status": r.status_code}
        
        # Check status
        if r.status_code != expect_status:
            print(f"{C.RED}✗ FAIL{C.END}: {name} - Expected {expect_status}, got {r.status_code}")
            results["test_summary"]["failed"] += 1
            results["failures"].append(f"{name}: {r.status_code}")
            results["apis"][name] = {"status": r.status_code, "ms": elapsed}
            return False
        
        # Check performance
        if elapsed > 1000:
            print(f"{C.YELLOW}⚠{C.END} {name}: {elapsed:.0f}ms (slow)")
            results["test_summary"]["warnings"] += 1
        else:
            print(f"{C.GREEN}✓{C.END} {name}: {r.status_code} - {elapsed:.0f}ms")
        
        results["test_summary"]["passed"] += 1
        results["apis"][name] = {"status": r.status_code, "ms": elapsed}
        return True
        
    except requests.Timeout:
        print(f"{C.RED}✗ TIMEOUT{C.END}: {name}")
        results["test_summary"]["failed"] += 1
        results["failures"].append(f"{name}: TIMEOUT")
        return False
    except Exception as e:
        print(f"{C.RED}✗ ERROR{C.END}: {name} - {str(e)[:50]}")
        results["test_summary"]["failed"] += 1
        results["failures"].append(f"{name}: {str(e)[:50]}")
        return False

def section(title):
    print(f"\n{C.CYAN}{C.BOLD}{title}{C.END}\n")

if __name__ == "__main__":
    print(f"\n{C.BOLD}{C.CYAN}═══════════════════════════════════════════════════════════")
    print(f"STOCK SENTINEL - REAL RUNTIME TEST (CORRECTED ENDPOINTS)")
    print(f"═══════════════════════════════════════════════════════════{C.END}\n")
    
    # ==============================================
    # 1. HEALTH & BASIC ENDPOINTS
    # ==============================================
    section("1️⃣  HEALTH CHECK & BASIC ENDPOINTS")
    test("GET", "/api/health", "Health: Status Check", expect_status=200)
    test("GET", "/docs", "API: OpenAPI Docs", expect_status=200)
    
    # ==============================================
    # 2. AUTHENTICATION
    # ==============================================
    section("2️⃣  AUTHENTICATION API")
    test("POST", "/api/auth/register", "Auth: Register (invalid email)", 
         data={"email": "not-email", "password": "test123", "full_name": "Test"},
         expect_status=422)
    test("POST", "/api/auth/login", "Auth: Login (empty)", data={}, expect_status=422)
    
    # ==============================================
    # 3. SEARCH & STOCK LOOKUP
    # ==============================================
    section("3️⃣  SEARCH & STOCK LOOKUP")
    test("GET", "/api/search?q=AAPL", "Search: AAPL", expect_status=200)
    test("GET", "/api/search?q=", "Search: Empty Query", expect_status=422)
    test("GET", "/api/stock/AAPL/quote", "Stock: Quote (AAPL)", expect_status=200)
    test("GET", "/api/stock/INVALID123ABC/quote", "Stock: Quote (Invalid Symbol)", expect_status=404)
    test("GET", "/api/stock/AAPL", "Stock: Candles (AAPL)", expect_status=200)
    
    # ==============================================
    # 4. NEWS ENDPOINTS
    # ==============================================
    section("4️⃣  NEWS API")
    test("GET", "/api/news", "News: Get All", expect_status=200)
    test("GET", "/api/news?limit=5", "News: With Limit", expect_status=200)
    test("GET", "/api/news?limit=-1", "News: Negative Limit", expect_status=422)
    test("GET", "/api/news/search?q=", "News: Empty Search", expect_status=200)  # Returns 200 with empty
    
    # ==============================================
    # 5. STOCKS EXTENDED (MARKET DATA)
    # ==============================================
    section("5️⃣  MARKET DATA & STOCKS EXTENDED")
    test("GET", "/api/stocks/live", "Stocks: Live Ribbon", expect_status=200)
    test("GET", "/api/stocks/live/quotes", "Stocks: Live Quotes", expect_status=200)
    test("GET", "/api/stocks/AAPL/price", "Stocks: AAPL Price", expect_status=200)
    test("GET", "/api/stocks/AAPL", "Stocks: AAPL Details", expect_status=200)
    test("GET", "/api/stocks/market-summary/overview", "Stocks: Market Summary", expect_status=200)
    
    # ==============================================
    # 6. PROTECTED ENDPOINTS (SHOULD FAIL WITHOUT AUTH)
    # ============================================== 
    section("6️⃣  PROTECTED ENDPOINTS (NO AUTH)")
    test("GET", "/api/watchlist", "Watchlist: Get (no auth)", expect_status=401)
    test("GET", "/api/portfolio", "Portfolio: Get (no auth)", expect_status=401)
    test("GET", "/api/alerts", "Alerts: Get (no auth)", expect_status=401)
    test("GET", "/api/dashboard/data", "Dashboard: Data (no auth)", expect_status=401)
    
    # ==============================================
    # 7. PERFORMANCE SUMMARY
    # ==============================================
    section("7️⃣  PERFORMANCE SUMMARY")
    
    # Sort by speed
    sorted_perf = sorted(results["performance"].items(), key=lambda x: x[1]["ms"], reverse=True)
    print("Slowest endpoints:")
    for name, perf in sorted_perf[:5]:
        if perf["ms"] > 1000:
            print(f"  {C.YELLOW}⚠{C.END} {name}: {perf['ms']:.0f}ms")
        else:
            print(f"  {name}: {perf['ms']:.0f}ms")
    
    # ==============================================
    # 8. FRONTEND CHECK
    # ==============================================
    section("8️⃣  FRONTEND SERVER CHECK")
    try:
        r = requests.get(FRONTEND_URL, timeout=5)
        if r.status_code == 200:
            print(f"{C.GREEN}✓{C.END} Frontend: Responding ({r.status_code})")
            results["test_summary"]["passed"] += 1
        else:
            print(f"{C.YELLOW}⚠{C.END} Frontend: Unexpected {r.status_code}")
            results["test_summary"]["warnings"] += 1
    except Exception as e:
        print(f"{C.RED}✗{C.END} Frontend: Not responding - {str(e)[:50]}")
        results["test_summary"]["failed"] += 1
    
    # ==============================================
    # 9. FINAL REPORT
    # ==============================================
    s = results["test_summary"]
    print(f"\n{C.BOLD}{C.CYAN}═══════════════════════════════════════════════════════════")
    print(f"FINAL TEST REPORT")
    print(f"═══════════════════════════════════════════════════════════{C.END}\n")
    
    print(f"Total Tests:  {s['total']}")
    print(f"{C.GREEN}Passed:      {s['passed']}{C.END}")
    print(f"{C.RED}Failed:      {s['failed']}{C.END}")
    print(f"{C.YELLOW}Warnings:    {s['warnings']}{C.END}\n")
    
    if s["failed"] > 0:
        print(f"Failed tests:")
        for failure in results["failures"]:
            print(f"  {C.RED}✗{C.END} {failure}")
        print()
    
    # Calculate score
    score = min(100, (s["passed"] / s["total"] * 100)) if s["total"] > 0 else 0
    score = max(0, score - (s["warnings"] * 2) - (s["failed"] * 5))
    
    print(f"{C.BOLD}SCORE: {score:.0f}/100{C.END}")
    
    if score >= 85:
        print(f"{C.GREEN}✓ PRODUCTION READY{C.END}")
    elif score >= 70:
        print(f"{C.YELLOW}⚠ NEEDS ATTENTION{C.END}")
    else:
        print(f"{C.RED}✗ CRITICAL ISSUES{C.END}")
    
    # Save results
    with open("RUNTIME_TEST_RESULTS.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to RUNTIME_TEST_RESULTS.json\n")
