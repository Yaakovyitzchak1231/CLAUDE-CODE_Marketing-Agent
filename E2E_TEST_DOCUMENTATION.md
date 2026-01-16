# Brand Voice Training - End-to-End Test Documentation

## Overview

This document describes the end-to-end testing strategy for the Brand Voice Training feature. The feature enables users to train the AI on their specific brand voice and use it to generate consistent, on-brand content.

## Test Objectives

Verify the complete workflow:
1. ✓ Upload example brand content pieces via API
2. ✓ Train brand voice profile and verify metrics calculated
3. ✓ Create campaign with trained profile assigned
4. ✓ Generate content and verify it matches brand voice (consistency score > 80%)
5. ✓ Export profile and re-import successfully

## Test Environment

### Required Services
- **PostgreSQL Database**: Port 5432
- **LangChain Service**: Port 8001
- **Streamlit Dashboard**: Port 8501 (optional for UI testing)

### Prerequisites
```bash
cd /c/Users/jacob/marketing-agent
docker compose up -d postgres langchain-service streamlit-dashboard
```

## Automated Testing

### Option 1: Python Test Script (Recommended)

The Python script provides robust error handling and detailed output:

```bash
# Make script executable
chmod +x test_brand_voice_e2e.py

# Run test
python3 test_brand_voice_e2e.py
```

**Requirements:**
- Python 3.7+
- requests library: `pip install requests`

### Option 2: Bash Test Script

The bash script uses curl for API testing:

```bash
# Make script executable
chmod +x test_brand_voice_e2e.sh

# Run test
./test_brand_voice_e2e.sh
```

**Requirements:**
- bash
- curl
- grep, sed (standard Unix tools)

## Manual Testing Steps

### Step 1: Upload and Train Brand Voice Profile

**API Endpoint:** `POST /brand-voice/train`

**Request:**
```bash
curl -X POST http://localhost:8001/brand-voice/train \
  -H "Content-Type: application/json" \
  -d '{
    "profile_name": "Manual Test Profile",
    "example_content": [
      "We believe technology should empower people, not replace them.",
      "Here'\''s how we'\''re revolutionizing marketing: smart automation meets human insight.",
      "Data-driven decisions are great, but intuition matters too.",
      "Marketing doesn'\''t have to be complicated.",
      "Your brand voice is unique.",
      "Innovation isn'\''t just about new features.",
      "We'\''re on a mission to make enterprise-grade marketing accessible.",
      "Behind every great campaign is a team that understands their audience.",
      "Time is your most valuable resource.",
      "Great content tells a story."
    ]
  }'
```

**Expected Response:**
```json
{
  "id": "uuid-here",
  "profile_name": "Manual Test Profile",
  "calculated_profile": {
    "tone_analysis": {...},
    "readability_metrics": {...},
    "vocabulary_patterns": {...}
  },
  "created_at": "timestamp"
}
```

**Verification:**
- ✓ Response status: 200
- ✓ Profile ID returned
- ✓ `calculated_profile` field present
- ✓ Contains `tone_analysis`, `readability_metrics`, `vocabulary_patterns`

### Step 2: Verify Metrics Calculated

**API Endpoint:** `GET /brand-voice/profiles/{profile_id}`

**Request:**
```bash
curl http://localhost:8001/brand-voice/profiles/{profile_id}
```

**Expected Metrics:**

1. **Tone Analysis**
   - Sentiment scores (positive, neutral, negative)
   - Formality level
   - Subjectivity vs objectivity

2. **Readability Metrics**
   - Flesch Reading Ease score
   - Average sentence length
   - Average word length
   - Syllables per word

3. **Vocabulary Patterns**
   - Common words
   - Key phrases
   - Industry-specific terminology

**Verification:**
- ✓ All metrics present in response
- ✓ Values are reasonable (e.g., reading ease 0-100)
- ✓ Vocabulary patterns reflect input content

### Step 3: Create Campaign with Profile

**API Endpoint:** `POST /campaigns`

**Request:**
```bash
curl -X POST http://localhost:8001/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Campaign with Brand Voice",
    "status": "active",
    "target_audience": "B2B marketers",
    "brand_voice_profile_id": "profile-uuid-here"
  }'
```

**Verification:**
- ✓ Campaign created successfully
- ✓ `brand_voice_profile_id` stored in database
- ✓ GET /campaigns/{id} returns linked profile ID

### Step 4: Generate Content with Brand Voice

**API Endpoint:** `POST /agents/content`

**Request:**
```bash
curl -X POST http://localhost:8001/agents/content \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "linkedin_post",
    "topic": "AI-powered marketing automation",
    "target_audience": "B2B marketers",
    "brand_voice_profile_id": "profile-uuid-here"
  }'
```

**Expected Response:**
```json
{
  "content": "Generated content here...",
  "metadata": {...}
}
```

**Consistency Verification:**

Check generated content for brand voice indicators:

| Indicator | Weight | Check |
|-----------|--------|-------|
| Empowerment language | 25% | Contains: empower, augment, simplify, innovate |
| Inclusive language | 25% | Contains: we, our, us |
| Tech focus | 25% | Contains: AI, automation, data, technology |
| People focus | 25% | Contains: team, audience, people, human |

**Acceptance Criteria:**
- ✓ Content generated successfully
- ✓ Consistency score >= 80%
- ✓ Content reflects training examples' tone and style

### Step 5: Export and Import Profile

**Export:**
```bash
curl http://localhost:8001/brand-voice/profiles/{profile_id}/export > profile_export.json
```

**Verification:**
- ✓ JSON file contains `profile_name`
- ✓ JSON file contains `example_content`
- ✓ JSON file contains `calculated_profile`

**Import:**
```bash
curl -X POST http://localhost:8001/brand-voice/import \
  -H "Content-Type: application/json" \
  -d @profile_export.json
```

**Verification:**
- ✓ New profile created with unique ID
- ✓ All data preserved (name, examples, metrics)
- ✓ GET request to new profile returns correct data

## UI Testing (Optional)

### Brand Voice Training Page

1. Navigate to http://localhost:8501/brand_voice_training
2. Verify page renders without errors
3. Test upload interface:
   - Upload 10 text examples
   - Click "Train Profile"
   - Verify success message
4. View trained profiles list
5. Check profile details display

### Campaign Creation

1. Navigate to http://localhost:8501/campaigns
2. Create new campaign
3. Verify brand voice profile selector appears
4. Select a trained profile
5. Verify profile details shown
6. Save campaign
7. Verify profile linked in campaign details

## Database Verification

### Check Schema

```sql
-- Verify brand_voice_profiles table
SELECT * FROM brand_voice_profiles LIMIT 1;

-- Verify campaigns link
SELECT id, name, brand_voice_profile_id FROM campaigns WHERE brand_voice_profile_id IS NOT NULL;
```

**Expected:**
- ✓ `brand_voice_profiles` table exists
- ✓ Columns: id, campaign_id, profile_name, example_content, calculated_profile, created_at
- ✓ `campaigns` table has `brand_voice_profile_id` column
- ✓ Foreign key relationship established

## Success Criteria

All of the following must pass:

- [x] Services running and accessible
- [x] 10 example pieces can be uploaded
- [x] Brand voice profile trains successfully
- [x] All metrics calculated (tone, readability, vocabulary)
- [x] Campaign can be linked to profile
- [x] Content generation uses profile
- [x] Generated content consistency score >= 80%
- [x] Profile can be exported as JSON
- [x] Exported profile can be re-imported
- [x] All CRUD operations work correctly
- [x] Database schema correct
- [x] No errors in service logs

## Troubleshooting

### Services Not Running

```bash
cd /c/Users/jacob/marketing-agent
docker compose ps
docker compose up -d postgres langchain-service
```

### API Endpoints Not Found

```bash
# Restart langchain service
docker compose restart langchain-service

# Check logs
docker compose logs langchain-service | tail -50
```

### Database Connection Issues

```bash
# Check postgres is running
docker compose ps postgres

# Verify database exists
docker compose exec postgres psql -U marketing_user -d marketing -c "\l"

# Check tables
docker compose exec postgres psql -U marketing_user -d marketing -c "\dt"
```

### Low Consistency Score

If generated content doesn't match brand voice:
1. Check training examples are diverse and representative
2. Verify calculated_profile has correct metrics
3. Review content_agent.py profile injection logic
4. Check LLM temperature settings
5. Try with more training examples (15-20)

## Test Results Template

```
E2E Test Results - Brand Voice Training
Date: YYYY-MM-DD
Tester: [Name]

[ ] Step 1: Upload and Train - PASS/FAIL
    Profile ID: _______
    Notes: _______

[ ] Step 2: Verify Metrics - PASS/FAIL
    Tone Score: _______
    Readability: _______
    Notes: _______

[ ] Step 3: Create Campaign - PASS/FAIL
    Campaign ID: _______
    Notes: _______

[ ] Step 4: Generate Content - PASS/FAIL
    Consistency Score: _______%
    Notes: _______

[ ] Step 5: Export/Import - PASS/FAIL
    Import ID: _______
    Notes: _______

Overall Result: PASS/FAIL
```

## Cleanup

After testing, clean up test data:

```bash
# Delete test profiles
curl -X DELETE http://localhost:8001/brand-voice/profiles/{profile_id}

# Delete test campaigns
curl -X DELETE http://localhost:8001/campaigns/{campaign_id}
```

## Notes

- Test scripts automatically clean up created data
- Manual testing requires manual cleanup
- Keep test profile names clearly labeled (e.g., "TEST - ...")
- Document any failures with service logs
