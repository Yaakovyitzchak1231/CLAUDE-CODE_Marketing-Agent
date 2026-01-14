# Configure External n8n Setup Script
# For Windows PowerShell
# Configures the system to use external n8n instance instead of local Docker n8n

$ErrorActionPreference = "Stop"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "External n8n Configuration Script" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$EXTERNAL_N8N_URL = "https://n8n-de5xsqtqma-wl.a.run.app"
$ENV_FILE = ".env"
$DOCKER_COMPOSE_FILE = "docker-compose.yml"
$BACKUP_SUFFIX = ".backup-" + (Get-Date -Format "yyyyMMdd-HHmmss")

# Function to create backup
function Backup-File {
    param($FilePath)
    $BackupPath = "$FilePath$BACKUP_SUFFIX"
    Copy-Item $FilePath $BackupPath -Force
    Write-Host "✓ Created backup: $BackupPath" -ForegroundColor Green
}

# Function to check if file exists
function Test-FileExists {
    param($FilePath)
    if (!(Test-Path $FilePath)) {
        Write-Host "✗ Error: $FilePath not found!" -ForegroundColor Red
        Write-Host "  Make sure you're running this script from the project root directory." -ForegroundColor Yellow
        exit 1
    }
}

# Step 1: Check prerequisites
Write-Host "Step 1: Checking prerequisites..." -ForegroundColor Yellow
Test-FileExists $ENV_FILE
Test-FileExists $DOCKER_COMPOSE_FILE
Write-Host "✓ All required files found" -ForegroundColor Green
Write-Host ""

# Step 2: Backup files
Write-Host "Step 2: Creating backups..." -ForegroundColor Yellow
Backup-File $ENV_FILE
Backup-File $DOCKER_COMPOSE_FILE
Write-Host ""

# Step 3: Configure docker-compose.yml
Write-Host "Step 3: Configuring docker-compose.yml..." -ForegroundColor Yellow

$dockerComposeContent = Get-Content $DOCKER_COMPOSE_FILE -Raw

# Check if n8n service is already commented out
if ($dockerComposeContent -match "^\s*#\s*n8n:") {
    Write-Host "⚠ n8n service appears to be already commented out" -ForegroundColor Yellow
} else {
    # Comment out n8n service section
    $lines = Get-Content $DOCKER_COMPOSE_FILE
    $inN8nSection = $false
    $modifiedLines = @()

    foreach ($line in $lines) {
        # Detect start of n8n service
        if ($line -match "^\s*n8n:\s*$") {
            $inN8nSection = $true
            $modifiedLines += "  # COMMENTED OUT - USING EXTERNAL N8N"
            $modifiedLines += "  # $line"
            continue
        }

        # Detect end of n8n service (next service or empty line after networks)
        if ($inN8nSection -and ($line -match "^\s*[a-z_]+:\s*$" -and $line -notmatch "^\s*-")) {
            $inN8nSection = $false
        }

        # Comment out lines in n8n section
        if ($inN8nSection) {
            if ($line -match "^\s*$") {
                $modifiedLines += $line
            } else {
                $modifiedLines += "  # $line"
            }
        } else {
            $modifiedLines += $line
        }
    }

    # Save modified docker-compose.yml
    $modifiedLines | Set-Content $DOCKER_COMPOSE_FILE -Encoding UTF8
    Write-Host "✓ Commented out local n8n service in docker-compose.yml" -ForegroundColor Green
}
Write-Host ""

# Step 4: Configure .env file
Write-Host "Step 4: Configuring .env file..." -ForegroundColor Yellow

$envContent = Get-Content $ENV_FILE

# Check if external n8n config already exists
$hasExternalConfig = $envContent | Where-Object { $_ -match "N8N_EXTERNAL_URL" }

if ($hasExternalConfig) {
    Write-Host "⚠ External n8n configuration already exists in .env" -ForegroundColor Yellow
    Write-Host "  Current configuration:" -ForegroundColor Yellow
    $envContent | Where-Object { $_ -match "N8N_EXTERNAL_URL|N8N_WEBHOOK_URL|N8N_API_KEY" } | ForEach-Object {
        Write-Host "    $_" -ForegroundColor Cyan
    }
} else {
    # Comment out local n8n settings
    $modifiedEnv = @()
    $inN8nSection = $false

    foreach ($line in $envContent) {
        # Detect n8n configuration section
        if ($line -match "N8N CONFIGURATION") {
            $inN8nSection = $true
            $modifiedEnv += $line
            continue
        }

        # Exit n8n section
        if ($inN8nSection -and $line -match "^# =====") {
            $inN8nSection = $false

            # Add external n8n configuration before next section
            $modifiedEnv += ""
            $modifiedEnv += "# External n8n (Cloud Run) - CONFIGURED BY SCRIPT"
            $modifiedEnv += "N8N_EXTERNAL_URL=$EXTERNAL_N8N_URL"
            $modifiedEnv += "N8N_WEBHOOK_URL=$EXTERNAL_N8N_URL/webhook"
            $modifiedEnv += "N8N_API_KEY=your_n8n_api_key_here"
            $modifiedEnv += ""
            $modifiedEnv += $line
            continue
        }

        # Comment out local n8n settings
        if ($inN8nSection -and $line -match "^(N8N_USER|N8N_PASSWORD|N8N_HOST|N8N_API_KEY|TIMEZONE)=") {
            $modifiedEnv += "# $line"
        } else {
            $modifiedEnv += $line
        }
    }

    # Save modified .env
    $modifiedEnv | Set-Content $ENV_FILE -Encoding UTF8
    Write-Host "✓ Updated .env file with external n8n configuration" -ForegroundColor Green
}
Write-Host ""

# Step 5: Get API Key from user
Write-Host "Step 5: n8n API Key Configuration" -ForegroundColor Yellow
Write-Host ""
Write-Host "To complete the setup, you need to get your n8n API key:" -ForegroundColor White
Write-Host "  1. Go to: $EXTERNAL_N8N_URL" -ForegroundColor Cyan
Write-Host "  2. Login to your n8n instance" -ForegroundColor Cyan
Write-Host "  3. Go to: Settings → API" -ForegroundColor Cyan
Write-Host "  4. Click 'Create API Key'" -ForegroundColor Cyan
Write-Host "  5. Copy the generated API key" -ForegroundColor Cyan
Write-Host ""

$apiKey = Read-Host "Enter your n8n API key (or press Enter to skip)"

if ($apiKey -and $apiKey -ne "") {
    # Update API key in .env
    $envContent = Get-Content $ENV_FILE
    $envContent = $envContent -replace "N8N_API_KEY=your_n8n_api_key_here", "N8N_API_KEY=$apiKey"
    $envContent | Set-Content $ENV_FILE -Encoding UTF8
    Write-Host "✓ Updated n8n API key in .env" -ForegroundColor Green
} else {
    Write-Host "⚠ Skipped API key configuration" -ForegroundColor Yellow
    Write-Host "  You can manually edit .env and update N8N_API_KEY later" -ForegroundColor Yellow
}
Write-Host ""

# Step 6: Update streamlit_dashboard configuration
Write-Host "Step 6: Updating service configurations..." -ForegroundColor Yellow

$dockerComposeContent = Get-Content $DOCKER_COMPOSE_FILE -Raw

# Update streamlit N8N_API_URL to use external n8n
$dockerComposeContent = $dockerComposeContent -replace "N8N_API_URL=http://n8n:5678/api/v1", "N8N_API_URL=$EXTERNAL_N8N_URL/api/v1"

$dockerComposeContent | Set-Content $DOCKER_COMPOSE_FILE -Encoding UTF8
Write-Host "✓ Updated streamlit dashboard to use external n8n API" -ForegroundColor Green
Write-Host ""

# Step 7: Summary
Write-Host "================================================" -ForegroundColor Green
Write-Host "Configuration Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Changes made:" -ForegroundColor White
Write-Host "  ✓ Commented out local n8n service in docker-compose.yml" -ForegroundColor Green
Write-Host "  ✓ Updated .env with external n8n configuration" -ForegroundColor Green
Write-Host "  ✓ Updated streamlit to use external n8n API" -ForegroundColor Green
Write-Host "  ✓ Backups created with suffix: $BACKUP_SUFFIX" -ForegroundColor Green
Write-Host ""

Write-Host "External n8n URL: $EXTERNAL_N8N_URL" -ForegroundColor Cyan
Write-Host ""

# Step 8: Next steps
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Review the .env file and ensure N8N_API_KEY is set:" -ForegroundColor White
Write-Host "     notepad .env" -ForegroundColor Cyan
Write-Host ""
Write-Host "  2. Restart Docker services:" -ForegroundColor White
Write-Host "     docker-compose down" -ForegroundColor Cyan
Write-Host "     docker-compose up -d" -ForegroundColor Cyan
Write-Host ""
Write-Host "  3. Verify services are running:" -ForegroundColor White
Write-Host "     docker-compose ps" -ForegroundColor Cyan
Write-Host ""
Write-Host "  4. Configure n8n workflows:" -ForegroundColor White
Write-Host "     - Go to: $EXTERNAL_N8N_URL" -ForegroundColor Cyan
Write-Host "     - Import workflows from n8n-workflows/ folder" -ForegroundColor Cyan
Write-Host "     - Update PostgreSQL credentials to connect to local DB" -ForegroundColor Cyan
Write-Host ""

Write-Host "Note: Your local PostgreSQL is not exposed to the internet." -ForegroundColor Yellow
Write-Host "      For n8n to access it, you'll need to:" -ForegroundColor Yellow
Write-Host "      - Use CloudFlare Tunnel, ngrok, or similar" -ForegroundColor Yellow
Write-Host "      - OR migrate to Cloud SQL for shared access" -ForegroundColor Yellow
Write-Host ""

Write-Host "Configuration script completed successfully! 🎉" -ForegroundColor Green
