# Video Tutorial Scripts

## Overview

This document provides scripts for creating video tutorials demonstrating the B2B Marketing Automation Platform. Each tutorial includes a step-by-step walkthrough, expected outcomes, and talking points.

## Tutorial 1: System Setup and First Campaign (10 minutes)

### Objective
Walk through initial setup, Docker deployment, and creating the first marketing campaign.

### Prerequisites
- Docker Desktop installed
- Git repository cloned
- 16GB+ RAM available

### Script

**[00:00-00:30] Introduction**
```
"Welcome to this tutorial on setting up the B2B Marketing Automation Platform.
In this video, we'll deploy the entire system using Docker, create our first campaign,
and generate our first piece of marketing content. Let's get started!"
```

**[00:30-02:00] Environment Setup**
```
"First, let's set up our environment variables. I'm copying the .env.example file
to .env and filling in our credentials."

[Screen: Show .env.example being copied]

"For LinkedIn, I'm adding my OAuth access token from the LinkedIn Developer Portal.
For WordPress, I'm entering my blog URL and application password.
And for email, I'm using Gmail SMTP credentials with an app-specific password."

[Screen: Show editing .env file with credentials redacted]
```

**[02:00-04:00] Starting Services**
```
"Now let's start all the services using Docker Compose.
This will spin up 13 different containers including PostgreSQL, n8n, Ollama,
and our LangChain service."

[Screen: Terminal showing docker-compose up -d]

docker-compose up -d

"Let's verify everything is running properly."

[Screen: Terminal showing docker-compose ps]

docker-compose ps

"Perfect! All services are up. Notice that Ollama is pulling the Llama 3 model
- this might take a few minutes the first time."
```

**[04:00-05:00] Accessing the Dashboard**
```
"Let's open the Streamlit dashboard at localhost:8501."

[Screen: Browser showing Streamlit dashboard]

"This is the main interface where we'll manage campaigns, review content,
and track analytics. Let's start with the onboarding wizard."

[Screen: Click "Onboarding" in sidebar]
```

**[05:00-07:00] User Onboarding**
```
"The onboarding wizard collects information about your business,
target audience, and brand guidelines. Let's fill this out."

[Screen: Step through onboarding wizard]

Step 1 - Basic Info:
  Email: demo@example.com
  Company: Acme Marketing Solutions
  Role: Marketing Director

Step 2 - Business Info:
  Industry: SaaS
  Company Size: 50-100 employees
  Website: https://acme-marketing.com

Step 3 - Target Audience:
  "B2B marketing managers at tech companies looking to automate
   their content creation and improve campaign efficiency"

Step 4 - Brand Guidelines:
  Voice: Professional but approachable
  Tone: Informative and helpful
  Colors: #1E3A8A (Blue), #FFFFFF (White)
  Keywords: automation, AI, efficiency, ROI

[Screen: Submit onboarding form]

"Great! The system is now analyzing our website and setting up our first campaign."
```

**[07:00-08:30] Generating First Content**
```
"Now let's generate our first marketing content. I'll click 'Generate Content'
and specify a topic."

[Screen: Content generation form]

Topic: "How AI is Transforming B2B Marketing in 2024"
Content Type: LinkedIn Post
Target Word Count: 250

[Screen: Click Generate]

"The system is now:
1. Researching the topic using our search engine
2. Analyzing our brand guidelines
3. Generating content with Llama 3
4. Optimizing for SEO
5. Checking grammar

This takes about 10-15 seconds."

[Screen: Show loading indicator, then content appears]
```

**[08:30-09:30] Reviewing and Approving**
```
"Here's our generated content. The system has already:
- Matched our brand voice
- Included relevant hashtags
- Optimized for LinkedIn's 3000 character limit
- Calculated an SEO score of 85

Let's review it. Looks good! I'll click 'Approve & Publish'."

[Screen: Review interface, click Approve]

"The content is now being published to LinkedIn. We can see the post
going live in real-time."

[Screen: Show publishing status, then LinkedIn post URL]
```

**[09:30-10:00] Wrap-up**
```
"And that's it! In just 10 minutes, we've:
- Deployed the entire platform
- Set up our first campaign
- Generated and published our first content

In the next tutorial, we'll explore image generation, video creation,
and advanced analytics. Thanks for watching!"
```

---

## Tutorial 2: Content Generation Workflow (8 minutes)

### Objective
Deep dive into the content generation process, including research, writing, and SEO optimization.

### Script

**[00:00-00:30] Introduction**
```
"In this tutorial, we'll explore the content generation workflow in detail.
You'll learn how the AI researches topics, generates content, and optimizes
for different platforms."
```

**[00:30-02:00] Research Pipeline**
```
"Before generating content, the system runs competitive research.
Let's trigger that manually."

[Screen: Navigate to Research tab]

"I'm entering our competitors and topics to research."

Competitors:
- hubspot.com
- marketo.com

Topics:
- Marketing automation trends
- AI content generation

[Screen: Click "Start Research"]

"The system is now:
1. Scraping competitor websites
2. Analyzing their messaging
3. Extracting key themes
4. Performing sentiment analysis

Let's see the results."

[Screen: Show research insights table]

"Great! We can see HubSpot focuses heavily on inbound methodology,
while Marketo emphasizes enterprise solutions. The system has
identified 'AI-powered personalization' as an emerging trend."
```

**[02:00-04:00] Content Generation with Research Context**
```
"Now when we generate content, it will use these insights."

[Screen: Content generation form]

Topic: "Marketing Automation ROI: What to Expect"
Content Type: Blog Post
Use Research: Yes

[Screen: Click Generate]

"Notice how the generated content incorporates insights from our research:
- Mentions industry trends we discovered
- References competitor positioning
- Uses data points from our analysis

This makes the content more authoritative and relevant."

[Screen: Show generated blog post with highlighted research references]
```

**[04:00-06:00] Platform-Specific Formatting**
```
"Let's generate the same topic for different platforms."

[Screen: Generate for LinkedIn, Twitter, Email]

"Notice how the content adapts:

LinkedIn (3000 char limit):
- Professional tone
- Industry hashtags
- Call-to-action

Twitter (280 char limit):
- Ultra-concise
- 2-3 hashtags max
- Thread format for longer content

Email Newsletter:
- Longer form
- Personalization variables
- Unsubscribe link

Each version maintains our brand voice while optimizing
for the platform's best practices."

[Screen: Show side-by-side comparison]
```

**[06:00-07:30] SEO Optimization**
```
"The SEO optimizer analyzes content and suggests improvements."

[Screen: Show SEO score breakdown]

"Our blog post has an SEO score of 78. Let's see the suggestions:
- Add target keyword to H1 heading
- Include related keywords in subheadings
- Optimize meta description
- Add internal links

I'll apply these suggestions."

[Screen: Click "Apply SEO Optimizations"]

"Now our score is 92! The system has:
- Restructured headings
- Added keyword-rich subheadings
- Generated meta description
- Suggested relevant internal links"
```

**[07:30-08:00] Wrap-up**
```
"You now understand the complete content generation workflow:
- Research-driven insights
- Platform-specific formatting
- SEO optimization

In the next tutorial, we'll cover image and video generation.
Thanks for watching!"
```

---

## Tutorial 3: Image and Video Generation (12 minutes)

### Objective
Demonstrate AI-powered media generation with DALL-E 3 and Runway ML.

### Script

**[00:00-00:30] Introduction**
```
"Welcome! Today we're exploring AI-powered image and video generation.
You'll learn how to create branded visuals for social media, blogs,
and advertising."
```

**[00:30-03:00] Image Generation with DALL-E 3**
```
"Let's create an image for our LinkedIn post about AI in marketing."

[Screen: Navigate to Media Review > Generate Image]

Content: "AI is Transforming B2B Marketing"
Image Type: Social Post
Dimensions: 1200x628 (LinkedIn standard)
Provider: DALL-E 3

[Screen: Show auto-generated prompt]

"The system has built this prompt:
'Professional team collaboration in modern office, AI dashboard visible
on screen, bright natural lighting, corporate colors #1E3A8A and #FFFFFF,
minimalist style, business illustration, 1200x628px'

Notice how it incorporated our brand colors and created a relevant scene."

[Screen: Click Generate]

"DALL-E 3 typically takes 15-30 seconds. Let's see the result."

[Screen: Show generated image]

"Excellent! The image perfectly matches our brand guidelines.
Now let's add our logo watermark."

[Screen: Edit > Add Watermark]

Watermark Text: "© Acme Marketing"
Position: Bottom Right
Opacity: 80%

[Screen: Show watermarked image]
```

**[03:00-05:00] Image Editing**
```
"We can make additional edits before publishing."

[Screen: Image editor interface]

"Let's:
1. Crop to focus on the dashboard
2. Adjust brightness slightly
3. Add a subtle filter

[Screen: Apply edits]

"Perfect! Now this image is ready for LinkedIn.
Let's attach it to our content draft."

[Screen: Attach to draft, show preview]
```

**[05:00-08:00] Video Generation with Runway ML**
```
"Now let's create a video explainer. This is more complex."

[Screen: Video generation form]

Content: "3 Benefits of Marketing Automation"
Video Type: Explainer
Duration: 30 seconds
Provider: Runway ML

[Screen: Show generated video script]

"The system has broken this into scenes:

Scene 1 (5s): Hook - 'Are you spending too much time on manual marketing tasks?'
Scene 2 (10s): Problem - Show frustrated marketer with piles of work
Scene 3 (10s): Solution - Automation dashboard demo
Scene 4 (5s): CTA - 'Try our platform today'

Each scene gets its own visual prompt for Runway ML."

[Screen: Start generation]

"Video generation takes 1-2 minutes as it generates each scene
then stitches them together. Let's see the progress."

[Screen: Show scene generation progress]
```

**[08:00-10:00] Video Post-Processing**
```
"The scenes are generated. Now the system is:
1. Stitching scenes with transitions
2. Adding captions
3. Adding background music
4. Adding our intro/outro

[Screen: Show final video player]

"Here's the final video! Notice:
- Smooth transitions between scenes
- Burned-in captions for accessibility
- Professional background music
- Our branding in intro/outro

Let's trim it slightly and adjust captions."

[Screen: Video editor]

Trim: 0:00 - 0:28 (cut last 2 seconds)
Caption Font Size: 52 → 48 (slightly smaller)

[Screen: Apply and preview]
```

**[10:00-11:30] Asset Library**
```
"All generated media is stored in the Asset Library for reuse."

[Screen: Navigate to Asset Library]

"Here you can:
- Search by keywords
- Filter by type, provider, date
- View usage analytics
- Reuse in new campaigns

Let's search for 'AI dashboard' and reuse a previous image."

[Screen: Search and select previous image]

"This saves time and API costs by reusing quality assets."
```

**[11:30-12:00] Wrap-up**
```
"You've now learned:
- DALL-E 3 image generation with brand guidelines
- Image editing and watermarking
- Runway ML video generation
- Asset reuse and management

Next tutorial: Multi-channel publishing and analytics. See you there!"
```

---

## Tutorial 4: Human-in-the-Loop Review (6 minutes)

### Objective
Demonstrate the content review workflow with revision cycles.

### Script

**[00:00-00:30] Introduction**
```
"In this tutorial, we'll explore the human review workflow.
You'll learn how to review AI-generated content, request revisions,
and track version history."
```

**[00:30-02:00] Review Queue**
```
"When content is generated, it enters the review queue with status 'In Review'."

[Screen: Navigate to Content Review]

"Here's our review queue. Let's open the first draft."

[Screen: Click on draft about 'Marketing Automation ROI']

"The review interface shows:
- Original content on the left
- Editable version on the right
- SEO score and metrics below
- Version history tab
- Feedback history tab

Let's review this content."
```

**[02:00-03:30] Requesting Revisions**
```
"This content is good, but I'd like it to be more data-driven.
Let's request revisions."

[Screen: Add feedback]

Feedback: "Add specific statistics and ROI percentages.
Make the tone more authoritative by citing industry studies."

Quality Rating: 3/5

Suggested Edits:
- Section: Introduction
  Suggestion: Add industry statistics on automation adoption
- Section: ROI Metrics
  Suggestion: Include specific percentage improvements

[Screen: Click "Request Revisions"]

"The system is now:
1. Sending feedback to the Content Agent
2. Using LLM to apply targeted edits
3. Creating a new version

This takes about 10 seconds."

[Screen: Show loading, then revised content appears]
```

**[03:30-04:30] Comparing Versions**
```
"Here's the revised version. Let's compare it with the original."

[Screen: Click "Version History" tab]

"We can see:
- Version 1: Original (250 words, SEO 78)
- Version 2: Current (280 words, SEO 85)

Click 'Compare' to see the diff."

[Screen: Show side-by-side diff]

"The system added:
- '73% of B2B marketers report using automation' - industry stat
- 'Companies see an average 14.5% increase in sales productivity' - ROI data
- 'According to Forrester Research...' - authority citation

Much better! The changes are exactly what I requested."
```

**[04:30-05:30] Approval and Publishing**
```
"This version is ready to publish. Let's approve it."

[Screen: Return to main review, click "Approve & Publish"]

"Now I can choose publishing channels."

[Screen: Publishing options]

☑ LinkedIn
☑ WordPress Blog
☐ Email Newsletter

Schedule: Immediate

[Screen: Click Publish]

"The content is now being published to LinkedIn and WordPress.
We can see the real-time status."

[Screen: Show publishing progress]

"Done! Here are the published URLs:
- LinkedIn: linkedin.com/posts/...
- WordPress: acme-marketing.com/blog/marketing-automation-roi

Both include our generated image."
```

**[05:30-06:00] Wrap-up**
```
"You've learned the review workflow:
- Reviewing content in the queue
- Requesting targeted revisions
- Comparing versions
- Approving and publishing

Next: Analytics and engagement tracking. Thanks for watching!"
```

---

## Tutorial 5: Analytics and Engagement Tracking (7 minutes)

### Objective
Show how to track content performance across channels and use insights for optimization.

### Script

**[00:00-00:30] Introduction**
```
"Welcome to the analytics tutorial. Today we'll explore how to track
content performance, analyze engagement metrics, and optimize campaigns."
```

**[00:30-02:00] Analytics Dashboard**
```
"Let's navigate to the Analytics page."

[Screen: Click Analytics in sidebar]

"The overview shows our key metrics:
- Total Views: 15,234
- Total Clicks: 1,847
- Total Shares: 234
- Total Conversions: 89
- Average Engagement Rate: 4.2%

These metrics are aggregated from LinkedIn, WordPress, and email campaigns."

[Screen: Show metric cards]

"Let's dive deeper with the time series chart."

[Screen: Scroll to chart]

Date Range: Last 30 Days
Granularity: Week
Channels: All

"We can see engagement spiked during week 3 - that's when we
published our video content. Videos drive 3x more engagement
than text-only posts."
```

**[02:00-04:00] Channel Performance**
```
"Let's compare performance across channels."

[Screen: Channel comparison chart]

"Here's what we see:

LinkedIn:
- Views: 8,500
- Engagement Rate: 5.8%
- Best performing content type: Video

WordPress:
- Views: 5,200
- Engagement Rate: 3.2%
- Best performing content type: Long-form guides

Email:
- Opens: 1,534 (42% open rate)
- Clicks: 467 (30% click-through rate)
- Best performing content type: Newsletters with images

Insights:
1. LinkedIn drives highest engagement
2. Video content performs best everywhere
3. Email has strong open rates - our audience is engaged

Let's use these insights to optimize our strategy."
```

**[04:00-05:30] Content Performance**
```
"Let's see which specific pieces performed best."

[Screen: Top Performing Content table]

"Our top 5 pieces:

1. 'AI Transforming Marketing' (LinkedIn Post + Video)
   - Views: 3,200
   - Engagement: 8.2%
   - Conversions: 24

2. 'Marketing Automation ROI Guide' (Blog Post)
   - Views: 2,100
   - Engagement: 5.1%
   - Conversions: 18

3. 'Weekly Newsletter #47' (Email)
   - Opens: 580
   - Clicks: 174 (30% CTR)
   - Conversions: 12

Let's click on the top performer to see detailed metrics."

[Screen: Click on 'AI Transforming Marketing']

"Detailed breakdown:
- Published: 14 days ago
- Peak engagement: Day 2 (618 views)
- Geographic distribution: 45% US, 30% Europe, 25% Asia
- Device breakdown: 60% mobile, 40% desktop
- Referral sources: 70% organic, 20% shares, 10% direct

The video attachment increased engagement by 140% compared to
similar text-only posts."
```

**[05:30-06:30] Campaign Insights**
```
"Let's look at overall campaign performance."

[Screen: Navigate to Campaigns page, select campaign]

"Our 'Q1 2024 Automation' campaign shows:

Total Content Pieces: 42
Published: 38
In Review: 3
Rejected: 1

Performance:
- Total Reach: 45,000
- Total Engagement: 2,300 (5.1%)
- Generated Leads: 156
- Cost per Lead: $12.50 (well below industry average of $20)

The trend is positive - engagement is increasing month-over-month.
Our AI-generated content performs as well as human-written content
but costs 70% less to produce."
```

**[06:30-07:00] Wrap-up**
```
"Key takeaways:
1. Video content drives 3x more engagement
2. LinkedIn is our highest-performing channel
3. Email maintains strong open/click rates
4. AI-generated content delivers strong ROI

Use these insights to optimize your content strategy.
That concludes our tutorial series. Happy marketing!"
```

---

## Recording Tips

### Equipment Needed
- Screen recording software (OBS Studio, Camtasia, or ScreenFlow)
- Microphone for clear audio (USB condenser mic recommended)
- Quiet recording environment
- Prepared demo environment with all services running

### Recording Checklist
- [ ] Close unnecessary browser tabs and applications
- [ ] Set screen resolution to 1920x1080
- [ ] Increase font sizes for visibility
- [ ] Hide sensitive information (API keys, personal data)
- [ ] Test audio levels before recording
- [ ] Have demo data pre-loaded in database
- [ ] Prepare browser bookmarks for quick navigation
- [ ] Clear browser history and cookies for clean UI
- [ ] Disable notifications and pop-ups

### Editing Guidelines
- Add intro/outro slides with branding
- Include timestamps for easy navigation
- Add zoom-ins for important UI elements
- Include callout boxes for key points
- Add background music (royalty-free)
- Export in 1080p @ 30fps
- Add closed captions for accessibility

### Publishing Platforms
- YouTube (public or unlisted)
- Vimeo (for higher quality)
- Internal wiki/documentation site
- README links to video tutorials

---

## Tutorial Maintenance

### Update Schedule
- Review every 3 months for UI changes
- Re-record if major features added
- Update scripts for version-specific changes
- Keep API credentials fresh in demos

### User Feedback
- Monitor comments for common questions
- Create FAQ based on user questions
- Add additional tutorials based on requests
- Track video analytics (views, completion rate)

---

This completes the video tutorial documentation. Each tutorial is designed to be standalone but also part of a comprehensive learning path for new users of the B2B Marketing Automation Platform.
