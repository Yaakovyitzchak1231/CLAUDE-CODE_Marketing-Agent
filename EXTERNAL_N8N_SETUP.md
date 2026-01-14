# External n8n Configuration Guide

This guide is specifically for users who have n8n hosted externally (Cloud Run, Railway, Render, etc.) instead of running it locally in Docker.

## Your Setup

**External n8n URL**: `https://n8n-de5xsqtqma-wl.a.run.app`

## Automated Configuration (Recommended)

We've created automated scripts to configure your system for external n8n.

### For Windows Users

**Run in PowerShell:**

```powershell
.\configure-external-n8n.ps1
```

**Or run in Command Prompt:**

```cmd
powershell -ExecutionPolicy Bypass -File configure-external-n8n.ps1
```

### For Linux/Mac Users

**Run in Terminal:**

```bash
chmod +x configure-external-n8n.sh
./configure-external-n8n.sh
```

### What the Script Does

1. ✅ Creates backup copies of `.env` and `docker-compose.yml`
2. ✅ Comments out the local n8n service in `docker-compose.yml`
3. ✅ Updates `.env` with external n8n configuration
4. ✅ Prompts you for your n8n API key
5. ✅ Updates service configurations to use external n8n

## Manual Configuration (Alternative)

If you prefer to configure manually:

### Step 1: Edit `.env`

Open `.env` and comment out local n8n settings:

```bash
# ==================== N8N CONFIGURATION ====================
# Local Docker n8n (default) - COMMENTED OUT
# N8N_USER=admin
# N8N_PASSWORD=change_this_n8n_password
# N8N_HOST=localhost
# TIMEZONE=America/New_York

# External n8n (Cloud Run)
N8N_EXTERNAL_URL=https://n8n-de5xsqtqma-wl.a.run.app
N8N_WEBHOOK_URL=https://n8n-de5xsqtqma-wl.a.run.app/webhook
N8N_API_KEY=your_actual_api_key_here
```

### Step 2: Edit `docker-compose.yml`

Find the n8n service section (lines 5-34) and comment it all out:

```yaml
services:
  # ==================== ORCHESTRATION ====================
  # COMMENTED OUT - USING EXTERNAL N8N
  # n8n:
  #   image: n8nio/n8n:latest
  #   container_name: n8n
  #   ...
  # (comment out entire n8n service block)

  # ==================== LLM SERVICES ====================
  ollama:
    image: ollama/ollama:latest
```

### Step 3: Update Streamlit Configuration

In `docker-compose.yml`, find the `streamlit_dashboard` service and update:

```yaml
streamlit_dashboard:
  environment:
    - N8N_API_URL=https://n8n-de5xsqtqma-wl.a.run.app/api/v1
```

### Step 4: Get n8n API Key

1. Go to https://n8n-de5xsqtqma-wl.a.run.app
2. Login to your n8n instance
3. Navigate to: **Settings → API**
4. Click **"Create API Key"**
5. Copy the generated key
6. Update `N8N_API_KEY` in `.env` file

### Step 5: Restart Services

```bash
docker-compose down
docker-compose up -d
```

## Database Access for External n8n

Your local PostgreSQL database runs on your machine and is not accessible from the internet. For your Cloud Run n8n to connect to it, you have two options:

### Option 1: CloudFlare Tunnel (Recommended)

**Free and secure way to expose PostgreSQL:**

1. Install CloudFlare Tunnel:
   ```bash
   # Windows (via Chocolatey)
   choco install cloudflared

   # Or download from: https://github.com/cloudflare/cloudflared/releases
   ```

2. Create tunnel for PostgreSQL:
   ```bash
   cloudflared tunnel --url tcp://localhost:5432
   ```

3. Use the provided URL in your n8n PostgreSQL credentials

### Option 2: ngrok

**Quick tunneling solution:**

1. Install ngrok: https://ngrok.com/download

2. Create tunnel:
   ```bash
   ngrok tcp 5432
   ```

3. Use the provided address in n8n PostgreSQL credentials

### Option 3: Cloud SQL Migration (Production)

For production use, consider:
- Migrating PostgreSQL to Google Cloud SQL
- Your Cloud Run n8n can connect directly
- More reliable and secure than tunneling

## Configuring n8n Workflows

After setting up external n8n:

1. **Access your n8n instance**: https://n8n-de5xsqtqma-wl.a.run.app

2. **Import workflows**:
   - Go to Workflows → Import
   - Upload workflows from `n8n-workflows/` folder
   - Import all JSON files

3. **Configure PostgreSQL credentials**:
   - Go to Credentials → Add Credential
   - Select "PostgreSQL"
   - Enter connection details:
     - Host: (your CloudFlare/ngrok URL or public IP)
     - Database: `marketing`
     - User: `n8n`
     - Password: (from your `.env` file)
     - Port: `5432`

4. **Update workflow credentials**:
   - Open each imported workflow
   - Select the PostgreSQL credential you created
   - Save the workflow

5. **Update webhook URLs**:
   - Any webhooks in workflows should use:
     - `https://n8n-de5xsqtqma-wl.a.run.app/webhook/...`

## Verification Checklist

After configuration, verify:

- [ ] Local Docker services running (except n8n):
  ```bash
  docker-compose ps
  ```
  Should show: postgres, redis, ollama, chroma, langchain_service, streamlit_dashboard, etc.

- [ ] Can access external n8n:
  ```bash
  # Open in browser
  https://n8n-de5xsqtqma-wl.a.run.app
  ```

- [ ] Dashboard can connect to external n8n API:
  - Go to http://localhost:8501
  - Check for n8n integration status

- [ ] PostgreSQL accessible from n8n (via tunnel or Cloud SQL)

## Troubleshooting

### Issue: "Cannot connect to n8n API"

**Check:**
1. n8n API key is correct in `.env`
2. External n8n URL is accessible
3. Firewall/network allows outbound HTTPS

### Issue: "n8n cannot connect to PostgreSQL"

**Check:**
1. CloudFlare Tunnel or ngrok is running
2. PostgreSQL credentials in n8n are correct
3. Database `marketing` exists
4. User `n8n` has proper permissions

**Test connection locally:**
```bash
docker exec postgres psql -U n8n -d marketing -c "SELECT 1;"
```

### Issue: Webhooks not working

**Check:**
1. Webhook URLs use your external n8n domain
2. n8n workflows are activated
3. Webhook paths are correct

### Issue: Services can't reach each other

After commenting out n8n, some services may reference it. Check:

```bash
docker-compose logs langchain_service
docker-compose logs streamlit_dashboard
```

Look for connection errors to n8n.

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│   Your Local Machine (Docker)          │
│                                         │
│  ┌──────────┐  ┌──────────┐           │
│  │PostgreSQL│  │  Ollama  │           │
│  └────┬─────┘  └──────────┘           │
│       │                                │
│  ┌────▼─────────┐  ┌──────────┐      │
│  │  LangChain   │  │  Chroma  │      │
│  │   Service    │  │ VectorDB │      │
│  └────┬─────────┘  └──────────┘      │
│       │                                │
│  ┌────▼─────────┐                     │
│  │  Streamlit   │                     │
│  │  Dashboard   │                     │
│  └──────────────┘                     │
└───────────┬─────────────────────────┬─┘
            │                         │
            │                         │
        ┌───▼──────────┐      ┌───────▼────────┐
        │   Internet   │      │ CloudFlare     │
        │              │      │ Tunnel/ngrok   │
        └───┬──────────┘      └───────┬────────┘
            │                         │
    ┌───────▼─────────────────────────▼─────┐
    │   Google Cloud Run                    │
    │                                        │
    │  ┌──────────────────────────────┐    │
    │  │          n8n                  │    │
    │  │ n8n-de5xsqtqma-wl.a.run.app  │    │
    │  └──────────────────────────────┘    │
    └────────────────────────────────────────┘
```

## Benefits of External n8n

✅ **Pros:**
- Always online (24/7 availability)
- Auto-scaling on Cloud Run
- No local resource usage for n8n
- Easier to share workflows with team
- Managed updates and backups

⚠️ **Cons:**
- Requires tunnel/proxy for local database access
- Additional network latency
- Depends on internet connection
- May have Cloud Run cold start delays

## Next Steps

1. **Run the configuration script** (recommended)
2. **Get your n8n API key** from Cloud Run instance
3. **Set up database tunnel** (CloudFlare/ngrok)
4. **Import workflows** to external n8n
5. **Test end-to-end** workflow execution

## Support

If you encounter issues:

1. Check logs: `docker-compose logs -f`
2. Verify n8n is accessible: `curl https://n8n-de5xsqtqma-wl.a.run.app`
3. Test database connection from n8n
4. Review this guide's troubleshooting section

---

**Last Updated**: 2026-01-14
**Your n8n URL**: https://n8n-de5xsqtqma-wl.a.run.app
