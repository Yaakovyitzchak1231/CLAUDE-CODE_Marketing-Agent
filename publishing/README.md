# Publishing Package

Multi-channel content publishing for LinkedIn, WordPress, and Email.

## Overview

This package provides Python clients for publishing marketing content across three major channels:

- **LinkedIn API**: Post text, images, videos, and articles
- **WordPress XML-RPC**: Create blog posts with media
- **SMTP Email**: Send newsletters with HTML templates

## Installation

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file with the following credentials:

```bash
# LinkedIn API
LINKEDIN_ACCESS_TOKEN=your_linkedin_oauth_token

# WordPress
WORDPRESS_URL=https://yourblog.com
WORDPRESS_USERNAME=your_username
WORDPRESS_PASSWORD=your_app_password

# SMTP Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your.email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_NAME=Your Company
```

## Usage

### LinkedIn Publisher

#### Basic Text Post

```python
from publishing import LinkedInPublisher

publisher = LinkedInPublisher()

result = publisher.create_text_post(
    text="Excited to share our latest insights on B2B marketing! #Marketing #AI",
    visibility="PUBLIC"
)

print(f"Posted to: {result['url']}")
```

#### Post with Image

```python
result = publisher.create_post_with_media(
    text="Check out our latest infographic!",
    media_urls=["https://example.com/infographic.png"],
    media_type="image"
)
```

#### Post with Multiple Images

```python
result = publisher.create_post_with_media(
    text="Product showcase: Our latest features",
    media_urls=[
        "https://example.com/image1.png",
        "https://example.com/image2.png",
        "https://example.com/image3.png"
    ],
    media_type="image"
)
```

#### Post with Video

```python
result = publisher.create_post_with_media(
    text="Watch our product demo video!",
    media_urls=["https://example.com/demo.mp4"],
    media_type="video"
)
```

#### Get Post Analytics

```python
analytics = publisher.get_post_analytics(post_id="urn:li:ugcPost:12345")

print(f"Likes: {analytics['likes']}")
print(f"Comments: {analytics['comments']}")
print(f"Shares: {analytics['shares']}")
print(f"Impressions: {analytics['impressions']}")
```

### WordPress Publisher

#### Basic Blog Post

```python
from publishing import WordPressPublisher

publisher = WordPressPublisher()

result = publisher.create_post(
    title="How to Automate B2B Marketing",
    content="<p>Marketing automation has become essential...</p>",
    status="publish",
    categories=["Marketing", "Automation"],
    tags=["B2B", "AI", "Tools"]
)

print(f"Published at: {result['url']}")
```

#### Blog Post with Featured Image

```python
result = publisher.create_post_with_media(
    title="Top 10 Marketing Trends for 2024",
    content="<h2>1. AI-Powered Content</h2><p>Artificial intelligence...</p>",
    featured_image_url="https://example.com/header.png",
    status="publish",
    categories=["Trends"],
    tags=["2024", "Marketing"]
)
```

#### Blog Post with Multiple Images

```python
result = publisher.create_post_with_media(
    title="Product Gallery",
    content="<p>Here are our latest products...</p>",
    featured_image_url="https://example.com/header.png",
    media_urls=[
        "https://example.com/product1.png",
        "https://example.com/product2.png"
    ],
    status="publish"
)
```

#### Update Existing Post

```python
result = publisher.update_post(
    post_id=123,
    title="Updated: Marketing Automation Guide",
    content="<p>Updated content here...</p>",
    status="publish"
)
```

#### Get Recent Posts

```python
posts = publisher.get_recent_posts(count=10)

for post in posts:
    print(f"{post['title']} - {post['url']}")
```

### Email Publisher

#### Send Newsletter

```python
from publishing import EmailPublisher

publisher = EmailPublisher()

result = publisher.send_newsletter(
    to_emails=["subscriber@example.com"],
    subject="Your Weekly Marketing Insights",
    content="""
        <h1>Welcome to This Week's Newsletter</h1>
        <p>Here are the top marketing trends...</p>
        <h2>Trend #1: AI Content Generation</h2>
        <p>Artificial intelligence is transforming...</p>
    """,
    header_image_url="https://example.com/banner.png",
    footer_text="© 2024 Your Company. All rights reserved.",
    unsubscribe_link="https://example.com/unsubscribe"
)

print(f"Sent to {result['recipients']} recipients")
```

#### Send Custom HTML Email

```python
result = publisher.send_email(
    to_emails=["recipient@example.com"],
    subject="Product Launch Announcement",
    html_content="""
        <html>
            <body>
                <h1>We're Launching Something Amazing!</h1>
                <p>Get ready for our new product...</p>
            </body>
        </html>
    """,
    cc_emails=["team@example.com"],
    reply_to="support@example.com"
)
```

#### Send Email with Attachments

```python
result = publisher.send_email(
    to_emails=["client@example.com"],
    subject="Monthly Report - December 2024",
    html_content="<p>Please find attached your monthly report.</p>",
    attachments=[
        {
            "filename": "report.pdf",
            "url": "https://example.com/reports/december.pdf"
        }
    ]
)
```

#### Send Bulk Personalized Emails

```python
recipients = [
    {"email": "john@example.com", "name": "John", "company": "Acme Corp"},
    {"email": "jane@example.com", "name": "Jane", "company": "TechCo"},
]

html_template = """
    <h1>Hello {{name}}!</h1>
    <p>Thank you for being a valued customer at {{company}}.</p>
"""

result = publisher.send_bulk_emails(
    recipients=recipients,
    subject="Personalized Newsletter for {{name}}",
    html_template=html_template,
    batch_size=50
)

print(f"Sent: {result['sent']}, Failed: {result['failed']}")
```

## Integration with n8n Workflows

### LinkedIn Publishing Node

```json
{
  "parameters": {
    "url": "http://langchain-service:8001/publish/linkedin",
    "method": "POST",
    "bodyParametersJson": {
      "content": "{{ $json.content }}",
      "media_urls": "{{ $json.media_urls }}",
      "media_type": "{{ $json.media_type || 'image' }}",
      "hashtags": "{{ $json.hashtags }}"
    }
  }
}
```

### WordPress Publishing Node

```json
{
  "parameters": {
    "url": "http://langchain-service:8001/publish/wordpress",
    "method": "POST",
    "bodyParametersJson": {
      "title": "{{ $json.title }}",
      "content": "{{ $json.content }}",
      "featured_image_url": "{{ $json.featured_image_url }}",
      "categories": "{{ $json.categories }}",
      "tags": "{{ $json.tags }}"
    }
  }
}
```

### Email Publishing Node

```json
{
  "parameters": {
    "url": "http://langchain-service:8001/publish/email",
    "method": "POST",
    "bodyParametersJson": {
      "to_emails": "{{ $json.to_emails }}",
      "subject": "{{ $json.subject }}",
      "content": "{{ $json.content }}",
      "header_image_url": "{{ $json.header_image_url }}"
    }
  }
}
```

## API Reference

### LinkedInPublisher

#### Methods

- `create_text_post(text, visibility="PUBLIC")` - Create text-only post
- `create_post_with_media(text, media_urls, media_type, visibility="PUBLIC")` - Post with images/video
- `create_article(title, content, thumbnail_url)` - Create LinkedIn article
- `upload_image(image_url)` - Upload image and get asset URN
- `upload_video(video_url, title, description)` - Upload video and get asset URN
- `get_post_analytics(post_id)` - Get engagement metrics
- `format_post_content(content, hashtags)` - Format text with hashtags

#### Limits

- Text posts: 3,000 characters
- Images per post: 9 max
- Videos per post: 1 max
- Image size: 10 MB max
- Video size: 200 MB max

### WordPressPublisher

#### Methods

- `create_post(title, content, status, categories, tags, featured_image_id, excerpt)` - Create blog post
- `create_post_with_media(title, content, media_urls, featured_image_url, status, categories, tags)` - Post with media
- `update_post(post_id, title, content, status)` - Update existing post
- `delete_post(post_id)` - Delete post
- `get_post(post_id)` - Get post details
- `get_recent_posts(count)` - List recent posts
- `upload_media(media_url, filename, media_type)` - Upload media file
- `test_connection()` - Test XML-RPC connection

#### Post Statuses

- `publish` - Published and visible
- `draft` - Draft (not visible)
- `private` - Private (only visible to logged-in users)
- `pending` - Pending review

### EmailPublisher

#### Methods

- `send_email(to_emails, subject, html_content, plain_content, cc_emails, bcc_emails, reply_to, attachments, inline_images)` - Send email
- `send_newsletter(to_emails, subject, content, header_image_url, footer_text, unsubscribe_link, preheader)` - Send newsletter
- `send_bulk_emails(recipients, subject, html_template, personalization_fields, batch_size)` - Bulk send

#### Email Limits

- Gmail: 500 recipients/day (free), 2,000/day (Google Workspace)
- Attachment size: 25 MB max (Gmail)
- Best practice: Batch size of 50-100 for bulk sends

## Error Handling

All publishers raise exceptions on failure. Wrap calls in try/except:

```python
try:
    result = publisher.create_text_post(text="Hello LinkedIn!")
    print(f"Success: {result['url']}")
except Exception as e:
    print(f"Failed to publish: {str(e)}")
```

## Testing

### Test LinkedIn Connection

```python
publisher = LinkedInPublisher()
user_info = publisher.get_user_info()
print(f"Connected as: {user_info}")
```

### Test WordPress Connection

```python
publisher = WordPressPublisher()
is_connected = publisher.test_connection()
print(f"WordPress connected: {is_connected}")
```

### Test Email (Send Test Email)

```python
publisher = EmailPublisher()
result = publisher.send_email(
    to_emails=["your.email@example.com"],
    subject="Test Email",
    html_content="<p>This is a test email.</p>"
)
print(f"Test email sent: {result['success']}")
```

## Security Best Practices

1. **Never commit credentials** - Use `.env` files and `.gitignore`
2. **Use OAuth for LinkedIn** - Generate access tokens via LinkedIn Developer Portal
3. **Use application passwords for WordPress** - Don't use main account password
4. **Use app passwords for Gmail** - Enable 2FA and create app-specific passwords
5. **Rotate credentials regularly** - Update tokens/passwords every 90 days
6. **Validate email addresses** - Use email validation before sending bulk emails
7. **Implement rate limiting** - Respect API rate limits (LinkedIn: 100 req/day free tier)

## Troubleshooting

### LinkedIn Issues

**Error: "Invalid access token"**
- Solution: Regenerate OAuth token via LinkedIn Developer Portal

**Error: "Daily API limit exceeded"**
- Solution: Upgrade to LinkedIn Marketing API or reduce posting frequency

### WordPress Issues

**Error: "XML-RPC not enabled"**
- Solution: Enable XML-RPC in WordPress settings or via plugin

**Error: "Incorrect username or password"**
- Solution: Use WordPress application password, not main password

### Email Issues

**Error: "Authentication failed"**
- Solution: Enable "Less secure app access" or use app-specific password

**Error: "Daily sending quota exceeded"**
- Solution: Reduce batch size or upgrade to business email service

**Error: "Email rejected as spam"**
- Solution: Add proper SPF/DKIM records, warm up IP, use authenticated domain

## License

MIT License - See LICENSE file for details
