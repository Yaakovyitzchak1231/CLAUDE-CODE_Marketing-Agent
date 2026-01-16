# Brand Voice Training - E2E Test Suite

This directory contains end-to-end tests for the Brand Voice Training feature (Task 011).

## Quick Start

### Prerequisites

Ensure all services are running:
```bash
cd /c/Users/jacob/marketing-agent
docker compose up -d postgres langchain-service streamlit-dashboard
```

Wait for services to be healthy (~30 seconds), then run tests.

### Running Tests

**Option 1: Python Test (Recommended)**
```bash
python3 test_brand_voice_e2e.py
```

**Option 2: Bash Test**
```bash
./test_brand_voice_e2e.sh
```

## What Gets Tested

The E2E test verifies the complete brand voice training workflow:

1. **Upload & Train** (Step 1)
   - Uploads 10 example brand content pieces
   - Trains brand voice profile via API
   - Verifies profile created with unique ID

2. **Verify Metrics** (Step 2)
   - Checks calculated_profile field exists
   - Verifies tone_analysis metrics
   - Verifies readability_metrics
   - Verifies vocabulary_patterns

3. **Create Campaign** (Step 3)
   - Creates test campaign
   - Links campaign to brand voice profile
   - Verifies association in database

4. **Generate Content** (Step 4)
   - Generates content using profile
   - Calculates consistency score
   - Verifies score >= 80%

5. **Export/Import** (Step 5)
   - Exports profile to JSON
   - Re-imports with new ID
   - Verifies data integrity

6. **Cleanup** (Step 6)
   - Removes test profiles
   - Removes test campaigns
   - Cleans up temporary files

## Test Scripts

### test_brand_voice_e2e.py

**Python test script with robust error handling**

Features:
- Detailed error messages
- Colored output
- Progress indicators
- Automatic cleanup on failure
- Saves export files for inspection

Requirements:
- Python 3.7+
- requests library: `pip install requests`

### test_brand_voice_e2e.sh

**Bash test script using curl**

Features:
- No external dependencies (except curl)
- Works in any Unix-like environment
- Simple and readable
- Color-coded output

Requirements:
- bash
- curl
- grep, sed

## Test Documentation

See `E2E_TEST_DOCUMENTATION.md` for:
- Detailed test strategy
- Manual testing steps
- API endpoint documentation
- Troubleshooting guide
- Success criteria checklist

## Expected Output

Both scripts produce similar output:

```
========================================
Brand Voice Training E2E Test
========================================

Step 0: Checking services are running...
✓ Services are running

Step 1: Training brand voice profile with 10 example pieces...
✓ Brand voice profile created with ID: abc123...

Step 2: Verifying brand voice metrics were calculated...
✓ All brand voice metrics calculated successfully

Step 3: Creating campaign with trained profile assigned...
✓ Campaign created with ID: def456...
✓ Campaign successfully linked to brand voice profile

Step 4: Generating content with brand voice profile...
✓ Content generated successfully
Brand Voice Consistency Score: 100%
✓ Content matches brand voice (score: 100% >= 80%)

Step 5: Exporting brand voice profile...
✓ Profile exported successfully

Step 5b: Re-importing brand voice profile...
✓ Profile re-imported successfully with new ID: ghi789...
✓ Imported profile has all required data

Step 6: Cleaning up test data...
✓ Deleted imported profile
✓ Deleted original profile
✓ Deleted test campaign

========================================
All E2E Tests Passed Successfully!
========================================
```

## Troubleshooting

### "Cannot connect to LangChain service"

Services not running. Start them:
```bash
cd /c/Users/jacob/marketing-agent
docker compose up -d postgres langchain-service
```

### "Profile missing calculated_profile field"

The brand voice analyzer may not be working. Check:
```bash
docker compose logs langchain-service | grep -i "brand"
```

### "Consistency score < 80%"

Generated content doesn't match brand voice. This could mean:
- Content agent isn't using the profile correctly
- Training examples aren't representative
- LLM isn't following profile guidelines

Check content_agent.py integration.

### "Failed to create campaign"

Campaigns API may have issues. Test directly:
```bash
curl -X POST http://localhost:8001/campaigns \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "status": "active"}'
```

## Files

- `test_brand_voice_e2e.py` - Python test script
- `test_brand_voice_e2e.sh` - Bash test script
- `E2E_TEST_DOCUMENTATION.md` - Detailed test documentation
- `TEST_README.md` - This file

## CI/CD Integration

To integrate into CI pipeline:

```yaml
test-brand-voice:
  script:
    - docker compose up -d postgres langchain-service
    - sleep 30  # Wait for services
    - python3 test_brand_voice_e2e.py
  artifacts:
    when: on_failure
    paths:
      - brand_voice_export_*.json
```

## Manual Testing

For manual testing via UI, see the detailed steps in `E2E_TEST_DOCUMENTATION.md`.

Quick manual test:
1. Open http://localhost:8501/brand_voice_training
2. Upload 10 text examples
3. Click "Train Profile"
4. Go to Campaigns page
5. Create campaign with profile
6. Generate content
7. Verify consistency

## Support

For issues or questions:
1. Check `E2E_TEST_DOCUMENTATION.md` troubleshooting section
2. Review service logs: `docker compose logs langchain-service`
3. Verify database schema: `docker compose exec postgres psql -U marketing_user -d marketing -c "\d brand_voice_profiles"`

## Success Criteria

Tests pass when:
- ✓ All 6 steps complete without errors
- ✓ Profile metrics calculated correctly
- ✓ Campaign links to profile
- ✓ Content consistency >= 80%
- ✓ Export/import preserves data
- ✓ Cleanup completes successfully
