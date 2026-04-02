#!/usr/bin/env python3
"""
PostgreSQL Connection Diagnostic Script

Checks:
1. If PostgreSQL is running
2. If user 'stocksentinel' exists
3. If database 'stocksentinel' exists
4. Current database users and their privileges
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return output"""
    print(f"\n{'='*80}")
    print(f"CHECK: {description}")
    print(f"{'='*80}")
    print(f"Command: {cmd}\n")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(result.stdout)
            return True
        else:
            print(f"❌ ERROR: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Command timed out")
        return False
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║           PostgreSQL Connection Diagnostic Tool                            ║
║                                                                            ║
║  This script checks if PostgreSQL is properly configured for Stock        ║
║  Sentinel. Run with admin PostgreSQL access.                             ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Check 1: PostgreSQL is running
    run_command(
        "psql --version",
        "PostgreSQL is installed and accessible"
    )
    
    # Check 2: Can connect to default postgres database
    run_command(
        'psql -U postgres -h localhost -d postgres -c "SELECT 1"',
        "Can connect to PostgreSQL as 'postgres' user"
    )
    
    # Check 3: List all users
    run_command(
        'psql -U postgres -h localhost -d postgres -c "\\du"',
        "List all PostgreSQL users"
    )
    
    # Check 4: Check if stocksentinel user exists
    run_command(
        'psql -U postgres -h localhost -d postgres -c "SELECT 1 FROM pg_user WHERE usename = \'stocksentinel\';"',
        "Check if 'stocksentinel' user exists"
    )
    
    # Check 5: List all databases
    run_command(
        'psql -U postgres -h localhost -d postgres -c "\\l"',
        "List all databases"
    )
    
    # Check 6: Check if stocksentinel database exists
    run_command(
        'psql -U postgres -h localhost -d postgres -c "SELECT 1 FROM pg_database WHERE datname = \'stocksentinel\';"',
        "Check if 'stocksentinel' database exists"
    )
    
    print(f"\n{'='*80}")
    print("DIAGNOSTIC COMPLETE")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
