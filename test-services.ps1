# Test All Services Connectivity
# B2B Marketing Automation Platform - PowerShell Version

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Service Connectivity Test" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Test counters
$script:Passed = 0
$script:Failed = 0

# Test function
function Test-Service {
    param(
        [string]$Name,
        [string]$Url,
        [int]$ExpectedCode = 200
    )

    Write-Host ("Testing {0,-25}" -f $Name) -NoNewline

    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec 10 -UseBasicParsing -ErrorAction SilentlyContinue
        $status = $response.StatusCode

        if ($status -eq $ExpectedCode) {
            Write-Host "✓ PASS (HTTP $status)" -ForegroundColor Green
            $script:Passed++
            return $true
        } else {
            Write-Host "✗ FAIL (HTTP $status, expected $ExpectedCode)" -ForegroundColor Red
            $script:Failed++
            return $false
        }
    } catch {
        $status = $_.Exception.Response.StatusCode.value__
        if ($null -eq $status) {
            $status = "No response"
        }

        # For some services, connection refused is expected for HTTP
        if ($ExpectedCode -eq 0 -and $status -eq "No response") {
            Write-Host "✓ PASS (Service running)" -ForegroundColor Green
            $script:Passed++
            return $true
        } else {
            Write-Host "✗ FAIL ($status)" -ForegroundColor Red
            $script:Failed++
            return $false
        }
    }
}

# Wait for services
Write-Host "Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
Write-Host ""

# ==================== CORE INFRASTRUCTURE ====================
Write-Host "Core Infrastructure:" -ForegroundColor Cyan
Write-Host "-------------------"

# Test database and Redis (check if containers are running)
$postgresRunning = docker ps --filter "name=postgres" --filter "status=running" -q
if ($postgresRunning) {
    Write-Host ("Testing {0,-25}" -f "PostgreSQL") -NoNewline
    Write-Host "✓ PASS (Container running)" -ForegroundColor Green
    $script:Passed++
} else {
    Write-Host ("Testing {0,-25}" -f "PostgreSQL") -NoNewline
    Write-Host "✗ FAIL (Container not running)" -ForegroundColor Red
    $script:Failed++
}

$redisRunning = docker ps --filter "name=redis" --filter "status=running" -q
if ($redisRunning) {
    Write-Host ("Testing {0,-25}" -f "Redis") -NoNewline
    Write-Host "✓ PASS (Container running)" -ForegroundColor Green
    $script:Passed++
} else {
    Write-Host ("Testing {0,-25}" -f "Redis") -NoNewline
    Write-Host "✗ FAIL (Container not running)" -ForegroundColor Red
    $script:Failed++
}

Test-Service -Name "Nginx" -Url "http://localhost/health" -ExpectedCode 200

Write-Host ""

# ==================== AI & DATA SERVICES ====================
Write-Host "AI & Data Services:" -ForegroundColor Cyan
Write-Host "-------------------"

Test-Service -Name "Ollama" -Url "http://localhost:11434/api/tags" -ExpectedCode 200
Test-Service -Name "Chroma" -Url "http://localhost:8000/api/v1/heartbeat" -ExpectedCode 200
Test-Service -Name "SearXNG" -Url "http://localhost:8080" -ExpectedCode 200

Write-Host ""

# ==================== ORCHESTRATION & DASHBOARD ====================
Write-Host "Orchestration & Dashboard:" -ForegroundColor Cyan
Write-Host "--------------------------"

Test-Service -Name "n8n" -Url "http://localhost:5678" -ExpectedCode 200
Test-Service -Name "Streamlit Dashboard" -Url "http://localhost:8501/_stcore/health" -ExpectedCode 200
Test-Service -Name "Matomo Analytics" -Url "http://localhost:8081" -ExpectedCode 200

Write-Host ""

# ==================== UTILITIES ====================
Write-Host "Utilities:" -ForegroundColor Cyan
Write-Host "----------"

Test-Service -Name "Adminer" -Url "http://localhost:8082" -ExpectedCode 200

Write-Host ""

# ==================== NGINX REVERSE PROXY ROUTES ====================
Write-Host "Nginx Reverse Proxy Routes:" -ForegroundColor Cyan
Write-Host "---------------------------"

Test-Service -Name "Main Health" -Url "http://localhost/health" -ExpectedCode 200
Test-Service -Name "Dashboard Route" -Url "http://localhost/dashboard" -ExpectedCode 200
Test-Service -Name "n8n Route" -Url "http://localhost/n8n" -ExpectedCode 200
Test-Service -Name "Analytics Route" -Url "http://localhost/analytics/" -ExpectedCode 200
Test-Service -Name "Search Route" -Url "http://localhost/search/" -ExpectedCode 200
Test-Service -Name "Adminer Route" -Url "http://localhost/adminer/" -ExpectedCode 200

Write-Host ""

# ==================== DETAILED SERVICE CHECKS ====================
Write-Host "Detailed Service Checks:" -ForegroundColor Cyan
Write-Host "------------------------"

# Test PostgreSQL connection
Write-Host ("Testing {0,-25}" -f "PostgreSQL Connection") -NoNewline
$pgTest = docker exec postgres psql -U marketing_user -d marketing -c "SELECT 1" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ PASS" -ForegroundColor Green
    $script:Passed++
} else {
    Write-Host "✗ FAIL" -ForegroundColor Red
    $script:Failed++
}

# Test Redis connection
Write-Host ("Testing {0,-25}" -f "Redis Connection") -NoNewline
$redisTest = docker exec redis redis-cli ping 2>$null
if ($redisTest -eq "PONG") {
    Write-Host "✓ PASS" -ForegroundColor Green
    $script:Passed++
} else {
    Write-Host "✗ FAIL" -ForegroundColor Red
    $script:Failed++
}

# Test Ollama models
Write-Host ("Testing {0,-25}" -f "Ollama Models") -NoNewline
try {
    $ollamaModels = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -UseBasicParsing
    $modelCount = $ollamaModels.models.Count
    if ($modelCount -gt 0) {
        Write-Host "✓ PASS ($modelCount models available)" -ForegroundColor Green
        $script:Passed++
    } else {
        Write-Host "⚠ WARN (No models pulled yet. Run: .\ollama\pull-models.ps1)" -ForegroundColor Yellow
        $script:Failed++
    }
} catch {
    Write-Host "✗ FAIL" -ForegroundColor Red
    $script:Failed++
}

# Test Chroma collections
Write-Host ("Testing {0,-25}" -f "Chroma Collections") -NoNewline
try {
    $chromaCollections = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/collections" -UseBasicParsing
    $collectionCount = $chromaCollections.Count
    Write-Host "✓ PASS ($collectionCount collections)" -ForegroundColor Green
    $script:Passed++
} catch {
    Write-Host "✗ FAIL" -ForegroundColor Red
    $script:Failed++
}

Write-Host ""

# ==================== NETWORK CONNECTIVITY ====================
Write-Host "Network Connectivity:" -ForegroundColor Cyan
Write-Host "---------------------"

# Test inter-container networking
Write-Host ("Testing {0,-25}" -f "Container Network") -NoNewline
$networkTest = docker exec langchain_service ping -c 1 postgres 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ PASS" -ForegroundColor Green
    $script:Passed++
} else {
    Write-Host "✗ FAIL" -ForegroundColor Red
    $script:Failed++
}

Write-Host ""

# ==================== SUMMARY ====================
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

$total = $script:Passed + $script:Failed
Write-Host "Total Tests: $total"
Write-Host "Passed: $($script:Passed)" -ForegroundColor Green
Write-Host "Failed: $($script:Failed)" -ForegroundColor Red

if ($script:Failed -eq 0) {
    Write-Host ""
    Write-Host "✓ All services are operational!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Access points:"
    Write-Host "  Dashboard:  http://localhost/dashboard" -ForegroundColor White
    Write-Host "  n8n:        http://localhost/n8n" -ForegroundColor White
    Write-Host "  Analytics:  http://localhost/analytics" -ForegroundColor White
    Write-Host "  Database:   http://localhost/adminer" -ForegroundColor White
    Write-Host ""
    exit 0
} else {
    Write-Host ""
    Write-Host "⚠ Some services failed. Check logs:" -ForegroundColor Yellow
    Write-Host "  docker-compose logs [service-name]" -ForegroundColor White
    Write-Host ""
    exit 1
}
