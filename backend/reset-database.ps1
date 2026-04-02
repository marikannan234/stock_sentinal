# Database Reset and Migration Script for Stock Sentinel
# ===========================================================================
# This script safely resets the database and applies all migrations fresh.
# 
# IMPORTANT: This is for DEVELOPMENT ONLY!
# For production, run: alembic upgrade head
#
# Usage: .\reset-database.ps1
# ===========================================================================

param(
    [string]$Environment = "development",
    [switch]$SkipConfirmation = $false,
    [switch]$Verbose = $false
)

# Colors for console output
$colors = @{
    Green = [System.ConsoleColor]::Green
    Red = [System.ConsoleColor]::Red
    Yellow = [System.ConsoleColor]::Yellow
    Cyan = [System.ConsoleColor]::Cyan
    Gray = [System.ConsoleColor]::Gray
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor $colors.Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor $colors.Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor $colors.Cyan
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor $colors.Yellow
}

function Write-Verbose-Custom {
    param([string]$Message)
    if ($Verbose) {
        Write-Host "📝 $Message" -ForegroundColor $colors.Gray
    }
}

# ===========================================================================
# MAIN SCRIPT
# ===========================================================================

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor $colors.Cyan
Write-Host "║  Stock Sentinel Database Reset & Migration Tool               ║" -ForegroundColor $colors.Cyan
Write-Host "║  Environment: $Environment" -ForegroundColor $colors.Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor $colors.Cyan
Write-Host ""

# Verify we're in the right directory
if (-not (Test-Path "alembic.ini")) {
    Write-Error-Custom "alembic.ini not found. Please run this script from the backend directory."
    exit 1
}

Write-Verbose-Custom "Current directory: $(Get-Location)"

# ===========================================================================
# CONFIRMATION
# ===========================================================================

if (-not $SkipConfirmation) {
    Write-Warning-Custom "This will reset your database to initial state and apply all migrations."
    Write-Warning-Custom "All data will be LOST."
    Write-Host ""
    
    if ($Environment -eq "development") {
        Write-Info "Environment: DEVELOPMENT (safe to delete data)"
    } else {
        Write-Error-Custom "⚠️  PRODUCTION RESET DETECTED!"
        Write-Error-Custom "This script should NEVER be run in production!"
        Write-Host ""
        $response = Read-Host "Continue anyway? (yes/no)"
        if ($response -ne "yes") {
            Write-Info "Cancelled."
            exit 0
        }
    }
    
    Write-Host ""
    $response = Read-Host "Continue with database reset? (yes/no)"
    if ($response -ne "yes") {
        Write-Info "Cancelled."
        exit 0
    }
}

Write-Host ""

# ===========================================================================
# STEP 1: Activate Virtual Environment
# ===========================================================================

Write-Info "Step 1/5: Activating virtual environment..."

if (Test-Path ".venv\Scripts\Activate.ps1") {
    & ".venv\Scripts\Activate.ps1"
    Write-Success "Virtual environment activated"
} else {
    Write-Error-Custom ".venv not found. Please create virtual environment first."
    Write-Info "Create it with: python -m venv .venv"
    exit 1
}

Write-Host ""

# ===========================================================================
# STEP 2: Verify Database Connection
# ===========================================================================

Write-Info "Step 2/5: Verifying database connection..."

# Run Python to test connection
$dbTest = python -c "
from app.db.session import engine
try:
    with engine.connect() as conn:
        print('CONNECTION_OK')
except Exception as e:
    print(f'CONNECTION_ERROR: {str(e)}')
" 2>&1

if ($dbTest -match "CONNECTION_OK") {
    Write-Success "Database connection verified"
} else {
    Write-Error-Custom "Failed to connect to database"
    Write-Error-Custom $dbTest
    Write-Info "Make sure PostgreSQL is running and credentials in config.py are correct."
    exit 1
}

Write-Host ""

# ===========================================================================
# STEP 3: Downgrade to Base
# ===========================================================================

Write-Info "Step 3/5: Downgrading database to base state..."
Write-Verbose-Custom "Running: alembic downgrade base"

$output = & alembic downgrade base 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Success "Database downgraded to base state"
    Write-Verbose-Custom $output
} else {
    Write-Error-Custom "Failed to downgrade database"
    Write-Error-Custom $output
    Write-Host ""
    Write-Info "This might happen if the database is already clean."
    Write-Info "Continuing with upgrade..."
}

Write-Host ""

# ===========================================================================
# STEP 4: Upgrade to Latest
# ===========================================================================

Write-Info "Step 4/5: Upgrading database to latest schema..."
Write-Verbose-Custom "Running: alembic upgrade head"

$output = & alembic upgrade head 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Success "Database upgraded to latest schema"
    Write-Verbose-Custom $output
} else {
    Write-Error-Custom "Failed to upgrade database!"
    Write-Error-Custom $output
    exit 1
}

Write-Host ""

# ===========================================================================
# STEP 5: Verify Schema
# ===========================================================================

Write-Info "Step 5/5: Verifying schema..."

$schemaTest = python -c "
from app.db.session import engine, Base
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()
print(f'TABLES:{len(tables)}')
for table in sorted(tables):
    indexes = inspector.get_indexes(table)
    print(f'TABLE:{table}:{len(indexes)}')
" 2>&1

if ($schemaTest -match "TABLES:") {
    $tableCount = [regex]::Match($schemaTest, "TABLES:(\d+)").Groups[1].Value
    Write-Success "Database schema verified - $tableCount tables created"
    Write-Verbose-Custom "Table summary:"
    foreach ($line in $schemaTest -split "\n") {
        if ($line -match "TABLE:") {
            $parts = $line -split ":"
            Write-Verbose-Custom "  - $($parts[1]): $($parts[2]) indexes"
        }
    }
} else {
    Write-Warning-Custom "Could not verify schema, but migration appeared successful"
    Write-Verbose-Custom $schemaTest
}

Write-Host ""

# ===========================================================================
# SUCCESS
# ===========================================================================

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor $colors.Green
Write-Host "║  ✅ Database Reset Complete!                                  ║" -ForegroundColor $colors.Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor $colors.Green
Write-Host ""

Write-Info "Next steps:"
Write-Info "1. Start the FastAPI application: python -m uvicorn app.main:app --reload"
Write-Info "2. Verify tables are created correctly in pgAdmin or psql"
Write-Info "3. Check application logs for any startup errors"
Write-Host ""

Write-Info "To check current migration status:"
Write-Info "  alembic current"
Write-Host ""

Write-Info "To see migration history:"
Write-Info "  alembic history --verbose"
Write-Host ""

# Deactivate is implicit when script ends
Write-Info "Virtual environment still active. Type 'deactivate' to exit."
