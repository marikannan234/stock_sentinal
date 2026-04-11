# Migration Management Script for Stock Sentinel
# Automatically detects and manages Alembic migrations in Docker containers

param(
    [ValidateSet("status", "upgrade", "downgrade", "history", "restart")]
    [string]$Action = "status",
    
    [string]$Revision = "head"
)

$BACKEND_CONTAINER = "stocksentinel-backend"
$DB_CONTAINER = "stocksentinel-db"

function Get-ContainerStatus {
    $container = docker ps --filter "name=$BACKEND_CONTAINER" --format "{{.Names}}"
    return $container -eq $BACKEND_CONTAINER
}

function Ensure-ContainersRunning {
    Write-Host "🔍 Checking container status..." -ForegroundColor Cyan
    
    $running = Get-ContainerStatus
    if (-not $running) {
        Write-Host "⚠️  Containers not running. Starting..." -ForegroundColor Yellow
        Set-Location $PSScriptRoot
        docker compose up -d
        Start-Sleep -Seconds 15
    }
    
    Write-Host "✅ Backend container is running" -ForegroundColor Green
}

function Show-MigrationStatus {
    Write-Host "`n📊 Current Migration Status:" -ForegroundColor Cyan
    docker exec $BACKEND_CONTAINER alembic current
    
    Write-Host "`n📜 Migration History:" -ForegroundColor Cyan
    docker exec $BACKEND_CONTAINER alembic history
}

function Run-MigrationUpgrade {
    Write-Host "`n⬆️  Applying migrations..." -ForegroundColor Cyan
    
    docker exec $BACKEND_CONTAINER alembic upgrade $Revision
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ Database migration applied successfully" -ForegroundColor Green
        Write-Host "🎉 Revision: $Revision" -ForegroundColor Green
    } else {
        Write-Host "`n❌ Migration failed!" -ForegroundColor Red
        exit 1
    }
}

function Run-MigrationDowngrade {
    Write-Host "`n⬇️  Rolling back migrations..." -ForegroundColor Cyan
    
    docker exec $BACKEND_CONTAINER alembic downgrade $Revision
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ Database rolled back successfully" -ForegroundColor Green
        Write-Host "🔙 Revision: $Revision" -ForegroundColor Green
    } else {
        Write-Host "`n❌ Rollback failed!" -ForegroundColor Red
        exit 1
    }
}

function Show-MigrationHistory {
    Write-Host "`n📜 Complete Migration History:" -ForegroundColor Cyan
    docker exec $BACKEND_CONTAINER alembic history
}

function Restart-Containers {
    Write-Host "`n🔄 Restarting containers..." -ForegroundColor Cyan
    Set-Location $PSScriptRoot
    docker compose down
    docker compose up -d
    
    Start-Sleep -Seconds 15
    Write-Host "✅ Containers restarted" -ForegroundColor Green
    Write-Host "   - Migrations auto-applied on startup" -ForegroundColor Green
}

# Main execution
Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Blue
Write-Host "║  Stock Sentinel Migration Manager     ║" -ForegroundColor Blue
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Blue

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "📅 Timestamp: $timestamp`n"

Ensure-ContainersRunning

switch ($Action) {
    "status" {
        Show-MigrationStatus
    }
    "upgrade" {
        Run-MigrationUpgrade
        Write-Host "`n" + ("─" * 40) + "`n"
        Show-MigrationStatus
    }
    "downgrade" {
        Run-MigrationDowngrade
        Write-Host "`n" + ("─" * 40) + "`n"
        Show-MigrationStatus
    }
    "history" {
        Show-MigrationHistory
    }
    "restart" {
        Restart-Containers
        Show-MigrationStatus
    }
}

Write-Host "`n✨ Done!" -ForegroundColor Green
