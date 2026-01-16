#!/bin/bash
# End-to-End Test for Brand Voice Training Feature
# This script tests the complete workflow from upload to content generation

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test configuration
LANGCHAIN_URL="http://localhost:8001"
POSTGRES_CONTAINER="marketing-agent-postgres-1"
DB_USER="marketing_user"
DB_NAME="marketing"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Brand Voice Training E2E Test${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Function to print test step
print_step() {
    echo -e "${YELLOW}Step $1:${NC} $2"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

# Check if services are running
print_step "0" "Checking services are running..."
if ! curl -s "$LANGCHAIN_URL/health" > /dev/null; then
    print_error "LangChain service is not running at $LANGCHAIN_URL"
fi
print_success "Services are running"
echo ""

# Step 1: Upload 10 example brand content pieces
print_step "1" "Training brand voice profile with 10 example pieces..."

# Create example content that represents a brand voice
# Using a tech-savvy, friendly, professional tone
EXAMPLE_CONTENT='[
  "We believe technology should empower people, not replace them. Our AI tools augment human creativity.",
  "Here'\''s how we'\''re revolutionizing marketing: smart automation meets human insight. The result? Better campaigns, faster.",
  "Data-driven decisions are great, but intuition matters too. We help you balance both for optimal results.",
  "Marketing doesn'\''t have to be complicated. Our platform simplifies campaign management while delivering powerful analytics.",
  "Your brand voice is unique. That'\''s why we built tools that learn from your content and amplify what makes you special.",
  "Innovation isn'\''t just about new features. It'\''s about solving real problems in ways that feel natural and intuitive.",
  "We'\''re on a mission to make enterprise-grade marketing tools accessible to teams of all sizes. No complexity, just results.",
  "Behind every great campaign is a team that understands their audience. Our AI helps you connect more authentically.",
  "Time is your most valuable resource. We built our platform to give you more of it by automating the tedious stuff.",
  "Great content tells a story. Our tools help you craft narratives that resonate with your audience and drive action."
]'

# Create training request
TRAIN_RESPONSE=$(curl -s -X POST "$LANGCHAIN_URL/brand-voice/train" \
  -H "Content-Type: application/json" \
  -d "{
    \"profile_name\": \"Test Brand Voice E2E\",
    \"example_content\": $EXAMPLE_CONTENT,
    \"campaign_id\": null
  }")

# Extract profile ID from response
PROFILE_ID=$(echo "$TRAIN_RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$PROFILE_ID" ]; then
    print_error "Failed to create brand voice profile. Response: $TRAIN_RESPONSE"
fi

print_success "Brand voice profile created with ID: $PROFILE_ID"
echo ""

# Step 2: Verify metrics calculated
print_step "2" "Verifying brand voice metrics were calculated..."

# Get profile details
PROFILE_DETAILS=$(curl -s "$LANGCHAIN_URL/brand-voice/profiles/$PROFILE_ID")

# Check if calculated_profile exists and has expected fields
if ! echo "$PROFILE_DETAILS" | grep -q '"calculated_profile"'; then
    print_error "Profile does not contain calculated_profile field"
fi

# Check for key metrics
for metric in "tone_analysis" "readability_metrics" "vocabulary_patterns"; do
    if ! echo "$PROFILE_DETAILS" | grep -q "\"$metric\""; then
        print_error "Missing metric: $metric"
    fi
done

print_success "All brand voice metrics calculated successfully"
echo ""

# Display some metrics
echo "Profile Metrics:"
echo "$PROFILE_DETAILS" | grep -o '"tone_analysis":[^}]*}' | head -1
echo ""

# Step 3: Create campaign with trained profile assigned
print_step "3" "Creating campaign with trained profile assigned..."

# Create a test campaign
CAMPAIGN_RESPONSE=$(curl -s -X POST "$LANGCHAIN_URL/campaigns" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"E2E Test Campaign with Brand Voice\",
    \"status\": \"active\",
    \"target_audience\": \"B2B marketers\",
    \"brand_voice_profile_id\": \"$PROFILE_ID\"
  }")

CAMPAIGN_ID=$(echo "$CAMPAIGN_RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$CAMPAIGN_ID" ]; then
    print_error "Failed to create campaign. Response: $CAMPAIGN_RESPONSE"
fi

print_success "Campaign created with ID: $CAMPAIGN_ID"

# Verify the profile is associated with the campaign
CAMPAIGN_DETAILS=$(curl -s "$LANGCHAIN_URL/campaigns/$CAMPAIGN_ID")
if ! echo "$CAMPAIGN_DETAILS" | grep -q "\"brand_voice_profile_id\":\"$PROFILE_ID\""; then
    print_error "Campaign is not properly linked to brand voice profile"
fi

print_success "Campaign successfully linked to brand voice profile"
echo ""

# Step 4: Generate content and verify it matches brand voice
print_step "4" "Generating content with brand voice profile..."

CONTENT_RESPONSE=$(curl -s -X POST "$LANGCHAIN_URL/agents/content" \
  -H "Content-Type: application/json" \
  -d "{
    \"content_type\": \"linkedin_post\",
    \"topic\": \"AI-powered marketing automation\",
    \"target_audience\": \"B2B marketers\",
    \"brand_voice_profile_id\": \"$PROFILE_ID\"
  }")

if ! echo "$CONTENT_RESPONSE" | grep -q '"content"'; then
    print_error "Failed to generate content. Response: $CONTENT_RESPONSE"
fi

GENERATED_CONTENT=$(echo "$CONTENT_RESPONSE" | grep -o '"content":"[^"]*"' | cut -d'"' -f4)

print_success "Content generated successfully"
echo ""
echo "Generated Content Preview:"
echo "$GENERATED_CONTENT" | head -c 200
echo "..."
echo ""

# Check brand voice consistency
# The content should reflect similar characteristics to the training examples
# Check for key indicators from our training examples:
# - Professional but friendly tone
# - Focus on empowerment and simplicity
# - Use of "we" and inclusive language
# - Mentions of AI/technology positively

CONSISTENCY_INDICATORS=0

if echo "$GENERATED_CONTENT" | grep -qi "empower\|augment\|simplif\|innovate"; then
    CONSISTENCY_INDICATORS=$((CONSISTENCY_INDICATORS + 25))
fi

if echo "$GENERATED_CONTENT" | grep -qi "we\|our\|us"; then
    CONSISTENCY_INDICATORS=$((CONSISTENCY_INDICATORS + 25))
fi

if echo "$GENERATED_CONTENT" | grep -qi "AI\|automat\|data"; then
    CONSISTENCY_INDICATORS=$((CONSISTENCY_INDICATORS + 25))
fi

if echo "$GENERATED_CONTENT" | grep -qi "team\|audience\|people"; then
    CONSISTENCY_INDICATORS=$((CONSISTENCY_INDICATORS + 25))
fi

echo "Brand Voice Consistency Score: $CONSISTENCY_INDICATORS%"

if [ $CONSISTENCY_INDICATORS -ge 80 ]; then
    print_success "Content matches brand voice (score: $CONSISTENCY_INDICATORS% >= 80%)"
else
    print_error "Content does not match brand voice well enough (score: $CONSISTENCY_INDICATORS% < 80%)"
fi
echo ""

# Step 5: Export profile and re-import successfully
print_step "5" "Exporting brand voice profile..."

EXPORT_RESPONSE=$(curl -s "$LANGCHAIN_URL/brand-voice/profiles/$PROFILE_ID/export")

if ! echo "$EXPORT_RESPONSE" | grep -q '"profile_name"'; then
    print_error "Failed to export profile. Response: $EXPORT_RESPONSE"
fi

# Save export to temp file
EXPORT_FILE="/tmp/brand_voice_export_$PROFILE_ID.json"
echo "$EXPORT_RESPONSE" > "$EXPORT_FILE"

print_success "Profile exported successfully to $EXPORT_FILE"
echo ""

print_step "5b" "Re-importing brand voice profile..."

# Modify the profile name for import to avoid conflicts
IMPORT_DATA=$(echo "$EXPORT_RESPONSE" | sed 's/"profile_name":"Test Brand Voice E2E"/"profile_name":"Test Brand Voice E2E (Imported)"/')

IMPORT_RESPONSE=$(curl -s -X POST "$LANGCHAIN_URL/brand-voice/import" \
  -H "Content-Type: application/json" \
  -d "$IMPORT_DATA")

IMPORTED_PROFILE_ID=$(echo "$IMPORT_RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$IMPORTED_PROFILE_ID" ]; then
    print_error "Failed to import profile. Response: $IMPORT_RESPONSE"
fi

print_success "Profile re-imported successfully with new ID: $IMPORTED_PROFILE_ID"
echo ""

# Verify imported profile has same characteristics
IMPORTED_DETAILS=$(curl -s "$LANGCHAIN_URL/brand-voice/profiles/$IMPORTED_PROFILE_ID")

if ! echo "$IMPORTED_DETAILS" | grep -q '"calculated_profile"'; then
    print_error "Imported profile missing calculated_profile"
fi

print_success "Imported profile has all required data"
echo ""

# Step 6: Cleanup test data
print_step "6" "Cleaning up test data..."

# Delete imported profile
curl -s -X DELETE "$LANGCHAIN_URL/brand-voice/profiles/$IMPORTED_PROFILE_ID" > /dev/null
print_success "Deleted imported profile"

# Delete original profile
curl -s -X DELETE "$LANGCHAIN_URL/brand-voice/profiles/$PROFILE_ID" > /dev/null
print_success "Deleted original profile"

# Delete test campaign
curl -s -X DELETE "$LANGCHAIN_URL/campaigns/$CAMPAIGN_ID" > /dev/null
print_success "Deleted test campaign"

# Remove export file
rm -f "$EXPORT_FILE"
print_success "Removed export file"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}All E2E Tests Passed Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Summary:"
echo "  ✓ Uploaded 10 example brand content pieces"
echo "  ✓ Trained brand voice profile with calculated metrics"
echo "  ✓ Created campaign with trained profile assigned"
echo "  ✓ Generated content matching brand voice (consistency >= 80%)"
echo "  ✓ Exported and re-imported profile successfully"
echo "  ✓ Cleaned up test data"
echo ""
