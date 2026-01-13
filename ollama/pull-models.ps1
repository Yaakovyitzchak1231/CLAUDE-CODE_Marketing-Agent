# Pull required models for the B2B Marketing Automation Platform
# PowerShell version

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Ollama Model Setup" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Wait for Ollama to be ready
Write-Host "Waiting for Ollama service to start..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0

while ($attempt -lt $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            break
        }
    } catch {
        Write-Host "  Still waiting... (Attempt $($attempt + 1)/$maxAttempts)" -ForegroundColor Gray
        Start-Sleep -Seconds 5
        $attempt++
    }
}

if ($attempt -eq $maxAttempts) {
    Write-Host "✗ Ollama failed to start" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Ollama is ready!" -ForegroundColor Green
Write-Host ""

# Pull Llama 3 8B
Write-Host "Pulling Llama 3 8B model..." -ForegroundColor Yellow
Write-Host "  This may take several minutes (4.7GB download)" -ForegroundColor Gray
docker exec ollama ollama pull llama3:8b

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Llama 3 8B pulled successfully!" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to pull Llama 3 8B" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Pull Mistral 7B
Write-Host "Pulling Mistral 7B model (alternative)..." -ForegroundColor Yellow
Write-Host "  This may take several minutes (4.1GB download)" -ForegroundColor Gray
docker exec ollama ollama pull mistral:7b

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Mistral 7B pulled successfully!" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to pull Mistral 7B" -ForegroundColor Red
}
Write-Host ""

# Optional models (commented out)
# Write-Host "Pulling CodeLlama 7B (optional)..." -ForegroundColor Yellow
# docker exec ollama ollama pull codellama:7b
# Write-Host ""

# List all models
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Available Models:" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
docker exec ollama ollama list

Write-Host ""
Write-Host "✓ Model setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Usage examples:" -ForegroundColor Cyan
Write-Host '  # Test Llama 3:' -ForegroundColor Gray
Write-Host '  curl http://localhost:11434/api/generate -d "{\"model\":\"llama3:8b\",\"prompt\":\"Hello\"}"' -ForegroundColor White
Write-Host ""
Write-Host '  # Test Mistral:' -ForegroundColor Gray
Write-Host '  curl http://localhost:11434/api/generate -d "{\"model\":\"mistral:7b\",\"prompt\":\"Hello\"}"' -ForegroundColor White
