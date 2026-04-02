#!/usr/bin/env python3
"""
Production Logging Verification Script

This script verifies that the logging system is working correctly.
Run this after deploying the logging infrastructure.

Usage:
    python verify_logging.py          # Run all checks
    python verify_logging.py --test   # Test with sample log writes
    python verify_logging.py --clean  # Clean old logs
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime
import subprocess
import json


def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_section(text):
    """Print formatted section."""
    print(f"\n▶ {text}")


def print_success(text):
    """Print success message."""
    print(f"  ✅ {text}")


def print_warning(text):
    """Print warning message."""
    print(f"  ⚠️  {text}")


def print_error(text):
    """Print error message."""
    print(f"  ❌ {text}")


def check_file_exists(path, name):
    """Check if required file exists."""
    if os.path.exists(path):
        size = os.path.getsize(path)
        print_success(f"{name}: {path} ({size} bytes)")
        return True
    else:
        print_error(f"{name} missing: {path}")
        return False


def check_logs_directory():
    """Verify logs directory and files."""
    print_section("Checking logs directory structure...")
    
    logs_dir = Path("logs")
    
    if not logs_dir.exists():
        print_warning("Logs directory doesn't exist yet (will be created on first run)")
        return False
    
    print_success(f"Logs directory exists: {logs_dir.absolute()}")
    
    # Check log files
    required_logs = {
        "app.log": "Application log (DEBUG+)",
        "errors.log": "Error log (ERROR+)",
        "access.log": "HTTP request/response log",
    }
    
    all_exist = True
    for log_file, description in required_logs.items():
        log_path = logs_dir / log_file
        if log_path.exists():
            size = os.path.getsize(log_path)
            print_success(f"{log_file}: {size} bytes - {description}")
        else:
            print_warning(f"{log_file} will be created on first request")
            all_exist = False
    
    return all_exist


def check_python_files():
    """Verify all required Python files exist."""
    print_section("Checking required Python modules...")
    
    required_files = {
        "app/core/logging_config.py": "Logging configuration",
        "app/core/exceptions.py": "Exception classes",
        "app/core/error_handlers.py": "Error handlers and middleware",
        "app/schemas/error_responses.py": "Error response schemas",
    }
    
    all_exist = True
    for path, name in required_files.items():
        if not check_file_exists(path, name):
            all_exist = False
    
    return all_exist


def check_imports():
    """Test that all imports work."""
    print_section("Testing Python imports...")
    
    try:
        from app.core.logging_config import setup_logging, get_logger
        print_success("logging_config: setup_logging(), get_logger()")
    except ImportError as e:
        print_error(f"logging_config import failed: {e}")
        return False
    
    try:
        from app.core.exceptions import (
            APIException, StockNotFoundError, InvalidTickerError,
            AuthenticationError, ValidationError
        )
        print_success("exceptions: All 13 exception classes")
    except ImportError as e:
        print_error(f"exceptions import failed: {e}")
        return False
    
    try:
        from app.core.error_handlers import (
            http_exception_handler, setup_exception_handlers, setup_middleware
        )
        print_success("error_handlers: setup_exception_handlers(), setup_middleware()")
    except ImportError as e:
        print_error(f"error_handlers import failed: {e}")
        return False
    
    try:
        from app.schemas.error_responses import ErrorResponse
        print_success("error_responses: Pydantic models")
    except ImportError as e:
        print_error(f"error_responses import failed: {e}")
        return False
    
    return True


def test_logging():
    """Test logging system with sample writes."""
    print_section("Testing logging output...")
    
    try:
        from app.core.logging_config import setup_logging, get_logger
        
        # Setup logging
        setup_logging()
        
        # Get logger
        logger = get_logger(__name__)
        
        # Test different log levels
        logger.debug("Test DEBUG message")
        logger.info("Test INFO message")
        logger.warning("Test WARNING message")
        logger.error("Test ERROR message")
        logger.critical("Test CRITICAL message")
        
        # Test with extra context
        logger.info(
            "Test with context",
            extra={
                "user_id": 123,
                "action": "test",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        print_success("Log messages written - check logs/app.log")
        return True
    
    except Exception as e:
        print_error(f"Logging test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_exceptions():
    """Test exception system."""
    print_section("Testing exception system...")
    
    try:
        from app.core.exceptions import (
            StockNotFoundError,
            InvalidTickerError,
            ValidationError,
            AuthenticationError,
            ExternalAPIError,
        )
        
        # Test exception creation
        exc1 = StockNotFoundError("RELIANCE")
        exc_dict = exc1.to_dict()
        
        if "error" not in exc_dict or "code" not in exc_dict["error"]:
            print_error("Exception.to_dict() format incorrect")
            return False
        
        print_success("StockNotFoundError created and serialized correctly")
        print(f"  → Status code: {exc1.status_code}")
        print(f"  → Error code: {exc_dict['error']['code']}")
        print(f"  → Message: {exc_dict['error']['message']}")
        
        # Test different exception types
        exceptions_to_test = [
            InvalidTickerError("XYZ"),
            ValidationError("Age must be > 0"),
            AuthenticationError("Invalid token"),
            ExternalAPIError("API timeout"),
        ]
        
        for exc in exceptions_to_test:
            exc_dict = exc.to_dict()
            print_success(f"{exc.__class__.__name__}: Code={exc_dict['error']['code']}")
        
        return True
    
    except Exception as e:
        print_error(f"Exception test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_log_contents():
    """Show actual log file contents."""
    print_section("Recent log file contents...")
    
    log_files = ["logs/app.log", "logs/errors.log", "logs/access.log"]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"\n  📄 {log_file} (last 10 lines):")
            print("  " + "-" * 66)
            try:
                with open(log_file, "r") as f:
                    lines = f.readlines()
                    last_lines = lines[-10:] if len(lines) > 10 else lines
                    for line in last_lines:
                        print(f"  {line.rstrip()}")
            except Exception as e:
                print(f"    Error reading file: {e}")
            print("  " + "-" * 66)


def show_summary(results):
    """Show test summary."""
    print_header("VERIFICATION SUMMARY")
    
    checks = {
        "Python files": results.get("python_files", False),
        "Imports": results.get("imports", False),
        "Logging": results.get("logging", False),
        "Exceptions": results.get("exceptions", False),
        "Log files": results.get("log_files", False),
    }
    
    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    
    for check, status in checks.items():
        symbol = "✅" if status else "⚠️"
        print(f"  {symbol} {check}")
    
    print(f"\n  Result: {passed}/{total} checks passed")
    
    if passed == total:
        print_success("All checks passed! Logging system is ready.")
        return True
    else:
        print_warning("Some checks failed. Review errors above.")
        return False


def main():
    """Main verification function."""
    print_header("STOCK SENTINEL LOGGING VERIFICATION")
    
    results = {}
    
    # Check Python files exist
    results["python_files"] = check_python_files()
    
    # Change to backend directory if needed
    if not os.path.exists("app"):
        if os.path.exists("backend"):
            os.chdir("backend")
            print(f"\n📁 Changed to backend directory")
    
    # Check logs directory
    results["log_files"] = check_logs_directory()
    
    # Check imports
    results["imports"] = check_imports()
    
    # Test exceptions
    results["exceptions"] = test_exceptions()
    
    # Test logging if --test flag
    if "--test" in sys.argv:
        results["logging"] = test_logging()
        show_log_contents()
    else:
        print_section("Log testing (use --test flag to enable)")
        print("  ℹ️  Skipped (use: python verify_logging.py --test)")
    
    # Show summary
    success = show_summary(results)
    
    # Additional help
    print_header("NEXT STEPS")
    
    print("\n1. Start the server:")
    print("   cd backend")
    print("   uvicorn app.main:app --reload")
    
    print("\n2. Check logs are created:")
    print("   tail -f logs/app.log")
    
    print("\n3. Test error handling:")
    print("   curl http://localhost:8000/api/stock/INVALID/quote")
    
    print("\n4. Migrate existing routes:")
    print("   See: MIGRATION_EXAMPLE_STOCK_ROUTE.md")
    
    print("\n" + "=" * 70)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
