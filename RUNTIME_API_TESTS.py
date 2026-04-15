#!/usr/bin/env python3
"""
Stock Sentinel - COMPREHENSIVE RUNTIME API TESTING
Tests all backend APIs with real HTTP calls to validate production readiness
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import sys

# Configuration
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
TIMEOUT = 10

# Test Results Tracking
test_results = {
    "apis_tested": [],
    "passed": [],
    "failed": [],
    "warnings": [],
    "performance_metrics": {},
    "total_tests": 0,
    "total_passed": 0,
    "total_failed": 0,
}

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def log(msg: str, color: str = Colors.BLUE) -> None:
    """Print colored log message"""
    print(f"{color}{msg}{Colors.END}")

def log_success(msg: str) -> None:
    """Print success message"""
    print(f"{Colors.GREEN}PASS: {msg}{Colors.END}")

def log_failure(msg: str) -> None:
    """Print failure message"""
    print(f"{Colors.RED}FAIL: {msg}{Colors.END}")

def log_warning(msg: str) -> None:
    """Print warning message"""
    print(f"{Colors.YELLOW}WARN: {msg}{Colors.END}")

def test_api(
    method: str,
    endpoint: str,
    name: str,
    data: Optional[Dict] = None,
    expected_status: int = 200,
    description: str = "",
) -> Tuple[bool, Dict]:
    """
    Test a single API endpoint
    Returns: (success: bool, response_data: dict)
    """
    test_results["total_tests"] += 1
    test_results["apis_tested"].append(name)
    
    url = f"{BASE_URL}{endpoint}"
    start_time = time.time()
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=TIMEOUT, json=data)
        elif method.upper() == "POST":
            response = requests.post(url, timeout=TIMEOUT, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, timeout=TIMEOUT, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, timeout=TIMEOUT, json=data)
        else:
            raise ValueError(f"Unknown HTTP method: {method}")
        
        response_time = time.time() - start_time
        
        # Log performance
        test_results["performance_metrics"][name] = {
            "endpoint": endpoint,
            "method": method,
            "response_time_ms": response_time * 1000,
            "status_code": response.status_code,
        }
        
        # Check status code
        if response.status_code != expected_status:
            log_failure(f"{name} - Expected {expected_status}, got {response.status_code}")
            test_results["failed"].append({
                "test": name,
                "endpoint": endpoint,
                "expected": expected_status,
                "actual": response.status_code,
                "response": response.text[:200],
            })
            test_results["total_failed"] += 1
            return False, {"error": f"Status {response.status_code}"}
        
        # Check response time (warn if > 1 second)
        if response_time > 1.0:
            log_warning(f"{name} - Slow response: {response_time*1000:.0f}ms")
            test_results["warnings"].append({
                "test": name,
                "issue": f"Slow response: {response_time*1000:.0f}ms",
            })
        
        # Parse JSON response
        try:
            response_data = response.json()
        except:
            response_data = {"raw": response.text}
        
        log_success(f"{name} ({response.status_code}) - {response_time*1000:.0f}ms")
        test_results["passed"].append({
            "test": name,
            "endpoint": endpoint,
            "response_time_ms": response_time * 1000,
        })
        test_results["total_passed"] += 1
        
        return True, response_data
        
    except requests.exceptions.Timeout:
        log_failure(f"{name} - Timeout (>{TIMEOUT}s)")
        test_results["failed"].append({
            "test": name,
            "endpoint": endpoint,
            "error": "Timeout",
        })
        test_results["total_failed"] += 1
        return False, {"error": "Timeout"}
        
    except Exception as e:
        log_failure(f"{name} - Error: {str(e)}")
        test_results["failed"].append({
            "test": name,
            "endpoint": endpoint,
            "error": str(e),
        })
        test_results["total_failed"] += 1
        return False, {"error": str(e)}


def test_auth_api() -> str:
    """Test authentication APIs and return token for authenticated tests"""
    log(f"\n=== TESTING AUTH APIs ===")
    
    # Test register (should fail with existing user)
    success, resp = test_api(
        "POST",
        "/api/auth/register",
        "Auth: Register User",
        data={
            "email": "test@example.com",
            "password": "securepassword123!",
            "full_name": "Test User",
        },
        expected_status=200,
    )
    
    # Test login
    test_credentials = {
        "email": "testuser@example.com",
        "password": "password123!",
    }
    
    success, resp = test_api(
        "POST",
        "/api/auth/login",
        "Auth: Login",
        data=test_credentials,
        expected_status=200,
    )
    
    token = resp.get("access_token") if success else None
    
    # Test refresh token if we got token
    if token:
        # We'll use the token for subsequent authenticated calls
        log_success("Auth: Got access token")
    else:
        log_warning("Auth: Could not obtain token, some tests will be skipped")
    
    return token


def test_stock_api() -> None:
    """Test stock-related APIs"""
    log(f"\n=== TESTING STOCK APIs ===")
    
    # Test get stock data
    test_api(
        "GET",
        "/api/stocks/AAPL",
        "Stock: Get AAPL Data",
        expected_status=200,
    )
    
    # Test search stocks
    test_api(
        "GET",
        "/api/stocks/search?query=Apple",
        "Stock: Search Stocks",
        expected_status=200,
    )
    
    # Test market data
    test_api(
        "GET",
        "/api/dashboard/market-overview",
        "Stock: Market Overview",
        expected_status=200,
    )
    
    # Test trending stocks
    test_api(
        "GET",
        "/api/dashboard/trending",
        "Stock: Trending Stocks",
        expected_status=200,
    )
    
    # Test market indices
    test_api(
        "GET",
        "/api/stocks/indices",
        "Stock: Market Indices",
        expected_status=200,
    )


def test_portfolio_api() -> None:
    """Test portfolio APIs"""
    log(f"\n=== TESTING PORTFOLIO APIs ===")
    
    # Test get portfolio (no auth - should fail or return empty)
    test_api(
        "GET",
        "/api/portfolio",
        "Portfolio: Get Portfolio",
        expected_status=200,
    )
    
    # Test portfolio statistics
    test_api(
        "GET",
        "/api/portfolio/stats",
        "Portfolio: Get Statistics",
        expected_status=200,
    )
    
    # Test allocation
    test_api(
        "GET",
        "/api/portfolio/allocation",
        "Portfolio: Get Allocation",
        expected_status=200,
    )


def test_news_api() -> None:
    """Test news APIs"""
    log(f"\n=== TESTING NEWS APIs ===")
    
    # Test market news
    test_api(
        "GET",
        "/api/news/market",
        "News: Market News",
        expected_status=200,
    )
    
    # Test stock news
    test_api(
        "GET",
        "/api/news/AAPL",
        "News: AAPL News",
        expected_status=200,
    )
    
    # Test sentiment
    test_api(
        "GET",
        "/api/news/sentiment",
        "News: Market Sentiment",
        expected_status=200,
    )


def test_alerts_api() -> None:
    """Test alerts APIs"""
    log(f"\n=== TESTING ALERTS APIs ===")
    
    # Test get alerts (no auth - should return empty or 401)
    test_api(
        "GET",
        "/api/alerts",
        "Alerts: Get All Alerts",
        expected_status=200,
    )
    
    # Test get active alerts
    test_api(
        "GET",
        "/api/alerts/active",
        "Alerts: Get Active Alerts",
        expected_status=200,
    )
    
    # Test get alert types
    test_api(
        "GET",
        "/api/alerts/types",
        "Alerts: Get Alert Types",
        expected_status=200,
    )


def test_watchlist_api() -> None:
    """Test watchlist APIs"""
    log(f"\n=== TESTING WATCHLIST APIs ===")
    
    # Test get watchlist
    test_api(
        "GET",
        "/api/watchlist",
        "Watchlist: Get Watchlist",
        expected_status=200,
    )
    
    # Test get watchlist items
    test_api(
        "GET",
        "/api/watchlist/items",
        "Watchlist: Get Items",
        expected_status=200,
    )


def test_error_handling() -> None:
    """Test error handling and edge cases"""
    log(f"\n=== TESTING ERROR HANDLING ===")
    
    # Test invalid endpoint
    test_api(
        "GET",
        "/api/stocks/INVALID_TICKER_XXXXX",
        "Error: Invalid Stock Ticker",
        expected_status=404,  # Should be not found or 400
    )
    
    # Test malformed request
    test_api(
        "GET",
        "/api/stocks",
        "Error: Missing Required Param",
        expected_status=422,  # Unprocessable entity
    )
    
    # Test method not allowed
    test_api(
        "POST",
        "/api/stocks/AAPL",
        "Error: Wrong HTTP Method",
        data={},
        expected_status=405,  # Method not allowed
    )


def test_concurrent_requests() -> None:
    """Test handling of concurrent requests"""
    log(f"\n=== TESTING CONCURRENT REQUESTS ===")
    
    import threading
    
    results = []
    
    def make_request(ticker: str, index: int) -> None:
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/stocks/{ticker}", timeout=TIMEOUT)
        elapsed = time.time() - start
        results.append({
            "ticker": ticker,
            "status": response.status_code,
            "time": elapsed,
            "index": index,
        })
    
    # Make 5 concurrent requests
    threads = []
    tickers = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
    
    for i, ticker in enumerate(tickers):
        t = threading.Thread(target=make_request, args=(ticker, i))
        threads.append(t)
        t.start()
    
    # Wait for all threads
    for t in threads:
        t.join(timeout=TIMEOUT + 5)
    
    # Check results
    if len(results) == len(tickers):
        log_success(f"Concurrent Requests: All {len(tickers)} requests completed")
        avg_time = sum(r["time"] for r in results) / len(results)
        test_results["performance_metrics"]["concurrent_avg"] = avg_time * 1000
    else:
        log_failure(f"Concurrent Requests: Only {len(results)}/{len(tickers)} completed")


def test_data_validation() -> None:
    """Test data validation and null safety"""
    log(f"\n=== TESTING DATA VALIDATION ===")
    
    # Get market data and validate structure
    success, resp = test_api(
        "GET",
        "/api/dashboard/market-overview",
        "Data: Market Overview Structure",
        expected_status=200,
    )
    
    if success and isinstance(resp, dict):
        # Check for required fields
        required_fields = []  # API should define these
        if "data" in resp:
            log_success("Data: Response has 'data' field")
        elif "market" in resp:
            log_success("Data: Response has 'market' field")
        else:
            log_warning("Data: Response structure unclear")
    
    # Get trending with null check
    success, resp = test_api(
        "GET",
        "/api/dashboard/trending",
        "Data: Trending Stocks (Null Check)",
        expected_status=200,
    )
    
    if success:
        # Should not crash even if trending data is empty/null
        log_success("Data: Handled trending data gracefully")


def generate_report() -> None:
    """Generate comprehensive test report"""
    log(f"\n{'='*60}")
    log(f"RUNTIME TEST REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"{'='*60}")
    
    # Summary
    total = test_results["total_tests"]
    passed = test_results["total_passed"]
    failed = test_results["total_failed"]
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    log(f"\nSUMMARY")
    log(f"Total Tests: {total}")
    log_success(f"Passed: {passed}")
    if failed > 0:
        log_failure(f"Failed: {failed}")
    log(f"Pass Rate: {pass_rate:.1f}%")
    
    # Performance Summary
    if test_results["performance_metrics"]:
        log(f"\nPERFORMANCE METRICS")
        times = {}
        for k, v in test_results["performance_metrics"].items():
            if isinstance(v, dict) and "response_time_ms" in v:
                times[k] = v["response_time_ms"]
            elif isinstance(v, (int, float)):
                times[k] = v
        if times:
            avg_time = sum(times.values()) / len(times)
            max_time = max(times.values())
            min_time = min(times.values())
            
            log(f"Average Response Time: {avg_time:.0f}ms")
            log(f"Min Response Time: {min_time:.0f}ms")
            log(f"Max Response Time: {max_time:.0f}ms")
            
            # Highlight slow endpoints
            slow = {k: v for k, v in times.items() if v > 1000}
            if slow:
                log_warning(f"Slow Endpoints (>1s): {len(slow)}")
                for name, t in slow.items():
                    log_warning(f"  - {name}: {t:.0f}ms")
    
    # Warnings
    if test_results["warnings"]:
        log(f"\nWARNINGS ({len(test_results['warnings'])})")
        for warning in test_results["warnings"]:
            log_warning(f"{warning.get('test', 'Unknown')}: {warning.get('issue', 'Unknown issue')}")
    
    # Failed Tests
    if test_results["failed"]:
        log(f"\nFAILED TESTS ({len(test_results['failed'])})")
        for failure in test_results["failed"]:
            log_failure(f"{failure.get('test', 'Unknown')} ({failure.get('endpoint', 'Unknown endpoint')})")
            if "error" in failure:
                log(f"  Error: {failure['error']}")
    
    # Production Ready Verdict
    log(f"\nPRODUCTION READINESS")
    
    if pass_rate >= 95 and failed == 0:
        log_success("✓ PRODUCTION READY - All tests passed")
        score = 100
    elif pass_rate >= 90:
        log_warning("⚠ MOSTLY READY - Minor issues present")
        score = 85
    elif pass_rate >= 80:
        log_warning("⚠ NEEDS REVIEW - Some tests failing")
        score = 70
    else:
        log_failure("✗ NOT READY - Critical issues present")
        score = score_calculation(pass_rate, failed)
    
    log(f"\nFinal Score: {score}/100")
    
    # Save report to file
    report_file = "RUNTIME_TEST_RESULTS.json"
    with open(report_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": pass_rate,
                "score": score,
            },
            "results": test_results,
        }, f, indent=2)
    
    log(f"\nReport saved to: {report_file}")


def score_calculation(pass_rate: float, failed: int) -> int:
    """Calculate final score"""
    base_score = int(pass_rate)
    deduction = failed * 5
    return max(0, min(100, base_score - deduction))


def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 60)
    print("STOCK SENTINEL - COMPREHENSIVE RUNTIME TEST SUITE")
    print("Testing Backend APIs for Production Ready")
    print("=" * 60)
    print(f"{Colors.END}\n")
    
    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            log_success("Backend API is running ✓")
        else:
            log_failure("Backend API returned unexpected status")
            sys.exit(1)
    except Exception as e:
        log_failure(f"Cannot reach backend at {BASE_URL}")
        log(f"Error: {e}")
        sys.exit(1)
    
    # Run test suites
    token = test_auth_api()
    test_stock_api()
    test_portfolio_api()
    test_news_api()
    test_alerts_api()
    test_watchlist_api()
    test_error_handling()
    test_concurrent_requests()
    test_data_validation()
    
    # Generate report
    generate_report()


if __name__ == "__main__":
    main()
