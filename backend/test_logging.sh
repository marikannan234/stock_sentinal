#!/usr/bin/env bash
# End-to-End Logging Testing Script
# This script tests the complete logging system with real requests

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_header() {
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
}

# Check if server is running
check_server() {
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health)
    if [ "$response" != "200" ] && [ "$response" != "000" ]; then
        return 1
    fi
    return 0
}

# Wait for server to start
wait_for_server() {
    log_info "Waiting for server to start..."
    for i in {1..30}; do
        if check_server; then
            log_success "Server is running"
            return 0
        fi
        sleep 1
    done
    log_error "Server failed to start after 30 seconds"
    return 1
}

# Test successful request
test_success_case() {
    log_header "Test 1: Successful Request"
    
    log_info "Making request to /api/health"
    response=$(curl -s http://localhost:8000/api/health)
    
    if echo "$response" | grep -q "status"; then
        log_success "Request succeeded"
        echo "Response: $response"
        return 0
    else
        log_error "Unexpected response"
        echo "Response: $response"
        return 1
    fi
}

# Test validation error
test_validation_error() {
    log_header "Test 2: Validation Error"
    
    log_info "Testing invalid ticker: /api/stock//quote (empty ticker)"
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" http://localhost:8000/api/stock//quote 2>/dev/null || echo "HTTP_CODE:000")
    
    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d':' -f2)
    body=$(echo "$response" | grep -v "HTTP_CODE:")
    
    log_info "HTTP Code: $http_code"
    
    if echo "$body" | grep -q "error"; then
        log_success "Error response received"
        echo "Response: $body" | head -c 200
        echo ""
        return 0
    else
        log_error "No error response"
        echo "Response: $body"
        return 1
    fi
}

# Test 404 error
test_not_found_error() {
    log_header "Test 3: Not Found Error"
    
    log_info "Testing non-existent endpoint: /api/nonexistent"
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" http://localhost:8000/api/nonexistent 2>/dev/null)
    
    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d':' -f2)
    body=$(echo "$response" | grep -v "HTTP_CODE:")
    
    log_info "HTTP Code: $http_code"
    
    if [ "$http_code" = "404" ]; then
        log_success "404 returned as expected"
        echo "Response: $body" | head -c 200
        echo ""
        return 0
    else
        log_warning "Expected 404, got $http_code"
        return 1
    fi
}

# Check log files exist
check_log_files() {
    log_header "Test 4: Log Files Created"
    
    if [ -f "logs/app.log" ]; then
        log_success "app.log exists"
        size=$(wc -c < logs/app.log)
        log_info "Size: $size bytes"
    else
        log_error "app.log not found"
        return 1
    fi
    
    if [ -f "logs/errors.log" ]; then
        log_success "errors.log exists"
        size=$(wc -c < logs/errors.log)
        log_info "Size: $size bytes"
    else
        log_warning "errors.log not created yet (will be created on first error)"
    fi
    
    if [ -f "logs/access.log" ]; then
        log_success "access.log exists"
        size=$(wc -c < logs/access.log)
        log_info "Size: $size bytes"
    else
        log_warning "access.log not created yet"
    fi
    
    return 0
}

# Check log content
check_log_content() {
    log_header "Test 5: Log Content"
    
    if [ ! -f "logs/app.log" ]; then
        log_error "app.log not found"
        return 1
    fi
    
    log_info "Recent app.log entries (last 5):"
    echo ""
    tail -5 logs/app.log | while IFS= read -r line; do
        echo "  $line"
    done
    echo ""
    
    if grep -q "GET /api/health" logs/app.log || grep -q "health" logs/app.log; then
        log_success "Health check logged"
    else
        log_warning "Health check not found in logs (logs may be empty)"
    fi
    
    return 0
}

# Verify exception handling
test_exception_handling() {
    log_header "Test 6: Exception Handling"
    
    log_info "Running Python import test..."
    
    cat > /tmp/test_exceptions.py << 'EOF'
import sys
sys.path.insert(0, '.')

try:
    from app.core.exceptions import StockNotFoundError, ValidationError, AuthenticationError, ExternalAPIError
    from app.core.logging_config import get_logger
    
    # Test exception creation
    exc = StockNotFoundError("TEST")
    exc_dict = exc.to_dict()
    
    if "error" in exc_dict and "code" in exc_dict["error"]:
        print("SUCCESS: Exception serialization works")
        sys.exit(0)
    else:
        print("FAIL: Exception serialization failed")
        sys.exit(1)
except Exception as e:
    print(f"FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF
    
    if python /tmp/test_exceptions.py 2>&1 | grep -q "SUCCESS"; then
        log_success "Exception handling works"
        python /tmp/test_exceptions.py
        return 0
    else
        log_error "Exception handling test failed"
        python /tmp/test_exceptions.py
        return 1
    fi
}

# Check middleware
test_middleware() {
    log_header "Test 7: Middleware & Timing"
    
    log_info "Making request to log timing..."
    
    start=$(date +%s%N)
    curl -s http://localhost:8000/api/health > /dev/null 2>&1
    end=$(date +%s%N)
    
    duration_ms=$((($end - $start) / 1000000))
    
    log_success "Request completed in ${duration_ms}ms"
    
    # Check if timing is logged
    if grep -q "ms" logs/access.log 2>/dev/null; then
        log_success "Request timing logged in access.log"
        tail -1 logs/access.log
    fi
    
    return 0
}

# Generate test report
generate_report() {
    log_header "Test Summary Report"
    
    results_file="/tmp/test_results.txt"
    
    cat > "$results_file" << 'EOF'
================================================================================
LOGGING SYSTEM TEST REPORT
================================================================================
EOF
    
    echo "" >> "$results_file"
    echo "Generated: $(date)" >> "$results_file"
    echo "Hostname: $(hostname)" >> "$results_file"
    echo "" >> "$results_file"
    
    if [ -f "logs/app.log" ]; then
        echo "LOG FILES:" >> "$results_file"
        ls -lh logs/ >> "$results_file"
        echo "" >> "$results_file"
    fi
    
    if [ -f "logs/app.log" ]; then
        echo "APP.LOG CONTENT (Last 20 lines):" >> "$results_file"
        tail -20 logs/app.log >> "$results_file"
        echo "" >> "$results_file"
    fi
    
    echo "=================================================================================" >> "$results_file"
    
    log_success "Report saved to $results_file"
    cat "$results_file"
}

# Main test execution
main() {
    log_header "Stock Sentinel - Logging System E2E Tests"
    
    log_info "Starting end-to-end logging tests..."
    echo ""
    
    # Check if server is running
    if ! check_server; then
        log_warning "Server not running. Please start with:"
        echo "  cd backend"
        echo "  uvicorn app.main:app --reload"
        echo ""
        log_info "Alternatively, run this script in another terminal after starting server"
        exit 1
    fi
    
    # Run tests
    test_counter=0
    pass_counter=0
    
    tests=(
        "test_success_case"
        "test_validation_error"
        "test_not_found_error"
        "check_log_files"
        "check_log_content"
        "test_exception_handling"
        "test_middleware"
    )
    
    for test in "${tests[@]}"; do
        ((test_counter++))
        if $test; then
            ((pass_counter++))
        else
            log_warning "Test failed but continuing..."
        fi
        sleep 1
    done
    
    echo ""
    log_header "Results"
    log_success "Passed: $pass_counter/$test_counter tests"
    
    if [ $pass_counter -eq $test_counter ]; then
        log_success "All tests passed! ✨"
        exit 0
    else
        log_warning "Some tests failed - check output above"
        exit 1
    fi
}

# Run main
main
