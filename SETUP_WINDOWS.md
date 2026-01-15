# Windows Setup Guide - B2B Marketing Automation Platform

Complete setup guide for Windows users using Command Prompt or PowerShell.

## Prerequisites

### Required Software

1. **Docker Desktop for Windows**
   - Download: https://www.docker.com/products/docker-desktop/
   - Version: 20.10+
   - Make sure Docker Desktop is running before starting setup

2. **Git for Windows**
   - Download: https://git-scm.com/download/win
   - Or use GitHub Desktop

3. **System Requirements**
   - Windows 10/11 (64-bit)
   - 16GB+ RAM
   - 50GB+ free disk space
   - WSL2 enabled (Docker Desktop requirement)

## Quick Start for Windows

### Step 1: Clone Repository

**Using Command Prompt or PowerShell:**
```cmd
git clone https://github.com/Yaakovyitzchak1231/marketing-agent.git
cd marketing-agent
```

Or if the directory is named differently:
```cmd
cd "B2B Marketing System"
```

### Step 2: Create Environment File

**Using Command Prompt:**
```cmd
copy .env.example .env
notepad .env
```

**Using PowerShell:**
```powershell
Copy-Item .env.example .env
notepad .env
```

**Required edits in .env file:**
- Change `POSTGRES_PASSWORD` to a secure password
- Change `REDIS_PASSWORD` to a secure password
- Change `N8N_PASSWORD` to a secure password
- Add your `OPENAI_API_KEY` if you have one
- Add your `RUNWAY_API_KEY` if you have one

Save and close the file.

### Step 3: Start Docker Desktop

1. Open Docker Desktop application
2. Wait for Docker to fully start (whale icon in system tray should be steady)
3. Open Settings → Resources and ensure:
   - Memory: At least 8GB (16GB recommended)
   - Disk space: At least 50GB

### Step 4: Start All Services

**Using Command Prompt or PowerShell:**
```cmd
docker-compose up -d
```

**Wait 2-3 minutes** for all services to initialize.

**Check service status:**
```cmd
docker-compose ps
```

You should see all services with status "Up" or "running".

### Step 5: Pull Ollama Models

**Required step - pull the AI models:**

```cmd
docker exec ollama ollama pull llama3.1:8b
```

Wait for download to complete (this is ~4.7GB, may take 5-15 minutes).

**Optional: Pull alternative model:**
```cmd
docker exec ollama ollama pull mistral:7b
```

**Verify models are installed:**
```cmd
docker exec ollama ollama list
```

### Step 6: Initialize Chroma Vector Database

```cmd
docker exec langchain_service python /app/chroma-init/init_collections.py
```

Expected output:
```
✓ Connected to Chroma client
✓ Chroma is ready!
✓ Created collection: user_profiles
✓ Created collection: content_library
✓ Created collection: market_segments
✓ Created collection: competitor_content
```

### Step 7: Verify PostgreSQL Database

**Check databases exist:**
```cmd
docker exec postgres psql -U n8n -c "\l"
```

**Check marketing database tables:**
```cmd
docker exec postgres psql -U n8n -d marketing -c "\dt"
```

You should see tables like: users, campaigns, content_drafts, media_assets, etc.

### Step 8: Test Services

**Using PowerShell (recommended):**
```powershell
.\test-services.ps1
```

**Or test manually:**

1. **Test Ollama:**
```cmd
curl http://localhost:11434/api/tags
```

2. **Test PostgreSQL:**
```cmd
docker exec postgres pg_isready -U n8n
```

3. **Test Redis:**
```cmd
docker exec redis redis-cli ping
```

4. **Test Chroma:**
```cmd
curl http://localhost:8000/api/v1/heartbeat
```

### Step 9: Access Services in Browser

Open your browser and test these URLs:

- **Streamlit Dashboard**: http://localhost:8501
- **n8n Workflows**: http://localhost:5678 (if using local n8n)
- **Matomo Analytics**: http://localhost:8081
- **Database Admin**: http://localhost:8082
- **SearXNG Search**: http://localhost:8080

## External n8n Configuration (Your Setup)

Since you use n8n on Cloud Run (https://n8n-de5xsqtqma-wl.a.run.app/), follow these steps:

### Step 1: Update .env File

Open `.env` in notepad:
```cmd
notepad .env
```

**Comment out local n8n settings** by adding `#` at the start of each line:
```bash
# N8N_USER=admin
# N8N_PASSWORD=change_this_n8n_password
# N8N_HOST=localhost
```

**Add your external n8n configuration:**
```bash
N8N_EXTERNAL_URL=https://n8n-de5xsqtqma-wl.a.run.app
N8N_WEBHOOK_URL=https://n8n-de5xsqtqma-wl.a.run.app/webhook
N8N_API_KEY=your_api_key_from_n8n_cloud
```

Save the file.

### Step 2: Modify docker-compose.yml

Open `docker-compose.yml`:
```cmd
notepad docker-compose.yml
```

**Find the n8n service section** (around line 3-35) and comment it out by adding `#` at the start of each line, or completely remove it.

Save the file.

### Step 3: Restart Services

```cmd
docker-compose down
docker-compose up -d
```

### Step 4: Configure n8n Cloud Instance

In your Cloud Run n8n instance:

1. Go to Settings → Credentials
2. Add PostgreSQL credential:
   - **Host**: Your public IP or use ngrok/CloudFlare tunnel
   - **Database**: `marketing`
   - **User**: `n8n`
   - **Password**: (from your .env file)
   - **Port**: `5432`

**Note:** For security, consider using Cloud SQL Proxy or setting up a VPN instead of exposing PostgreSQL directly.

## Common Windows-Specific Issues

### Issue 1: "docker-compose: command not found"

**Solution:** Docker Desktop not running or not in PATH.

1. Open Docker Desktop application
2. Wait for it to fully start
3. Try again

**Or use the full path:**
```cmd
"C:\Program Files\Docker\Docker\resources\bin\docker-compose.exe" up -d
```

### Issue 2: "Access Denied" or Permission Errors

**Solution:** Run Command Prompt or PowerShell as Administrator.

1. Right-click Command Prompt or PowerShell
2. Select "Run as Administrator"
3. Navigate back to project directory
4. Run commands again

### Issue 3: Line Ending Issues with .env File

**Solution:** Make sure .env uses Windows line endings (CRLF).

**Using PowerShell:**
```powershell
(Get-Content .env.example) | Set-Content -Encoding ASCII .env
```

### Issue 4: curl Command Not Found

**Solution A:** Use PowerShell instead of Command Prompt (PowerShell has curl alias).

**Solution B:** Install curl for Windows:
- Download: https://curl.se/windows/

**Solution C:** Use Invoke-WebRequest in PowerShell:
```powershell
Invoke-WebRequest -Uri http://localhost:11434/api/tags
```

### Issue 5: Ports Already in Use

**Check what's using a port (run as Administrator):**
```cmd
netstat -ano | findstr :5432
netstat -ano | findstr :5678
netstat -ano | findstr :8501
```

**Kill process using port (replace PID with actual process ID):**
```cmd
taskkill /PID <process_id> /F
```

### Issue 6: Docker Containers Keep Restarting

**Check logs:**
```cmd
docker-compose logs postgres
docker-compose logs ollama
docker-compose logs langchain_service
```

**Common causes:**
- Insufficient memory (increase in Docker Desktop settings)
- Missing .env file variables
- Port conflicts

**Restart all services:**
```cmd
docker-compose down
docker-compose up -d
```

### Issue 7: Path with Spaces

If your directory path has spaces (like "B2B Marketing System"), always use quotes:

```cmd
cd "C:\Users\jacob\B2B Marketing System"
docker-compose up -d
```

### Issue 8: WSL2 Not Enabled

Docker Desktop requires WSL2 on Windows 10/11.

**Enable WSL2:**

1. Open PowerShell as Administrator:
```powershell
wsl --install
```

2. Restart computer

3. Open Docker Desktop and verify it's using WSL2 backend (Settings → General)

## Windows-Specific Commands Reference

### File Operations

| Linux/Mac Command | Windows Command Prompt | Windows PowerShell |
|-------------------|------------------------|-------------------|
| `cp file1 file2` | `copy file1 file2` | `Copy-Item file1 file2` |
| `mv file1 file2` | `move file1 file2` | `Move-Item file1 file2` |
| `rm file` | `del file` | `Remove-Item file` |
| `cat file` | `type file` | `Get-Content file` |
| `ls` | `dir` | `Get-ChildItem` or `ls` |
| `pwd` | `cd` | `Get-Location` or `pwd` |
| `nano file` | `notepad file` | `notepad file` |
| `chmod +x file` | N/A (not needed) | N/A (not needed) |

### Docker Commands (Same on all platforms)

```cmd
docker-compose up -d          # Start all services
docker-compose down           # Stop all services
docker-compose ps             # List running services
docker-compose logs [service] # View logs
docker exec [container] [cmd] # Execute command in container
```

## Verification Checklist

After setup, verify everything works:

- [ ] Docker Desktop is running
- [ ] All containers are "Up" (`docker-compose ps`)
- [ ] Ollama models downloaded (`docker exec ollama ollama list`)
- [ ] Chroma collections created
- [ ] Can access http://localhost:8501 (Dashboard)
- [ ] Can access http://localhost:8082 (Adminer)
- [ ] Can access your external n8n instance
- [ ] PostgreSQL has 3 databases (marketing, n8n, matomo)

## Next Steps

1. **Configure API Keys**
   - Edit `.env` file
   - Add OpenAI API key for image generation
   - Add Runway API key for video generation
   - Add LinkedIn/WordPress credentials for publishing

2. **Import n8n Workflows**
   - Go to your Cloud Run n8n instance
   - Import workflows from `n8n-workflows/` folder
   - Configure credentials

3. **Test End-to-End**
   - Create a test campaign in Dashboard
   - Generate content
   - Review and approve
   - Publish to channels

## Getting Help

If you still encounter errors:

1. **Copy the exact error message**
2. **Note which command failed**
3. **Check the logs:**
   ```cmd
   docker-compose logs [service-name]
   ```
4. **Verify Docker Desktop is running**
5. **Check system requirements are met**

Common log locations:
- Docker Desktop logs: Docker Desktop → Troubleshoot → View logs
- Container logs: `docker-compose logs -f [service]`
- Windows Event Viewer: eventvwr.msc

## PowerShell Setup Script (Advanced)

Save this as `setup.ps1` and run in PowerShell:

```powershell
# Check Docker is running
if (!(Get-Process "Docker Desktop" -ErrorAction SilentlyContinue)) {
    Write-Host "Starting Docker Desktop..."
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    Start-Sleep -Seconds 10
}

# Create .env file
Copy-Item .env.example .env
Write-Host "Created .env file - please edit it with your settings"
notepad .env
Read-Host "Press Enter after editing .env"

# Start services
docker-compose up -d
Write-Host "Waiting for services to start..."
Start-Sleep -Seconds 120

# Pull models
Write-Host "Pulling Ollama models (this may take 10-20 minutes)..."
docker exec ollama ollama pull llama3.1:8b

# Initialize Chroma
docker exec langchain_service python /app/chroma-init/init_collections.py

Write-Host "`n✓ Setup complete!"
Write-Host "Access dashboard at: http://localhost:8501"
```

---

**Need more help?** Please share:
1. The exact command you ran
2. The complete error message
3. What step you're on

I can then provide specific fixes for your situation.
