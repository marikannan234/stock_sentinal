# Windows PowerShell - Production Logging Test Script
# Run this after starting your server to verify logging is working

# Make sure we're in the backend directory
if (-not (Test-Path "app/core/logging_config.py")) {
    if (Test-Path "backend") {
        Set-Location backend
    } else {
        Write-Host "❌ Please run from backend directory" -ForegroundColor Red
        exit 1
    }
}

# Colors
$Colors = @{
    Success = 'Green'
    Error = 'Red'
    Warning = 'Yellow'
    Info = 'Blue'
    Header = 'Cyan'
}

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor $Colors.Header
    Write-Host "  $Text" -ForegroundColor $Colors.Header
    Write-Host ("=" * 70) -ForegroundColor $Colors.Header
}

function Write-Section {
    param([string]$Text)
    Write-Host ""
    Write-Host "▶ $Text" -ForegroundColor $Colors.Info
}

function Write-Success {
    param([string]$Text)
    Write-Host "  ✅ $Text" -ForegroundColor $Colors.Success
}

function Write-Error-Custom {
    param([string]$Text)
    Write-Host "  ❌ $Text" -ForegroundColor $Colors.Error
}

function Write-Warning-Custom {
    param([string]$Text)
    Write-Host "  ⚠️  $Text" -ForegroundColor $Colors.Warning
}

# Test 1: Check files exist
function Test-FilesExist {
    Write-Header "Test 1: Check Required Files"
    
    $files = @(
        "app/core/logging_config.py",
        "app/core/exceptions.py",
        "app/core/error_handlers.py",
        "app/schemas/error_responses.py"
    )
    
    $allExist = $true
    foreach ($file in $files) {
        if (Test-Path $file) {
            $size = (Get-Item $file).Length
            Write-Success "$file ($size bytes)"
        } else {
            Write-Error-Custom "$file NOT FOUND"
            $allExist = $false
        }
    }
    
    return $allExist
}

# Test 2: Check imports work
function Test-Imports {
    Write-Header "Test 2: Test Python Imports"
    
    $testScript = @'
import sys
sys.path.insert(0, '.')

try:
    from app.core.logging_config import setup_logging, get_logger
    from app.core.exceptions import StockNotFoundError, ValidationError
    from app.core.error_handlers import http_exception_handler, setup_exception_handlers
    from app.schemas.error_responses import ErrorResponse
    print("SUCCESS: All imports work")
except Exception as e:
    print(f"FAIL: {e}")
    sys.exit(1)
'@
    
    $result = python -c $testScript 2>&1
    if ($result -like "*SUCCESS*") {
        Write-Success "Python imports: OK"
        return $true
    } else {
        Write-Error-Custom "Python import failed: $result"
        return $false
    }
}

# Test 3: Check server status
function Test-ServerRunning {
    Write-Header "Test 3: Check Server Status"
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -ErrorAction SilentlyContinue
        Write-Success "Server is running (Health: $($response.StatusCode))"
        return $true
    } catch {
        Write-Warning-Custom "Server not responding at http://localhost:8000"
        Write-Host "  Start server with: uvicorn app.main:app --reload" -ForegroundColor Yellow
        return $false
    }
}

# Test 4: Check logs directory
function Test-LogsDirectory {
    Write-Header "Test 4: Check Logs Directory"
    
    if (Test-Path "logs") {
        Write-Success "Logs directory exists"
        
        $logFiles = Get-ChildItem logs/*.log -ErrorAction SilentlyContinue
        if ($logFiles) {
            foreach ($file in $logFiles) {
                $size = $file.Length
                Write-Success "$($file.Name) ($size bytes)"
            }
        } else {
            Write-Warning-Custom "No log files yet (created on first request)"
        }
        return $true
    } else {
        Write-Warning-Custom "Logs directory will be created on first request"
        return $false
    }
}

# Test 5: Check exceptions work
function Test-Exceptions {
    Write-Header "Test 5: Test Exception System"
    
    $testScript = @'
import sys
sys.path.insert(0, '.')

try:
    from app.core.exceptions import StockNotFoundError, InvalidTickerError, ValidationError
    
    # Test exception creation
    exc = StockNotFoundError("RELIANCE")
    exc_dict = exc.to_dict()
    
    if "error" in exc_dict and "code" in exc_dict["error"]:
        print(f"✅ StockNotFoundError: Code={exc_dict['error']['code']}")
    else:
        print("❌ Exception format incorrect")
        sys.exit(1)
    
    # Test different exception types
    exc2 = InvalidTickerError("INVALID")
    exc_dict2 = exc2.to_dict()
    print(f"✅ InvalidTickerError: Code={exc_dict2['error']['code']}")
    
    exc3 = ValidationError("Test error")
    exc_dict3 = exc3.to_dict()
    print(f"✅ ValidationError: Code={exc_dict3['error']['code']}")
    
    print("SUCCESS: All exceptions work")
except Exception as e:
    print(f"FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
'@
    
    $result = python -c $testScript 2>&1
    Write-Host $result
    return $result -like "*SUCCESS*"
}

# Test 6: Test logging
function Test-Logging {
    Write-Header "Test 6: Test Logging System"
    
    $testScript = @'
import sys
sys.path.insert(0, '.')

try:
    from app.core.logging_config import setup_logging, get_logger
    from datetime import datetime
    
    setup_logging()
    logger = get_logger(__name__)
    
    logger.debug("Test DEBUG message")
    logger.info("Test INFO message")
    logger.warning("Test WARNING message")
    logger.error("Test ERROR message")
    
    logger.info(
        "Test with context",
        extra={
            "user_id": 123,
            "action": "test",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    print("SUCCESS: Logging works")
except Exception as e:
    print(f"FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
'@
    
    $result = python -c $testScript 2>&1
    if ($result -like "*SUCCESS*") {
        Write-Success "Log messages written successfully"
        
        # Show recent logs
        if (Test-Path "logs/app.log") {
            Write-Section "Recent app.log entries:"
            $lines = Get-Content logs/app.log -Tail 5
            foreach ($line in $lines) {
                Write-Host "  $line" -ForegroundColor Gray
            }
        }
        return $true
    } else {
        Write-Error-Custom "Logging test failed"
        Write-Host $result
        return $false
    }
}

# Test 7: Make HTTP request
function Test-HttpRequest {
    Write-Header "Test 7: Make HTTP Request"
    
    try {
        Write-Section "Making request to /api/health"
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -ErrorAction SilentlyContinue
        $body = $response.Content | ConvertFrom-Json
        
        Write-Success "HTTP 200 - Response: $($body | ConvertTo-Json -Depth 1)"
        
        # Check if logged
        Write-Section "Checking if request was logged..."
        if (Test-Path "logs/app.log") {
            $appLog = Get-Content logs/app.log -Tail 20
            if ($appLog -match "health") {
                Write-Success "Request logged in app.log"
            } else {
                Write-Warning-Custom "Request not found in recent logs"
            }
        }
        
        return $true
    } catch {
        Write-Error-Custom "HTTP request failed: $($_.Exception.Message)"
        return $false
    }
}

# Test 8: Show summary
function Test-Summary {
    Write-Header "Verification Summary"
    
    $tests = @(
        @{ Name = "Python files"; Result = $global:test1 },
        @{ Name = "Python imports"; Result = $global:test2 },
        @{ Name = "Server running"; Result = $global:test3 },
        @{ Name = "Logs directory"; Result = $global:test4 },
        @{ Name = "Exception system"; Result = $global:test5 },
        @{ Name = "Logging system"; Result = $global:test6 },
        @{ Name = "HTTP requests"; Result = $global:test7 }
    )
    
    $passed = 0
    $total = $tests.Count
    
    foreach ($test in $tests) {
        $symbol = if ($test.Result) { "✅" } else { "⚠️" }
        Write-Host "  $symbol $($test.Name)" -ForegroundColor $(if ($test.Result) { $Colors.Success } else { $Colors.Warning })
        if ($test.Result) { $passed++ }
    }
    
    Write-Host ""
    Write-Host "Result: $passed/$total checks passed" -ForegroundColor $(if ($passed -eq $total) { $Colors.Success } else { $Colors.Warning })
    
    if ($passed -eq $total) {
        Write-Success "All checks passed! Logging system is ready."
        return $true
    } else {
        Write-Warning-Custom "Some checks failed - review output above"
        return $false
    }
}

# Main execution
Write-Header "Stock Sentinel - Logging System Verification"

Write-Host ""
Write-Host "Running verification tests..." -ForegroundColor Cyan
Write-Host ""

# Run tests
$global:test1 = Test-FilesExist
$global:test2 = Test-Imports
$global:test3 = Test-ServerRunning
$global:test4 = Test-LogsDirectory
$global:test5 = Test-Exceptions
$global:test6 = Test-Logging
$global:test7 = if ($global:test3) { Test-HttpRequest } else { $false }

# Show summary
$success = Test-Summary

# Show next steps
Write-Header "Next Steps"

Write-Host ""
Write-Host "1. If all tests passed:" -ForegroundColor Cyan
Write-Host "   ✅ Your logging system is ready to use!"
Write-Host "   ✅ Start updating your routes (see QUICK_REFERENCE.md)"
Write-Host ""

Write-Host "2. If server is not running:" -ForegroundColor Cyan
Write-Host "   cd backend" -ForegroundColor Yellow
Write-Host "   uvicorn app.main:app --reload" -ForegroundColor Yellow
Write-Host "   Then run this script again in another terminal"
Write-Host ""

Write-Host "3. What to do next:" -ForegroundColor Cyan
Write-Host "   • Read QUICK_REFERENCE.md (5 min)"
Write-Host "   • Read MIGRATION_EXAMPLE_STOCK_ROUTE.md (10 min)"
Write-Host "   • Update your first route: app/api/routes/auth.py (10 min)"
Write-Host "   • Test: curl http://localhost:8000/api/auth/login"
Write-Host "   • Check: tail -f logs/app.log"
Write-Host ""

Write-Host "4. Documentation:" -ForegroundColor Cyan
Write-Host "   • QUICK_REFERENCE.md - One-page cheat sheet"
Write-Host "   • LOGGING_IMPLEMENTATION_CHECKLIST.md - Step-by-step guide"
Write-Host "   • LOGGING_ERROR_HANDLING_GUIDE.md - Complete documentation"
Write-Host "   • MIGRATION_EXAMPLE_STOCK_ROUTE.md - Real before/after example"
Write-Host ""

if (-not $success) {
    Write-Host "For help, check the troubleshooting section in QUICK_REFERENCE.md" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "You're all set! 🎉" -ForegroundColor Green
    exit 0
}
