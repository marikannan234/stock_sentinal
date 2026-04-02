#!/usr/bin/env pwsh

# ============================================================================
# Stock Sentinel Alert System - Quick Test Script
# ============================================================================
# Run this script to create test alerts and watch them trigger
# 
# Usage:
#   .\test_alerts.ps1                    (Production mode, 10-min cooldown)
#   .\test_alerts.ps1 -DevMode            (Dev mode, no cooldown)
#   .\test_alerts.ps1 -Verbose             (Show detailed output)

param(
    [switch]$DevMode = $false,
    [switch]$Verbose = $false
)

# Configuration
$TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0aGFsYXBhdGh5a2FubmFuMTIzQGdtYWlsLmNvbSIsImV4cCI6MTc3NTEzODM2OH0.KgmlnUl-vOR1_HUNeGwcPgbN6EG-6K2I6Dn522Fnk-0"
$API_URL = "http://localhost:8000/api/alerts"
$SCHEDULER_INTERVAL = 30

Write-Host "`n" -NoNewline
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║      Stock Sentinel Alert System - Test Script             ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

Write-Host "`nℹ️  Configuration:" -ForegroundColor Blue
Write-Host "   API Endpoint: $API_URL"
Write-Host "   Scheduler Interval: $SCHEDULER_INTERVAL seconds"
if ($DevMode) {
    Write-Host "   Mode: 🔧 DEV MODE (cooldown disabled)" -ForegroundColor Yellow
} else {
    Write-Host "   Mode: 📋 PRODUCTION MODE (10-min cooldown)" -ForegroundColor Yellow
}

# Helper function
function Create-TestAlert {
    param(
        [string]$Symbol,
        [string]$Type,
        [double]$Target,
        [string]$Condition = $null,
        [string]$Description = ""
    )
    
    $body = @{
        stock_symbol = $Symbol
        alert_type = $Type
        target_value = $Target
    }
    
    if ($Condition) {
        $body.condition = $Condition
    }
    
    $json = $body | ConvertTo-Json
    $headers = @{
        "Authorization" = "Bearer $TOKEN"
        "Content-Type" = "application/json"
    }
    
    try {
        $response = Invoke-WebRequest -Uri $API_URL -Method POST -Headers $headers -Body $json -ErrorAction Stop
        $alertData = $response.Content | ConvertFrom-Json
        $alertId = $alertData.id
        
        Write-Host "   ✓ $Symbol $Type alert created" -ForegroundColor Green
        Write-Host "     ID: $alertId | Target: $Target $(if($Condition) { "| Condition: $Condition" })" -ForegroundColor Gray
        if ($Description) {
            Write-Host "     $Description" -ForegroundColor Gray
        }
        
        return $alertId
    } catch {
        Write-Host "   ✗ Failed: $_" -ForegroundColor Red
        return $null
    }
}

# Create alerts
Write-Host "`n📝 Creating test alerts:" -ForegroundColor Blue

$alerts = @()
$alerts += @{ symbol="AAPL"; type="PRICE"; target=100.0; condition=">"; desc="Triggers if AAPL > $100" }
$alerts += @{ symbol="MSFT"; type="PERCENTAGE_CHANGE"; target=0.1; desc="Triggers on 0.1% change" }
$alerts += @{ symbol="GOOGL"; type="VOLUME_SPIKE"; target=20000000.0; desc="Triggers on volume spike" }
$alerts += @{ symbol="TSLA"; type="CRASH"; target=5.0; desc="Triggers on 5% crash" }

$alertIds = @()
foreach ($alert in $alerts) {
    $id = Create-TestAlert -Symbol $alert.symbol -Type $alert.type -Target $alert.target -Condition $alert.condition -Description $alert.desc
    if ($id) {
        $alertIds += @{ id=$id; symbol=$alert.symbol; type=$alert.type }
    }
}

if ($alertIds.Count -eq 0) {
    Write-Host "`n❌ No alerts created. Check your token and API endpoint." -ForegroundColor Red
    exit 1
}

# Wait for scheduler
Write-Host "`n⏳ Waiting for scheduler to run ($SCHEDULER_INTERVAL seconds)..." -ForegroundColor Blue
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
for ($i = 0; $i -lt $SCHEDULER_INTERVAL; $i++) {
    $remaining = $SCHEDULER_INTERVAL - $i
    Write-Host -NoNewline "`r   Progress: $remaining seconds remaining  "
    Start-Sleep -Seconds 1
}
$stopwatch.Stop()
Write-Host -NoNewline "`r"
Write-Host "   ✓ Scheduler cycle complete ($($stopwatch.Elapsed.TotalSeconds)s)" -ForegroundColor Green

# Check results
Write-Host "`n📊 Results:" -ForegroundColor Blue

try {
    # Get alert history
    $historyCmd = "SELECT id, alert_id, stock_symbol, alert_type, triggered_at, email_sent FROM alert_history WHERE triggered_at > NOW() - INTERVAL '5 minutes' ORDER BY triggered_at DESC;"
    
    Write-Host "`n   Recent triggers:" -ForegroundColor Cyan
    
    $history = docker exec -it stocksentinel-db psql -U stocksentinel -d stocksentinel -t -c $historyCmd 2>$null
    
    if ($history -and $history.Trim()) {
        $rawLines = $history -split "`n" | Where-Object { $_ -match '\|' }
        if ($rawLines.Count -gt 0) {
            foreach ($line in $rawLines) {
                $parts = $line -split '\|' | ForEach-Object { $_.Trim() }
                if ($parts.Count -ge 6) {
                    $id = $parts[0]
                    $alertId = $parts[1]
                    $symbol = $parts[2]
                    $type = $parts[3]
                    $time = $parts[4]
                    $emailSent = $parts[5] -like "*t"
                    
                    $emailIcon = if ($emailSent) { "✓" } else { "✗" }
                    Write-Host "      $emailIcon Alert #$alertId ($symbol $type) - Sent: $emailSent" -ForegroundColor $(if($emailSent) { "Green" } else { "Yellow" })
                }
            }
        } else {
            Write-Host "      No triggers yet. Wait a bit longer or check logs." -ForegroundColor Yellow
        }
    } else {
        Write-Host "      No triggers yet. Wait a bit longer or check logs." -ForegroundColor Yellow
    }
} catch {
    Write-Host "      Could not query database. Run manually:" -ForegroundColor Yellow
    Write-Host "      docker exec -it stocksentinel-db psql -U stocksentinel -d stocksentinel" -ForegroundColor Gray
}

# Check alert state
try {
    Write-Host "`n   Current alert state:" -ForegroundColor Cyan
    
    $stateCmd = "SELECT id, stock_symbol, alert_type, is_triggered, last_triggered_at FROM alerts WHERE id IN (" + (($alertIds | ForEach-Object { $_.id }) -join ",") + ") ORDER BY id;"
    
    $state = docker exec -it stocksentinel-db psql -U stocksentinel -d stocksentinel -t -c $stateCmd 2>$null
    
    if ($state -and $state.Trim()) {
        $lines = $state -split "`n" | Where-Object { $_ -match '\|' }
        foreach ($line in $lines) {
            $parts = $line -split '\|' | ForEach-Object { $_.Trim() }
            if ($parts.Count -ge 5) {
                $id = $parts[0]
                $symbol = $parts[1]
                $type = $parts[2]
                $triggered = $parts[3] -like "*t"
                $lastTime = $parts[4]
                
                $triggeredIcon = if ($triggered) { "💤" } else { "🔄" }
                $triggeredText = if ($triggered) { "In cooldown" } else { "Ready" }
                Write-Host "      $triggeredIcon #$id $symbol $type - $triggeredText" -ForegroundColor $(if($triggered) { "Yellow" } else { "Green" })
            }
        }
    }
} catch {
    # Silently fail
}

# Show what to do next
Write-Host "`n📋 Next steps:" -ForegroundColor Blue
Write-Host "   1. Check logs in real-time:" -ForegroundColor Gray
Write-Host "      cd backend && tail -f logs/app.log | grep -E '(ALERT|cooldown|Re-arm|Email)'" -ForegroundColor Cyan
Write-Host ""
Write-Host "   2. Monitor cooldown behavior:" -ForegroundColor Gray
Write-Host "      watch \"docker exec -it stocksentinel-db psql -U stocksentinel -d stocksentinel -c 'SELECT id, stock_symbol, is_triggered, last_triggered_at FROM alerts WHERE is_active;'\"" -ForegroundColor Cyan
Write-Host ""
Write-Host "   3. View triggered alerts:" -ForegroundColor Gray
Write-Host "      docker exec -it stocksentinel-db psql -U stocksentinel -d stocksentinel -c \"SELECT * FROM alert_history ORDER BY triggered_at DESC;\"" -ForegroundColor Cyan

if ($DevMode) {
    Write-Host "`n⚠️  Dev Mode is ON - cooldown is bypassed!" -ForegroundColor Yellow
    Write-Host "   Alerts can trigger multiple times immediately." -ForegroundColor Gray
} else {
    Write-Host "`n💡 Production Mode:" -ForegroundColor Blue
    Write-Host "   Alerts will skip triggers for 10 minutes after each email." -ForegroundColor Gray
    Write-Host "   To test without cooldown, use: .\test_alerts.ps1 -DevMode" -ForegroundColor Gray
}

Write-Host "`n✅ Test script complete!" -ForegroundColor Green
Write-Host ""
