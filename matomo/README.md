# Matomo Analytics

Matomo is an open-source web analytics platform used to track engagement metrics for published content.

## Features

- **Privacy-focused**: GDPR compliant, self-hosted
- **Real-time tracking**: Live visitor analytics
- **Custom events**: Track specific user actions
- **API access**: Programmatic data retrieval
- **No data limits**: Unlike Google Analytics free tier
- **Custom dashboards**: Visualize metrics

## Quick Start

### 1. Start Matomo

```bash
# Start all services
docker-compose up -d

# Check Matomo is running
docker-compose ps matomo
curl http://localhost:8081
```

### 2. Initial Setup

1. Open http://localhost:8081 in browser
2. Follow installation wizard:
   - Database: Select "PostgreSQL"
   - Database host: `postgres`
   - Database name: `matomo`
   - Database user: `${POSTGRES_USER}` (from .env)
   - Database password: `${POSTGRES_PASSWORD}` (from .env)
3. Create admin user
4. Add first website:
   - Name: "Marketing Content Tracking"
   - URL: Your published content domain
   - Timezone: America/New_York (or your timezone)

### 3. Get Tracking Code

After setup, Matomo provides JavaScript tracking code:

```html
<!-- Matomo -->
<script>
  var _paq = window._paq = window._paq || [];
  _paq.push(['trackPageView']);
  _paq.push(['enableLinkTracking']);
  (function() {
    var u="http://localhost:8081/";
    _paq.push(['setTrackerUrl', u+'matomo.php']);
    _paq.push(['setSiteId', '1']);
    var d=document, g=d.createElement('script'), s=d.getElementsByTagName('script')[0];
    g.async=true; g.src=u+'matomo.js'; s.parentNode.insertBefore(g,s);
  })();
</script>
<!-- End Matomo Code -->
```

## API Usage

### Authentication

Get API token from Matomo dashboard:
1. Go to Administration → Personal → Security
2. Create new token
3. Add to `.env`:
   ```bash
   MATOMO_AUTH_TOKEN=your_token_here
   MATOMO_SITE_ID=1
   ```

### Python Integration

```python
import requests
from typing import Dict, List
import os

class MatomoTracker:
    def __init__(
        self,
        base_url: str = "http://matomo:80",
        site_id: int = 1,
        auth_token: str = None
    ):
        self.base_url = base_url.rstrip('/')
        self.site_id = site_id
        self.auth_token = auth_token or os.getenv("MATOMO_AUTH_TOKEN")

    def get_visits(self, period: str = "day", date: str = "today") -> Dict:
        """
        Get visit statistics

        Args:
            period: day, week, month, year
            date: today, yesterday, YYYY-MM-DD, or date range
        """
        params = {
            "module": "API",
            "method": "VisitsSummary.get",
            "idSite": self.site_id,
            "period": period,
            "date": date,
            "format": "JSON",
            "token_auth": self.auth_token
        }

        response = requests.get(f"{self.base_url}/", params=params)
        return response.json()

    def get_top_pages(
        self,
        period: str = "day",
        date: str = "today",
        limit: int = 10
    ) -> List[Dict]:
        """Get most visited pages"""
        params = {
            "module": "API",
            "method": "Actions.getPageUrls",
            "idSite": self.site_id,
            "period": period,
            "date": date,
            "format": "JSON",
            "filter_limit": limit,
            "token_auth": self.auth_token
        }

        response = requests.get(f"{self.base_url}/", params=params)
        return response.json()

    def track_event(
        self,
        category: str,
        action: str,
        name: str = None,
        value: float = None,
        url: str = None
    ) -> bool:
        """
        Track custom event

        Args:
            category: Event category (e.g., 'Content', 'Publishing')
            action: Event action (e.g., 'Published', 'Shared')
            name: Optional event name
            value: Optional numeric value
            url: URL where event occurred
        """
        params = {
            "idsite": self.site_id,
            "rec": 1,
            "e_c": category,
            "e_a": action,
            "token_auth": self.auth_token
        }

        if name:
            params["e_n"] = name
        if value:
            params["e_v"] = value
        if url:
            params["url"] = url

        response = requests.get(
            f"{self.base_url}/matomo.php",
            params=params
        )

        return response.status_code == 200 or response.status_code == 204

    def get_conversions(
        self,
        period: str = "day",
        date: str = "today"
    ) -> Dict:
        """Get goal conversions"""
        params = {
            "module": "API",
            "method": "Goals.get",
            "idSite": self.site_id,
            "period": period,
            "date": date,
            "format": "JSON",
            "token_auth": self.auth_token
        }

        response = requests.get(f"{self.base_url}/", params=params)
        return response.json()

# Usage example
tracker = MatomoTracker(
    base_url="http://localhost:8081",
    site_id=1,
    auth_token="your_token"
)

# Get today's visits
visits = tracker.get_visits()
print(f"Visits today: {visits.get('nb_visits')}")

# Get top pages
top_pages = tracker.get_top_pages(limit=5)
for page in top_pages:
    print(f"{page['label']}: {page['nb_hits']} views")

# Track custom event
tracker.track_event(
    category="Content",
    action="Published",
    name="Blog Post: AI in Marketing",
    url="https://yourblog.com/ai-marketing"
)
```

## Tracking Setup

### For Published Content

When publishing content, inject Matomo tracking:

**Blog Posts (WordPress):**
```php
<?php
// Add to theme's header.php
$matomo_site_id = 1;
$matomo_url = "http://your-matomo-instance.com/";
?>
<script type="text/javascript">
  var _paq = window._paq = window._paq || [];
  _paq.push(['trackPageView']);
  _paq.push(['enableLinkTracking']);
  (function() {
    var u="<?php echo $matomo_url; ?>";
    _paq.push(['setTrackerUrl', u+'matomo.php']);
    _paq.push(['setSiteId', '<?php echo $matomo_site_id; ?>']);
    var d=document, g=d.createElement('script'), s=d.getElementsByTagName('script')[0];
    g.async=true; g.src=u+'matomo.js'; s.parentNode.insertBefore(g,s);
  })();
</script>
```

**Email Newsletters:**
```html
<!-- Add 1x1 tracking pixel -->
<img src="http://your-matomo-instance.com/matomo.php?idsite=1&rec=1&action_name=Newsletter+Opened"
     style="border:0" alt="" />
```

### Custom Event Tracking

Track specific actions:

```javascript
// Track button click
document.getElementById('cta-button').addEventListener('click', function() {
  _paq.push(['trackEvent', 'CTA', 'Click', 'Sign Up Button']);
});

// Track download
document.getElementById('download-whitepaper').addEventListener('click', function() {
  _paq.push(['trackEvent', 'Downloads', 'Whitepaper', 'Marketing Guide 2024']);
});

// Track video play
video.addEventListener('play', function() {
  _paq.push(['trackEvent', 'Video', 'Play', video.title]);
});

// Track scroll depth
window.addEventListener('scroll', function() {
  var scrollPercentage = (window.scrollY / document.body.scrollHeight) * 100;
  if (scrollPercentage > 75) {
    _paq.push(['trackEvent', 'Scroll', '75% Depth']);
  }
});
```

## Goals & Conversions

### Set Up Goals

1. Go to: Administration → Websites → Goals
2. Add new goal:
   - **Name**: Newsletter Signup
   - **Description**: User signs up for newsletter
   - **Match Against**: URL contains `/thank-you`
   - **Revenue**: Optional (e.g., $5 per signup)

### Track Conversions Programmatically

```python
# When goal is achieved (e.g., form submission)
params = {
    "idsite": 1,
    "rec": 1,
    "idgoal": 1,  # Goal ID from Matomo
    "revenue": 5.00,  # Optional
    "token_auth": "your_token"
}

requests.get("http://localhost:8081/matomo.php", params=params)
```

## Integration with n8n

Create n8n workflow to sync engagement data:

```javascript
// n8n HTTP Request node to Matomo API
{
  "method": "GET",
  "url": "http://matomo/",
  "qs": {
    "module": "API",
    "method": "Actions.getPageUrls",
    "idSite": "1",
    "period": "day",
    "date": "today",
    "format": "JSON",
    "token_auth": "{{$env.MATOMO_AUTH_TOKEN}}"
  }
}

// Process response and update PostgreSQL
const metrics = $json.body;
for (const page of metrics) {
  // Insert into engagement_metrics table
  await $db.query(`
    INSERT INTO engagement_metrics (content_id, views, clicks, engagement_rate)
    VALUES ($1, $2, $3, $4)
    ON CONFLICT (content_id) DO UPDATE SET
      views = $2,
      clicks = $3,
      engagement_rate = $4,
      tracked_at = CURRENT_TIMESTAMP
  `, [contentId, page.nb_hits, page.nb_visits, page.bounce_rate]);
}
```

## Webhook Integration

Set up real-time webhooks in Matomo:

1. Install HTTP API plugin
2. Configure webhook:
   ```
   URL: http://n8n:5678/webhook/matomo-event
   Events: PageView, Download, OutboundLink, Goal
   ```

3. n8n Webhook node to receive:
   ```javascript
   // Process incoming Matomo event
   const event = $json.body;

   if (event.type === 'goal') {
     // Update conversion metrics
     await updateConversionMetrics(event);
   } else if (event.type === 'pageview') {
     // Update view metrics
     await updateViewMetrics(event);
   }
   ```

## Reports & Dashboards

### Daily Summary Report

```python
def generate_daily_report(tracker: MatomoTracker) -> Dict:
    """Generate daily analytics report"""
    # Get visits
    visits = tracker.get_visits(period="day", date="today")

    # Get top pages
    top_pages = tracker.get_top_pages(limit=10)

    # Get conversions
    conversions = tracker.get_conversions(period="day", date="today")

    return {
        "date": "today",
        "total_visits": visits.get("nb_visits", 0),
        "unique_visitors": visits.get("nb_uniq_visitors", 0),
        "page_views": visits.get("nb_actions", 0),
        "bounce_rate": visits.get("bounce_rate", "0%"),
        "avg_time_on_site": visits.get("avg_time_on_site", 0),
        "top_pages": [
            {
                "url": page["label"],
                "views": page["nb_hits"],
                "unique_views": page["nb_visits"]
            }
            for page in top_pages[:5]
        ],
        "conversions": conversions.get("nb_conversions", 0)
    }

# Generate and send report
report = generate_daily_report(tracker)
send_email_report(report)
```

### Custom Dashboard

Create custom Matomo dashboard:
1. Go to: Dashboard → Manage Dashboards
2. Add widgets:
   - Visitor Log
   - Page URLs
   - Referrers
   - Goal Conversions
   - Custom Events
3. Share dashboard URL with team

## Data Privacy (GDPR)

### Configuration

```php
// config/config.ini.php
[General]
anonymize_ip = 1
force_ssl = 1
enable_do_not_track = 1

[PrivacyManager]
anonymizeUserId = 1
anonymizeOrderId = 1
doNotTrack = 1
```

### User Rights

Matomo supports GDPR user rights:
- **Right to access**: Export user data
- **Right to erasure**: Delete user data
- **Right to object**: Honor Do Not Track

### Cookie Consent

```html
<!-- Require consent before tracking -->
<script>
  var _paq = window._paq = window._paq || [];
  _paq.push(['requireConsent']);
  _paq.push(['trackPageView']);
  _paq.push(['enableLinkTracking']);
  // ... rest of tracking code

  // When user accepts cookies
  function acceptCookies() {
    _paq.push(['setConsentGiven']);
  }

  // When user declines
  function declineCookies() {
    _paq.push(['forgetConsentGiven']);
  }
</script>
```

## Troubleshooting

### No Data Appearing

```bash
# Check Matomo logs
docker logs matomo

# Verify database connection
docker exec matomo cat /var/www/html/config/config.ini.php

# Test tracking
curl "http://localhost:8081/matomo.php?idsite=1&rec=1&action_name=Test"
```

### Slow Performance

```bash
# Check database size
docker exec postgres psql -U marketing_user -d matomo -c "SELECT pg_size_pretty(pg_database_size('matomo'));"

# Archive old data
docker exec matomo php /var/www/html/console core:archive
```

### Connection Issues

```bash
# Restart Matomo
docker-compose restart matomo

# Check network
docker exec matomo ping postgres

# Verify environment variables
docker exec matomo env | grep MATOMO
```

## Best Practices

1. **Archive Old Data**: Run archiving daily to keep performance high
   ```bash
   docker exec matomo php /var/www/html/console core:archive
   ```

2. **Set Data Retention**: Delete old data after X months
   - Go to: Administration → Privacy → Anonymize Data
   - Set retention: 24 months recommended

3. **Monitor Performance**: Check database size monthly

4. **Backup Database**: Regular PostgreSQL backups include Matomo data

5. **Use Segments**: Create user segments for better insights
   - New visitors vs returning
   - By traffic source
   - By conversion status

## Resources

- [Matomo Documentation](https://matomo.org/docs/)
- [API Reference](https://developer.matomo.org/api-reference)
- [Tracking API](https://developer.matomo.org/api-reference/tracking-api)
- [GDPR Compliance](https://matomo.org/gdpr/)
