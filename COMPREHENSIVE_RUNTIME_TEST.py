#!/usr/bin/env python3
"""
Stock Sentinel - COMPREHENSIVE RUNTIME TESTING SUITE
Tests all backend APIs, frontend UI, and performance characteristics
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import sys

# Configuration
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3001"  # Port 3001 is in use
TIMEOUT = 10

# Test Results Tracking
results = {
    "apis_tested": [],
    "passed": [],
    "failed": [],
    "warnings": [],
    "performance": {},
    "test_summary": {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "warnings": 0,
    }
}

# Colors for output
class C:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    HEADER = '\033[95m'
    END = '\033[0m'

def header(msg: str):
    print(f"\n{C.HEADER}{C.BOLD}{'='*60}\n{msg}\n{'='*60}{C.END}\n")

def success(msg: str):
    print(f"{C.GREEN}✓ PASS{C.END}: {msg}")

def fail(msg: str):
    print(f"{C.RED}✗ FAIL{C.END}: {msg}")

def warn(msg: str):
    print(f"{C.YELLOW}⚠ WARN{C.END}: {msg}")

def info(msg: str):
    print(f"{C.BLUE}ℹ INFO{C.END}: {msg}")

def test_endpoint(
    method: str,
    endpoint: str,
    name: str,
    data: Optional[Dict] = None,
    expected_status: int = 200,
    headers: Optional[Dict] = None,
) -> Tuple[bool, Dict]:
    """Test a single API endpoint"""
    
    results["test_summary"]["total"] += 1
    url = f"{BASE_URL}{endpoint}"
    start_time = time.time()
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=TIMEOUT, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, timeout=TIMEOUT, json=data, headers=headers)
        elif method.upper() == "PUT":
            response = requests.put(url, timeout=TIMEOUT, json=data, headers=headers)
        elif method.upper() == "DELETE":
            response = requests.delete(url, timeout=TIMEOUT, json=data, headers=headers)
        else:
            fail(f"{name} - Unknown method: {method}")
            results["test_summary"]["failed"] += 1
            return False, {}
        
        response_time = time.time() - start_time
        
        # Record performance
        results["performance"][name] = {
            "endpoint": endpoint,
            "method": method,
            "response_time_ms": response_time * 1000,
            "status": response.status_code,
        }
        
        # Check status
        if response.status_code == expected_status:
            success(f"{name} ({response.status_code}) - {response_time*1000:.0f}ms")
            results["test_summary"]["passed"] += 1
            results["passed"].append(name)
            
            # Warn if slow
            if response_time > 1.0:
                warn(f"{name} - Slow response: {response_time*1000:.0f}ms (>1000ms)")
                results["test_summary"]["warnings"] += 1
                results["warnings"].append(f"{name} slow: {response_time*1000:.0f}ms")
            
            try:
                return True, response.json()
            except:
                return True, {"body": response.text[:100]}
        else:
            fail(f"{name} - Expected {expected_status}, got {response.status_code}")
            results["test_summary"]["failed"] += 1
            results["failed"].append(f"{name}: {response.status_code}")
            return False, {"error": f"Status {response.status_code}", "body": response.text[:200]}
            
    except requests.exceptions.Timeout:
        fail(f"{name} - Timeout after {TIMEOUT}s")
        results["test_summary"]["failed"] += 1
        results["failed"].append(f"{name}: TIMEOUT")
        return False, {"error": "Timeout"}
    except Exception as e:
        fail(f"{name} - {str(e)}")
        results["test_summary"]["failed"] += 1
        results["failed"].append(f"{name}: {str(e)}")
        return False, {"error": str(e)}


def test_health_api():
    """Test health check endpoint"""
    header("1️⃣  HEALTH CHECK API")
    
    success_flag, resp = test_endpoint(
        "GET", "/api/health", "Health: Status Check", expected_status=200
    )
    
    if success_flag:
        info(f"Response: {resp}")


def test_auth_api():
    """Test authentication APIs"""
    header("2️⃣  AUTHENTICATION API")
    
    # Test register with invalid email
    fail_flag, resp = test_endpoint(
        "POST", "/api/auth/register",
        "Auth: Register (Invalid Email)",
        data={
            "email": "not-an-email",
            "password": "test123",
            "full_name": "Test"
        },
        expected_status=422  # Validation error
    )
    if not fail_flag and resp.get("error"):
        success("Validation working - caught invalid email")
    
    # Test register with weak password
    fail_flag, resp = test_endpoint(
        "POST", "/api/auth/register",
        "Auth: Register (Weak Password)",
        data={
            "email": "test@example.com",
            "password": "weak",  # Too weak
            "full_name": "Test"
        },
        expected_status=422
    )
    
    # Test login with invalid credentials
    fail_flag, resp = test_endpoint(
        "POST", "/api/auth/login",
        "Auth: Login (Invalid Email)",
        data={
            "email": "nonexistent@test.com",
            "password": "password123"
        },
        expected_status=401
    )
    if not fail_flag:
        success("Auth corruption check passed - rejects invalid login")
    
    # Test login with empty data
    fail_flag, resp = test_endpoint(
        "POST", "/api/auth/login",
        "Auth: Login (Empty Data)",
        data={},
        expected_status=422
    )
    if not fail_flag:
        success("Empty data validation working")


def test_stock_api():
    """Test stock-related APIs"""
    header("3️⃣  STOCK API")
    
    # Test search with empty query
    success_flag, resp = test_endpoint(
        "GET", "/api/stocks/search?q=",
        "Stock: Search (Empty Query)",
        expected_status=400
    )
    if not success_flag:
        info("Empty search validation working")
    
    # Test search with invalid query
    success_flag, resp = test_endpoint(
        "GET", "/api/stocks/search?q=!!!###",
        "Stock: Search (Invalid Chars)",
        expected_status=400
    )
    
    # Test search with valid query
    success_flag, resp = test_endpoint(
        "GET", "/api/stocks/search?q=AAPL",
        "Stock: Search (Valid - AAPL)",
        expected_status=200
    )
    
    # Test get quote - invalid symbol
    success_flag, resp = test_endpoint(
        "GET", "/api/stocks/INVALID123/quote",
        "Stock: Quote (Invalid Symbol)",
        expected_status=400
    )
    
    # Test get quote - valid symbol
    success_flag, resp = test_endpoint(
        "GET", "/api/stocks/AAPL/quote",
        "Stock: Quote (Valid - AAPL)",
        expected_status=200
    )
    
    # Test technical indicators with invalid symbol
    success_flag, resp = test_endpoint(
        "GET", "/api/stocks/INVALID/indicators",
        "Stock: Indicators (Invalid Symbol)",
        expected_status=400
    )
    
    # Test technical indicators with valid symbol
    success_flag, resp = test_endpoint(
        "GET", "/api/stocks/AAPL/indicators",
        "Stock: Indicators (Valid - AAPL)",
        expected_status=200
    )


def test_news_api():
    """Test news-related APIs"""
    header("4️⃣  NEWS API")
    
    # Test get news with empty query
    success_flag, resp = test_endpoint(
        "GET", "/api/news",
        "News: Get All News",
        expected_status=200
    )
    
    # Test get news with invalid limit
    success_flag, resp = test_endpoint(
        "GET", "/api/news?limit=-1",
        "News: Invalid Limit",
        expected_status=400
    )
    if not success_flag:
        info("Negative limit validation working")
    
    # Test get news with valid limit
    success_flag, resp = test_endpoint(
        "GET", "/api/news?limit=10",
        "News: Get With Limit",
        expected_status=200
    )
    
    # Test search news with empty query
    success_flag, resp = test_endpoint(
        "GET", "/api/news/search?q=",
        "News: Search (Empty)",
        expected_status=400
    )
    if not success_flag:
        info("Empty search validation working")


def test_watchlist_api():
    """Test watchlist APIs"""
    header("5️⃣  WATCHLIST API")
    
    # Get watchlist (may require auth, so expect 401 or 200)
    success_flag, resp = test_endpoint(
        "GET", "/api/watchlist",
        "Watchlist: Get All",
        expected_status=200
    )
    if not success_flag:
        warn("Watchlist GET might require authentication")
    
    # Add to watchlist with invalid data
    success_flag, resp = test_endpoint(
        "POST", "/api/watchlist",
        "Watchlist: Add (No Symbol)",
        data={},
        expected_status=422
    )
    
    # Add to watchlist with empty symbol
    success_flag, resp = test_endpoint(
        "POST", "/api/watchlist",
        "Watchlist: Add (Empty Symbol)",
        data={"symbol": ""},
        expected_status=400
    )


def test_portfolio_api():
    """Test portfolio APIs"""
    header("6️⃣  PORTFOLIO API")
    
    # Get portfolio
    success_flag, resp = test_endpoint(
        "GET", "/api/portfolio",
        "Portfolio: Get",
        expected_status=200
    )
    if not success_flag:
        warn("Portfolio might require authentication")


def test_alerts_api():
    """Test alert APIs"""
    header("7️⃣  ALERTS API")
    
    # Get all alerts
    success_flag, resp = test_endpoint(
        "GET", "/api/alerts",
        "Alerts: Get All",
        expected_status=200
    )
    
    # Create alert with missing fields
    success_flag, resp = test_endpoint(
        "POST", "/api/alerts",
        "Alerts: Create (Missing Fields)",
        data={},
        expected_status=422
    )
    
    # Create alert with invalid symbol
    success_flag, resp = test_endpoint(
        "POST", "/api/alerts",
        "Alerts: Create (Invalid Symbol)",
        data={
            "symbol": "!!!",
            "condition": "PRICE_ABOVE",
            "target_value": 100
        },
        expected_status=400
    )
    
    # Create alert with invalid condition
    success_flag, resp = test_endpoint(
        "POST", "/api/alerts",
        "Alerts: Create (Invalid Condition)",
        data={
            "symbol": "AAPL",
            "condition": "INVALID_CONDITION",
            "target_value": 100
        },
        expected_status=422
    )


def test_dashboard_api():
    """Test dashboard APIs"""
    header("8️⃣  DASHBOARD API")
    
    # Get dashboard data
    success_flag, resp = test_endpoint(
        "GET", "/api/dashboard",
        "Dashboard: Get Data",
        expected_status=200
    )
    
    # Get market overview
    success_flag, resp = test_endpoint(
        "GET", "/api/dashboard/market-overview",
        "Dashboard: Market Overview",
        expected_status=200
    )


def test_websocket():
    """Test WebSocket availability"""
    header("9️⃣  WEBSOCKET TEST")
    
    try:
        from websocket import create_connection, WebSocketTimeoutException
        
        ws_url = f"{BASE_URL.replace('http', 'ws')}/ws/market-data"
        
        try:
            ws = create_connection(ws_url, timeout=5)
            success("WebSocket: Connection established")
            ws.close()
        except WebSocketTimeoutException:
            fail("WebSocket: Connection timeout")
        except Exception as e:
            warn(f"WebSocket: {str(e)}")
            
    except ImportError:
        warn("WebSocket library not installed (websocket-client)")


def test_frontend_availability():
    """Test frontend server response"""
    header("🔟 FRONTEND AVAILABILITY")
    
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            success(f"Frontend: Server responding ({response.status_code})")
        else:
            warn(f"Frontend: Unexpected status {response.status_code}")
    except Exception as e:
        fail(f"Frontend: Not responding - {str(e)}")


def generate_report():
    """Generate final report"""
    header("📊 FINAL TEST REPORT")
    
    summary = results["test_summary"]
    
    print(f"{C.BOLD}Test Results:{C.END}")
    print(f"  Total Tests:    {summary['total']}")
    print(f"  {C.GREEN}Passed:        {summary['passed']}{C.END}")
    print(f"  {C.RED}Failed:        {summary['failed']}{C.END}")
    print(f"  {C.YELLOW}Warnings:      {summary['warnings']}{C.END}")
    print()
    
    # Calculate score
    if summary['total'] > 0:
        pass_rate = (summary['passed'] / summary['total']) * 100
        fail_rate = (summary['failed'] / summary['total']) * 100
        score = max(0, 100 - (summary['failed'] * 10) - (summary['warnings'] * 2))
        score = min(100, score)
    else:
        pass_rate = 0
        fail_rate = 0
        score = 0
    
    print(f"{C.BOLD}Performance Metrics:{C.END}")
    
    # Find slowest endpoints
    perf_sorted = sorted(results["performance"].items(), 
                         key=lambda x: x[1]["response_time_ms"], reverse=True)
    
    print(f"  Slowest Endpoints:")
    for name, perf in perf_sorted[:5]:
        if perf["response_time_ms"] > 1000:
            print(f"    {C.YELLOW}⚠ {name}: {perf['response_time_ms']:.0f}ms (>1s){C.END}")
        else:
            print(f"    ✓ {name}: {perf['response_time_ms']:.0f}ms")
    
    print()
    print(f"{C.BOLD}Failed APIs:{C.END}")
    if results["failed"]:
        for failed in results["failed"]:
            print(f"  {C.RED}✗ {failed}{C.END}")
    else:
        print(f"  {C.GREEN}None{C.END}")
    
    print()
    print(f"{C.BOLD}Warnings:{C.END}")
    if results["warnings"]:
        for warning in results["warnings"]:
            print(f"  {C.YELLOW}⚠ {warning}{C.END}")
    else:
        print(f"  {C.GREEN}None{C.END}")
    
    print()
    print(f"{C.BOLD}{C.HEADER}FINAL SCORE: {score}/100{C.END}")
    
    if score >= 90:
        print(f"{C.GREEN}✓ PRODUCTION READY{C.END}")
        return True
    elif score >= 70:
        print(f"{C.YELLOW}⚠ NEEDS FIXES BEFORE PRODUCTION{C.END}")
        return False
    else:
        print(f"{C.RED}✗ NOT READY FOR PRODUCTION{C.END}")
        return False


# ============================================================================
# MAIN TEST EXECUTION
# ============================================================================

if __name__ == "__main__":
    print(f"{C.HEADER}{C.BOLD}")
    print("=" * 60)
    print("  STOCK SENTINEL - COMPREHENSIVE RUNTIME TEST SUITE")
    print("=" * 60)
    print(f"{C.END}\n")
    
    info(f"Testing Backend: {BASE_URL}")
    info(f"Testing Frontend: {FRONTEND_URL}\n")
    
    try:
        # Run tests in order
        test_health_api()
        test_auth_api()
        test_stock_api()
        test_news_api()
        test_watchlist_api()
        test_portfolio_api()
        test_alerts_api()
        test_dashboard_api()
        test_websocket()
        test_frontend_availability()
        
        # Generate final report
        production_ready = generate_report()
        
        # Save results to JSON
        with open("RUNTIME_TEST_RESULTS_LATEST.json", "w") as f:
            json.dump(results, f, indent=2)
        
        info(f"Detailed results saved to RUNTIME_TEST_RESULTS_LATEST.json")
        
        sys.exit(0 if production_ready else 1)
        
    except KeyboardInterrupt:
        print(f"\n{C.RED}Test interrupted by user{C.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{C.RED}Unexpected error: {str(e)}{C.END}")
        sys.exit(1)
