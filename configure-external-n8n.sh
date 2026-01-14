#!/bin/bash
# Configure External n8n Setup Script
# For Linux/Mac
# Configures the system to use external n8n instance instead of local Docker n8n

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
EXTERNAL_N8N_URL="https://n8n-de5xsqtqma-wl.a.run.app"
ENV_FILE=".env"
DOCKER_COMPOSE_FILE="docker-compose.yml"
BACKUP_SUFFIX=".backup-$(date +%Y%m%d-%H%M%S)"

echo -e "${CYAN}================================================${NC}"
echo -e "${CYAN}External n8n Configuration Script${NC}"
echo -e "${CYAN}================================================${NC}"
echo ""

# Function to create backup
backup_file() {
    local file=$1
    local backup="${file}${BACKUP_SUFFIX}"
    cp "$file" "$backup"
    echo -e "${GREEN}✓ Created backup: $backup${NC}"
}

# Function to check if file exists
check_file_exists() {
    local file=$1
    if [ ! -f "$file" ]; then
        echo -e "${RED}✗ Error: $file not found!${NC}"
        echo -e "${YELLOW}  Make sure you're running this script from the project root directory.${NC}"
        exit 1
    fi
}

# Step 1: Check prerequisites
echo -e "${YELLOW}Step 1: Checking prerequisites...${NC}"
check_file_exists "$ENV_FILE"
check_file_exists "$DOCKER_COMPOSE_FILE"
echo -e "${GREEN}✓ All required files found${NC}"
echo ""

# Step 2: Backup files
echo -e "${YELLOW}Step 2: Creating backups...${NC}"
backup_file "$ENV_FILE"
backup_file "$DOCKER_COMPOSE_FILE"
echo ""

# Step 3: Configure docker-compose.yml
echo -e "${YELLOW}Step 3: Configuring docker-compose.yml...${NC}"

if grep -q "^[[:space:]]*#[[:space:]]*n8n:" "$DOCKER_COMPOSE_FILE"; then
    echo -e "${YELLOW}⚠ n8n service appears to be already commented out${NC}"
else
    # Comment out n8n service section using sed
    sed -i.tmp '/^[[:space:]]*n8n:/,/^[[:space:]]*[a-z_]*:/ {
        /^[[:space:]]*n8n:/i\  # COMMENTED OUT - USING EXTERNAL N8N
        /^[[:space:]]*n8n:/s/^/  # /
        /^[[:space:]]*[a-z_]*:/!s/^/  # /
    }' "$DOCKER_COMPOSE_FILE"

    rm -f "${DOCKER_COMPOSE_FILE}.tmp"
    echo -e "${GREEN}✓ Commented out local n8n service in docker-compose.yml${NC}"
fi
echo ""

# Step 4: Configure .env file
echo -e "${YELLOW}Step 4: Configuring .env file...${NC}"

if grep -q "N8N_EXTERNAL_URL" "$ENV_FILE"; then
    echo -e "${YELLOW}⚠ External n8n configuration already exists in .env${NC}"
    echo -e "${YELLOW}  Current configuration:${NC}"
    grep -E "N8N_EXTERNAL_URL|N8N_WEBHOOK_URL|N8N_API_KEY" "$ENV_FILE" | sed "s/^/${CYAN}    /" && echo -e "${NC}"
else
    # Create temporary file with modifications
    awk '
        /N8N CONFIGURATION/ { in_n8n=1; print; next }
        /^# =====/ && in_n8n {
            print ""
            print "# External n8n (Cloud Run) - CONFIGURED BY SCRIPT"
            print "N8N_EXTERNAL_URL='$EXTERNAL_N8N_URL'"
            print "N8N_WEBHOOK_URL='$EXTERNAL_N8N_URL'/webhook"
            print "N8N_API_KEY=your_n8n_api_key_here"
            print ""
            in_n8n=0
            print
            next
        }
        in_n8n && /^(N8N_USER|N8N_PASSWORD|N8N_HOST|N8N_API_KEY|TIMEZONE)=/ {
            print "# " $0
            next
        }
        { print }
    ' "$ENV_FILE" > "${ENV_FILE}.tmp"

    mv "${ENV_FILE}.tmp" "$ENV_FILE"
    echo -e "${GREEN}✓ Updated .env file with external n8n configuration${NC}"
fi
echo ""

# Step 5: Get API Key from user
echo -e "${YELLOW}Step 5: n8n API Key Configuration${NC}"
echo ""
echo "To complete the setup, you need to get your n8n API key:"
echo -e "  ${CYAN}1. Go to: $EXTERNAL_N8N_URL${NC}"
echo -e "  ${CYAN}2. Login to your n8n instance${NC}"
echo -e "  ${CYAN}3. Go to: Settings → API${NC}"
echo -e "  ${CYAN}4. Click 'Create API Key'${NC}"
echo -e "  ${CYAN}5. Copy the generated API key${NC}"
echo ""

read -p "Enter your n8n API key (or press Enter to skip): " api_key

if [ -n "$api_key" ]; then
    # Update API key in .env
    sed -i.tmp "s/N8N_API_KEY=your_n8n_api_key_here/N8N_API_KEY=$api_key/" "$ENV_FILE"
    rm -f "${ENV_FILE}.tmp"
    echo -e "${GREEN}✓ Updated n8n API key in .env${NC}"
else
    echo -e "${YELLOW}⚠ Skipped API key configuration${NC}"
    echo -e "${YELLOW}  You can manually edit .env and update N8N_API_KEY later${NC}"
fi
echo ""

# Step 6: Update streamlit_dashboard configuration
echo -e "${YELLOW}Step 6: Updating service configurations...${NC}"

sed -i.tmp "s|N8N_API_URL=http://n8n:5678/api/v1|N8N_API_URL=${EXTERNAL_N8N_URL}/api/v1|g" "$DOCKER_COMPOSE_FILE"
rm -f "${DOCKER_COMPOSE_FILE}.tmp"

echo -e "${GREEN}✓ Updated streamlit dashboard to use external n8n API${NC}"
echo ""

# Step 7: Summary
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Configuration Complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Changes made:"
echo -e "  ${GREEN}✓ Commented out local n8n service in docker-compose.yml${NC}"
echo -e "  ${GREEN}✓ Updated .env with external n8n configuration${NC}"
echo -e "  ${GREEN}✓ Updated streamlit to use external n8n API${NC}"
echo -e "  ${GREEN}✓ Backups created with suffix: $BACKUP_SUFFIX${NC}"
echo ""

echo -e "${CYAN}External n8n URL: $EXTERNAL_N8N_URL${NC}"
echo ""

# Step 8: Next steps
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Review the .env file and ensure N8N_API_KEY is set:"
echo -e "     ${CYAN}nano .env${NC}"
echo ""
echo "  2. Restart Docker services:"
echo -e "     ${CYAN}docker-compose down${NC}"
echo -e "     ${CYAN}docker-compose up -d${NC}"
echo ""
echo "  3. Verify services are running:"
echo -e "     ${CYAN}docker-compose ps${NC}"
echo ""
echo "  4. Configure n8n workflows:"
echo -e "     ${CYAN}- Go to: $EXTERNAL_N8N_URL${NC}"
echo -e "     ${CYAN}- Import workflows from n8n-workflows/ folder${NC}"
echo -e "     ${CYAN}- Update PostgreSQL credentials to connect to local DB${NC}"
echo ""

echo -e "${YELLOW}Note: Your local PostgreSQL is not exposed to the internet.${NC}"
echo -e "${YELLOW}      For n8n to access it, you'll need to:${NC}"
echo -e "${YELLOW}      - Use CloudFlare Tunnel, ngrok, or similar${NC}"
echo -e "${YELLOW}      - OR migrate to Cloud SQL for shared access${NC}"
echo ""

echo -e "${GREEN}Configuration script completed successfully! 🎉${NC}"
