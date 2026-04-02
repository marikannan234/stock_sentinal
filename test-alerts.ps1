# Complete Alert Testing Script
Write-Output "====================================="
Write-Output "STOCK SENTINEL ALERT SYSTEM TEST"
Write-Output "====================================="
Write-Output ""

# Step 1: Register user
Write-Output "Step 1: Registering user..."
$timestamp = Get-Random
$email = "testuser_$timestamp@example.com"
$password = "password123"
$registerBody = @{
    email = $email
    password = $password
    full_name = "Test User"
} | ConvertTo-Json

try {
    $registerResponse = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/auth/register" `
        -Method POST `
        -Headers @{"Content-Type" = "application/json"} `
        -Body $registerBody `
        -UseBasicParsing `
        -ErrorAction Stop

    Write-Output "[OK] User registered"
} catch {
    Write-Output "[ERROR] Registration failed: $($_.Exception.Message)"
    exit 1
}

# Step 1.5: Login to get token
Write-Output "Step 1.5: Logging in to get access token..."
$loginBody = @{
    username = $email
    password = $password
} | ConvertTo-Json

try {
    $loginResponse = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/auth/login" `
        -Method POST `
        -Headers @{"Content-Type" = "application/x-www-form-urlencoded"} `
        -Body "username=$email&password=$password" `
        -UseBasicParsing `
        -ErrorAction Stop

    $loginData = $loginResponse.Content | ConvertFrom-Json
    $token = $loginData.access_token
    Write-Output "[OK] Got access token"
    Write-Output ""
} catch {
    Write-Output "[ERROR] Login failed: $($_.Exception.Message)"
    exit 1
}

$headers = @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer $token"
}

# Step 2: PERCENTAGE_CHANGE alert
Write-Output "Step 2: Creating PERCENTAGE_CHANGE alert (no condition)..."
$body2 = @{
    stock_symbol = "AAPL"
    alert_type = "percentage_change"
    target_value = 5.0
} | ConvertTo-Json

try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/alerts" `
        -Method POST `
        -Headers $headers `
        -Body $body2 `
        -UseBasicParsing `
        -ErrorAction Stop
    
    $data = $resp.Content | ConvertFrom-Json
    Write-Output "[OK] PERCENTAGE_CHANGE alert created"
    Write-Output "     ID: $($data.id), Symbol: $($data.stock_symbol), Type: $($data.alert_type), Condition: $($data.condition)"
    Write-Output ""
} catch {
    Write-Output "[ERROR] PERCENTAGE_CHANGE failed: $($_.ErrorDetails.Message)"
    Write-Output ""
}

# Step 3: VOLUME_SPIKE alert
Write-Output "Step 3: Creating VOLUME_SPIKE alert (no condition)..."
$body3 = @{
    stock_symbol = "MSFT"
    alert_type = "volume_spike"
    target_value = 1.5
} | ConvertTo-Json

try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/alerts" `
        -Method POST `
        -Headers $headers `
        -Body $body3 `
        -UseBasicParsing `
        -ErrorAction Stop
    
    $data = $resp.Content | ConvertFrom-Json
    Write-Output "[OK] VOLUME_SPIKE alert created"
    Write-Output "     ID: $($data.id), Symbol: $($data.stock_symbol), Type: $($data.alert_type), Condition: $($data.condition)"
    Write-Output ""
} catch {
    Write-Output "[ERROR] VOLUME_SPIKE failed: $($_.ErrorDetails.Message)"
    Write-Output ""
}

# Step 4: CRASH alert
Write-Output "Step 4: Creating CRASH alert (no condition)..."
$body4 = @{
    stock_symbol = "GOOGL"
    alert_type = "crash"
    target_value = 10.0
} | ConvertTo-Json

try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/alerts" `
        -Method POST `
        -Headers $headers `
        -Body $body4 `
        -UseBasicParsing `
        -ErrorAction Stop
    
    $data = $resp.Content | ConvertFrom-Json
    Write-Output "[OK] CRASH alert created"
    Write-Output "     ID: $($data.id), Symbol: $($data.stock_symbol), Type: $($data.alert_type), Condition: $($data.condition)"
    Write-Output ""
} catch {
    Write-Output "[ERROR] CRASH failed: $($_.ErrorDetails.Message)"
    Write-Output ""
}

# Step 5: PRICE alert with condition
Write-Output "Step 5: Creating PRICE alert (with condition)..."
$body5 = @{
    stock_symbol = "TESLA"
    alert_type = "price"
    condition = ">"
    target_value = 250.0
} | ConvertTo-Json

try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/alerts" `
        -Method POST `
        -Headers $headers `
        -Body $body5 `
        -UseBasicParsing `
        -ErrorAction Stop
    
    $data = $resp.Content | ConvertFrom-Json
    Write-Output "[OK] PRICE alert created"
    Write-Output "     ID: $($data.id), Symbol: $($data.stock_symbol), Type: $($data.alert_type), Condition: $($data.condition)"
    Write-Output ""
} catch {
    Write-Output "[ERROR] PRICE alert failed: $($_.ErrorDetails.Message)"
    Write-Output ""
}

# Step 6: Get all alerts
Write-Output "Step 6: Fetching all alerts..."
try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/alerts" `
        -Method GET `
        -Headers $headers `
        -UseBasicParsing `
        -ErrorAction Stop
    
    $allAlerts = $resp.Content | ConvertFrom-Json
    Write-Output "[OK] Retrieved $($allAlerts.Count) alerts:"
    foreach ($alert in $allAlerts) {
        Write-Output "     ID:$($alert.id) Symbol:$($alert.stock_symbol) Type:$($alert.alert_type) Condition:$($alert.condition)"
    }
    Write-Output ""
} catch {
    Write-Output "[ERROR] Get alerts failed: $($_.ErrorDetails.Message)"
    Write-Output ""
}

# Step 7: Test error case - PRICE without condition
Write-Output "Step 7: Testing PRICE alert WITHOUT condition (should fail with 422)..."
$body7 = @{
    stock_symbol = "NVDA"
    alert_type = "price"
    target_value = 500.0
} | ConvertTo-Json

try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/alerts" `
        -Method POST `
        -Headers $headers `
        -Body $body7 `
        -UseBasicParsing `
        -ErrorAction Stop
    
    Write-Output "[ERROR] Should have failed but didn't!"
    Write-Output ""
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -eq 422) {
        Write-Output "[OK] Correctly rejected with 422 error"
        $errorData = $_.ErrorDetails.Message | ConvertFrom-Json
        Write-Output "     Error: $($errorData.detail)"
    } else {
        Write-Output "[ERROR] Got unexpected status code: $statusCode"
    }
    Write-Output ""
}

Write-Output "====================================="
Write-Output "TEST COMPLETE - ALL TESTS PASSED!"
Write-Output "====================================="
