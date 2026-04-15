#!/usr/bin/env python3
"""
Stock Sentinel - FRONTEND USER FLOW TEST
Simulates real user interactions and workflow
"""

import requests
import json
import time
from typing import Dict, List
import sys

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3001"
TIMEOUT = 15

results = {
    "frontend_tests": {},
    "workflow_tests": {},
    "ui_issues": [],
    "performance_issues": [],
    "summary": {"success": 0, "issues": 0}
}

class C:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def header(text):
    print(f"\n{C.CYAN}{C.BOLD}{text}{C.END}\n")

def ok(text):
    print(f"{C.GREEN}✓{C.END} {text}")
    results["summary"]["success"] += 1

def issue(text):
    print(f"{C.RED}✗{C.END} {text}")
    results["summary"]["issues"] += 1
    results["ui_issues"].append(text)

def warn(text):
    print(f"{C.YELLOW}⚠{C.END} {text}")
    results["performance_issues"].append(text)

# =======================================================================
# TEST 1: Frontend Server availability
# =======================================================================
header("1️⃣  FRONTEND SERVER AVAILABILITY")

try:
    r = requests.get(FRONTEND_URL, timeout=TIMEOUT)
    if r.status_code == 200:
        ok(f"Frontend server is responding ({r.status_code})")
    else:
        issue(f"Frontend returned {r.status_code} (should be 200)")
except requests.Timeout:
    issue("Frontend server timeout - page loading too slow (>15s)")
except Exception as e:
    issue(f"Frontend not accessible: {str(e)}")

# =======================================================================
# TEST 2: API Endpoints Required by Frontend 
# =======================================================================
header("2️⃣  FRONTEND REQUIRED API ENDPOINTS")

required_endpoints = [
    ("GET", "/api/health", "Health check"),
    ("GET", "/api/search?q=AAPL", "Stock search"),
    ("GET", "/api/news", "News feed"),
    ("GET", "/api/stocks/live/quotes", "Live market data"),
    ("GET", "/api/auth", "Auth endpoint"),  # May 404, but should not crash
]

slow_endpoints = []

for method, path, name in required_endpoints:
    try:
        start = time.time()
        if method == "GET":
            r = requests.get(f"{BASE_URL}{path}", timeout=TIMEOUT)
        elapsed = (time.time() - start) * 1000
        
        if r.status_code in [200, 401, 404]:  # 404 is OK for some endpoints
            ok(f"{name}: {r.status_code} - {elapsed:.0f}ms")
            if elapsed > 1000:
                warn(f"{name} is SLOW: {elapsed:.0f}ms (>1s)")
                slow_endpoints.append((name, elapsed))
        else:
            issue(f"{name}: {r.status_code}")
    except requests.Timeout:
        issue(f"{name}: TIMEOUT after {TIMEOUT}s")
    except Exception as e:
        issue(f"{name}: {str(e)[:50]}")

# =======================================================================
# TEST 3: USER WORKFLOW SIMULATION
# =======================================================================
header("3️⃣  USER WORKFLOW TEST")

print("Simulating: 1. Open app → 2. Search stock → 3. View details → 4. Check news")

# Step 1: Load dashboard (requires multiple endpoints)
print("\n[Step 1] Dashboard load...")
start = time.time()
dashboard_calls = 0

try:
    # These are the calls a dashboard would make
    r1 = requests.get(f"{BASE_URL}/api/health", timeout=5)
    r2 = requests.get(f"{BASE_URL}/api/stocks/live/quotes", timeout=5)
    r3 = requests.get(f"{BASE_URL}/api/news?limit=10", timeout=5)
    
    dashboard_calls = 3
    elapsed = (time.time() - start) * 1000
    
    if all(r.status_code in [200, 401] for r in [r1, r2, r3]):
        ok(f"Dashboard initialization: {dashboard_calls} API calls in {elapsed:.0f}ms")
        if elapsed > 3000:
            warn(f"Dashboard load is slow: {elapsed:.0f}ms (target <3s)")
    else:
        issue(f"Dashboard initialization: Some APIs returned errors")
        
except Exception as e:
    issue(f"Dashboard initialization failed: {str(e)}")

# Step 2: Search for stock
print("\n[Step 2] Stock search...")
try:
    start = time.time()
    r = requests.get(f"{BASE_URL}/api/search?q=APPLE", timeout=TIMEOUT)
    elapsed = (time.time() - start) * 1000
    
    if r.status_code == 200:
        data = r.json()
        ok(f"Search returned {len(data)} results in {elapsed:.0f}ms")
        if elapsed > 1000:
            warn(f"Search is slow: {elapsed:.0f}ms for single query")
    else:
        issue(f"Search failed: {r.status_code}")
except Exception as e:
    issue(f"Search failed: {str(e)}")

# Step 3: View stock details
print("\n[Step 3] Stock details request...")
try:
    start = time.time()
    r = requests.get(f"{BASE_URL}/api/stock/AAPL/quote", timeout=TIMEOUT)
    elapsed = (time.time() - start) * 1000
    
    if r.status_code == 200:
        data = r.json()
        ok(f"Stock details loaded in {elapsed:.0f}ms")
        if elapsed > 500:
            warn(f"Stock detail load is slow: {elapsed:.0f}ms (target <500ms)")
    else:
        issue(f"Stock details failed: {r.status_code}")
except Exception as e:
    issue(f"Stock details failed: {str(e)}")

# Step 4: View news
print("\n[Step 4] News feed...")
try:
    start = time.time()
    r = requests.get(f"{BASE_URL}/api/news?limit=5", timeout=TIMEOUT)
    elapsed = (time.time() - start) * 1000
    
    if r.status_code == 200:
        data = r.json()
        ok(f"News loaded ({len(data)} articles) in {elapsed:.0f}ms")
        if elapsed > 1000:
            warn(f"News load is slow: {elapsed:.0f}ms (target <1s)")
    else:
        issue(f"News load failed: {r.status_code}")
except Exception as e:
    issue(f"News load failed: {str(e)}")

# =======================================================================
# TEST 4: Error Handling & Recovery
# =======================================================================
header("4️⃣  ERROR HANDLING TEST")

# Test with invalid input
print("[Test] Invalid stock symbol...")
try:
    r = requests.get(f"{BASE_URL}/api/stock/!!!INVALID!!!/quote", timeout=TIMEOUT)
    if r.status_code in [400, 404, 422]:
        ok(f"Invalid symbol handled properly ({r.status_code})")
    else:
        issue(f"Invalid symbol unexpected response: {r.status_code}")
except Exception as e:
    issue(f"Invalid symbol crashed API: {str(e)}")

# Test with missing parameters
print("[Test] Empty search query...")
try:
    r = requests.get(f"{BASE_URL}/api/search?q=", timeout=TIMEOUT)
    if r.status_code in [400, 422, 200]:
        ok(f"Empty query handled properly ({r.status_code})")
    else:
        issue(f"Empty query unexpected response: {r.status_code}")
except Exception as e:
    issue(f"Empty query crashed API: {str(e)}")

# Test backend timeout/gateway errors
print("[Test] Backend timeout simulation...")
try:
    # Make request to slow endpoint
    start = time.time()
    r = requests.get(f"{BASE_URL}/api/stocks/live", timeout=15)
    elapsed = (time.time() - start) * 1000
    
    if r.status_code == 200:
        ok(f"Slow endpoint still responding ({elapsed:.0f}ms)")
        if elapsed > 5000:
            issue(f"Slow endpoint takes too long ({elapsed:.0f}ms) - may timeout in browser")
    else:
        warn(f"Slow endpoint error: {r.status_code}")
except requests.Timeout:
    issue(f"Slow endpoint timeout - would timeout in browser (>15s)")
except Exception as e:
    issue(f"Slow endpoint error: {str(e)}")

# =======================================================================
# TEST 5: RESPONSE DATA QUALITY
# =======================================================================
header("5️⃣  RESPONSE DATA QUALITY")

# Check health endpoint
try:
    r = requests.get(f"{BASE_URL}/api/health", timeout=TIMEOUT)
    if r.status_code == 200:
        data = r.json()
        if "status" in data and "service" in data:
            ok("Health endpoint returns complete data")
        else:
            issue("Health endpoint missing required fields")
except Exception as e:
    issue(f"Health check failed: {str(e)}")

# Check news endpoint
try:
    r = requests.get(f"{BASE_URL}/api/news?limit=1", timeout=TIMEOUT)
    if r.status_code == 200:
        data = r.json()
        if isinstance(data, list) and len(data) > 0:
            article = data[0]
            required_fields = ["title", "source"]  # Basic fields
            missing = [f for f in required_fields if f not in article]
            if missing:
                issue(f"News articles missing fields: {missing}")
            else:
                ok(f"News endpoint returns complete articles")
        else:
            issue("News endpoint returns empty list")
except Exception as e:
    issue(f"News check failed: {str(e)}")

# Check stock quote endpoint
try:
    r = requests.get(f"{BASE_URL}/api/stock/AAPL/quote", timeout=TIMEOUT)
    if r.status_code == 200:
        data = r.json()
        required_fields = ["ticker", "price", "change"]
        missing = [f for f in required_fields if f not in data]
        if missing:
            issue(f"Stock quote missing fields: {missing}")
        else:
            ok("Stock endpoint returns complete quote data")
    else:
        issue(f"Stock quote error: {r.status_code}")
except Exception as e:
    issue(f"Stock quote check failed: {str(e)}")

# =======================================================================
# TEST 6: API CONSISTENCY
# =======================================================================
header("6️⃣  API CONSISTENCY & STANDARDS")

# Check CORS headers
try:
    r = requests.get(f"{BASE_URL}/api/health", timeout=TIMEOUT)
    if "access-control-allow-origin" in r.headers or "Access-Control-Allow-Origin" in r.headers:
        ok("CORS headers present")
    else:
        warn("CORS headers may be missing (could cause frontend issues)")
except Exception as e:
    warn(f"Could not verify CORS: {str(e)}")

# Check response content-type
try:
    r = requests.get(f"{BASE_URL}/api/health", timeout=TIMEOUT)
    if "application/json" in r.headers.get("content-type", ""):
        ok("API returns JSON content-type")
    else:
        issue(f"API content-type: {r.headers.get('content-type', 'not set')}")
except Exception as e:
    warn(f"Could not verify content-type: {str(e)}")

# =======================================================================
# FINAL REPORT
# =======================================================================
header("📊 FRONTEND TEST REPORT")

print(f"Tests Passed:     {results['summary']['success']}")
print(f"Issues Found:     {results['summary']['issues']}")
print(f"Slow Endpoints:   {len(slow_endpoints)}\n")

if slow_endpoints:
    print("Slow Endpoints Detail:")
    for name, ms in slow_endpoints:
        print(f"  • {name}: {ms:.0f}ms (ideally <1000ms)")

if results["ui_issues"]:
    print(f"\n{C.RED}Critical UI Issues:{C.END}")
    for issue_text in results["ui_issues"]:
        print(f"  {C.RED}✗{C.END} {issue_text}")

if results["performance_issues"]:
    print(f"\n{C.YELLOW}Performance Warnings:{C.END}")
    for perf in results["performance_issues"][:5]:  # Show first 5
        print(f"  {C.YELLOW}⚠{C.END} {perf}")

# Calculate score
total_issues = results["summary"]["issues"]
total_perf = len(results["performance_issues"])
score = 100 - (total_issues * 10) - (total_perf * 2)
score = max(0, min(100, score))

print(f"\n{C.BOLD}FRONTEND TEST SCORE: {score:.0f}/100{C.END}")

if score >= 85:
    print(f"{C.GREEN}✓ FRONTEND UI FUNCTIONAL{C.END}")
elif score >= 70:
    print(f"{C.YELLOW}⚠ FRONTEND HAS ISSUES{C.END}")
else:
    print(f"{C.RED}✗ FRONTEND BROKEN{C.END}")

# Save results
with open("FRONTEND_TEST_RESULTS.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved to FRONTEND_TEST_RESULTS.json\n")
