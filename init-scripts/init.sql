-- B2B Marketing Automation Platform Database Schema
-- Created: 2026-01-13
-- Description: Comprehensive schema for marketing automation with multi-agent system

-- Create additional databases for n8n and matomo
CREATE DATABASE n8n;
CREATE DATABASE matomo;
CREATE DATABASE marketing;

-- Connect to marketing database
\c marketing

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search optimization

-- ==================== USERS & CAMPAIGNS ====================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    company VARCHAR(255),
    full_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_company ON users(company);

CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    target_audience JSONB,  -- Stores audience segments, demographics, interests
    branding_json JSONB,    -- Stores brand colors, fonts, logo URLs, voice guidelines
    status VARCHAR(50) DEFAULT 'active',  -- active, paused, completed, archived
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_campaigns_user ON campaigns(user_id);
CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_campaigns_created_at ON campaigns(created_at DESC);

-- ==================== CONTENT MANAGEMENT ====================

CREATE TABLE content_drafts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,  -- text, image, video, carousel
    title VARCHAR(500),
    content TEXT,  -- For text content or descriptions
    seo_score DECIMAL(5,2),  -- 0-100 score
    keywords TEXT[],  -- Array of SEO keywords
    status VARCHAR(50) DEFAULT 'draft',  -- draft, in_review, approved, rejected, published
    channel VARCHAR(50),  -- linkedin, wordpress, email, twitter, instagram
    scheduled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) DEFAULT 'ai_agent'  -- ai_agent, human_editor
);

CREATE INDEX idx_content_drafts_campaign ON content_drafts(campaign_id);
CREATE INDEX idx_content_drafts_status ON content_drafts(status);
CREATE INDEX idx_content_drafts_type ON content_drafts(type);
CREATE INDEX idx_content_drafts_scheduled ON content_drafts(scheduled_at);

CREATE TABLE content_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    draft_id UUID REFERENCES content_drafts(id) ON DELETE CASCADE,
    version_number INT NOT NULL,
    content TEXT,
    changes_summary TEXT,
    created_by VARCHAR(100),  -- Reviewer name or 'ai_agent'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_content_versions_draft ON content_versions(draft_id);
CREATE INDEX idx_content_versions_number ON content_versions(draft_id, version_number);

CREATE TABLE review_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    draft_id UUID REFERENCES content_drafts(id) ON DELETE CASCADE,
    reviewer VARCHAR(255),
    feedback_text TEXT NOT NULL,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    suggested_edits TEXT,
    feedback_type VARCHAR(50),  -- tone, grammar, accuracy, branding, seo
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_review_feedback_draft ON review_feedback(draft_id);
CREATE INDEX idx_review_feedback_created ON review_feedback(created_at DESC);

-- ==================== MEDIA ASSETS ====================

CREATE TABLE media_assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    draft_id UUID REFERENCES content_drafts(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,  -- image, video
    file_path VARCHAR(500),
    url TEXT,
    prompt TEXT,  -- The prompt used to generate this asset
    api_provider VARCHAR(100),  -- dalle3, midjourney, runway, pika, stable_diffusion
    metadata_json JSONB,  -- dimensions, duration, format, size_bytes, prompt_params
    generation_cost DECIMAL(10,4),  -- Track API costs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_media_assets_draft ON media_assets(draft_id);
CREATE INDEX idx_media_assets_type ON media_assets(type);
CREATE INDEX idx_media_assets_provider ON media_assets(api_provider);

CREATE TABLE media_edits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID REFERENCES media_assets(id) ON DELETE CASCADE,
    edit_type VARCHAR(50),  -- crop, resize, filter, watermark, trim, caption, music
    edit_params JSONB,  -- Parameters used for the edit
    edited_file_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_media_edits_asset ON media_edits(asset_id);

-- ==================== RESEARCH & ANALYSIS ====================

CREATE TABLE competitors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    url TEXT,
    industry VARCHAR(255),
    last_scraped TIMESTAMP,
    data_json JSONB,  -- Stores competitor metrics, content examples, pricing, etc.
    scraping_status VARCHAR(50) DEFAULT 'pending',  -- pending, success, failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_competitors_campaign ON competitors(campaign_id);
CREATE INDEX idx_competitors_last_scraped ON competitors(last_scraped DESC);

CREATE TABLE market_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    segment VARCHAR(255),  -- Target audience segment
    insights_json JSONB,  -- Demographics, pain points, preferences, behavior patterns
    confidence_score DECIMAL(5,2),  -- 0-100 confidence in insights
    source VARCHAR(100),  -- web_scraping, survey, analytics, ai_analysis
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_market_insights_campaign ON market_insights(campaign_id);
CREATE INDEX idx_market_insights_segment ON market_insights(segment);

CREATE TABLE trends (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic VARCHAR(255) NOT NULL,
    score DECIMAL(10,2),  -- Trend strength/popularity score
    category VARCHAR(100),  -- technology, marketing, business, industry-specific
    source VARCHAR(100),  -- reddit, hackernews, google_trends, twitter
    metadata_json JSONB,  -- Additional trend data, related keywords, time series
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trends_topic ON trends(topic);
CREATE INDEX idx_trends_score ON trends(score DESC);
CREATE INDEX idx_trends_detected ON trends(detected_at DESC);
CREATE INDEX idx_trends_category ON trends(category);

-- ==================== PUBLISHING & TRACKING ====================

CREATE TABLE published_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    draft_id UUID REFERENCES content_drafts(id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL,  -- linkedin, wordpress, email, twitter
    url TEXT,
    post_id VARCHAR(255),  -- Platform-specific post/article ID
    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    publish_status VARCHAR(50) DEFAULT 'success'  -- success, failed, pending
);

CREATE INDEX idx_published_content_draft ON published_content(draft_id);
CREATE INDEX idx_published_content_channel ON published_content(channel);
CREATE INDEX idx_published_content_published_at ON published_content(published_at DESC);

CREATE TABLE engagement_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id UUID REFERENCES published_content(id) ON DELETE CASCADE,
    views INT DEFAULT 0,
    clicks INT DEFAULT 0,
    shares INT DEFAULT 0,
    likes INT DEFAULT 0,
    comments INT DEFAULT 0,
    conversions INT DEFAULT 0,
    engagement_rate DECIMAL(5,2),  -- Calculated engagement percentage
    tracked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_engagement_metrics_content ON engagement_metrics(content_id);
CREATE INDEX idx_engagement_metrics_tracked_at ON engagement_metrics(tracked_at DESC);

-- ==================== AGENT STATE & MEMORY ====================

CREATE TABLE agent_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    agent_name VARCHAR(100),  -- supervisor, research, content, image, etc.
    conversation_history JSONB,  -- Array of messages with roles and content
    state JSONB,  -- Current agent state for LangGraph
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agent_conversations_campaign ON agent_conversations(campaign_id);
CREATE INDEX idx_agent_conversations_agent ON agent_conversations(agent_name);

CREATE TABLE agent_tool_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name VARCHAR(100),
    tool_name VARCHAR(100),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    input_params JSONB,
    output_result JSONB,
    execution_time_ms INT,
    success BOOLEAN,
    error_message TEXT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agent_tool_usage_agent ON agent_tool_usage(agent_name);
CREATE INDEX idx_agent_tool_usage_tool ON agent_tool_usage(tool_name);
CREATE INDEX idx_agent_tool_usage_executed ON agent_tool_usage(executed_at DESC);

-- ==================== COST TRACKING ====================

CREATE TABLE api_costs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service VARCHAR(100),  -- openai, runway, midjourney, pika
    operation_type VARCHAR(100),  -- image_generation, video_generation, llm_call
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    units_consumed DECIMAL(10,4),  -- tokens, images, seconds, etc.
    cost_usd DECIMAL(10,4),
    metadata_json JSONB,  -- model, resolution, duration, etc.
    tracked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_costs_service ON api_costs(service);
CREATE INDEX idx_api_costs_campaign ON api_costs(campaign_id);
CREATE INDEX idx_api_costs_tracked ON api_costs(tracked_at DESC);

-- ==================== VIEWS FOR ANALYTICS ====================

-- Campaign performance view
CREATE VIEW campaign_performance AS
SELECT
    c.id AS campaign_id,
    c.name AS campaign_name,
    c.status,
    COUNT(DISTINCT cd.id) AS total_drafts,
    COUNT(DISTINCT CASE WHEN cd.status = 'published' THEN cd.id END) AS published_count,
    COUNT(DISTINCT pc.id) AS total_published,
    COALESCE(SUM(em.views), 0) AS total_views,
    COALESCE(SUM(em.clicks), 0) AS total_clicks,
    COALESCE(SUM(em.conversions), 0) AS total_conversions,
    COALESCE(AVG(em.engagement_rate), 0) AS avg_engagement_rate,
    COALESCE(SUM(ac.cost_usd), 0) AS total_api_costs
FROM campaigns c
LEFT JOIN content_drafts cd ON c.id = cd.campaign_id
LEFT JOIN published_content pc ON cd.id = pc.draft_id
LEFT JOIN engagement_metrics em ON pc.id = em.content_id
LEFT JOIN api_costs ac ON c.id = ac.campaign_id
GROUP BY c.id, c.name, c.status;

-- Content review queue view
CREATE VIEW review_queue AS
SELECT
    cd.id AS draft_id,
    cd.campaign_id,
    c.name AS campaign_name,
    cd.title,
    cd.type,
    cd.status,
    cd.created_at,
    COUNT(DISTINCT rf.id) AS feedback_count,
    ARRAY_AGG(DISTINCT ma.url) FILTER (WHERE ma.url IS NOT NULL) AS media_urls
FROM content_drafts cd
JOIN campaigns c ON cd.campaign_id = c.id
LEFT JOIN review_feedback rf ON cd.id = rf.draft_id
LEFT JOIN media_assets ma ON cd.id = ma.draft_id
WHERE cd.status IN ('draft', 'in_review')
GROUP BY cd.id, cd.campaign_id, c.name, cd.title, cd.type, cd.status, cd.created_at
ORDER BY cd.created_at DESC;

-- ==================== FUNCTIONS ====================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_campaigns_updated_at BEFORE UPDATE ON campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_content_drafts_updated_at BEFORE UPDATE ON content_drafts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_media_assets_updated_at BEFORE UPDATE ON media_assets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_competitors_updated_at BEFORE UPDATE ON competitors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_conversations_updated_at BEFORE UPDATE ON agent_conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==================== SEED DATA ====================

-- Insert default admin user
INSERT INTO users (email, company, full_name) VALUES
('admin@marketing-system.local', 'Marketing Automation Inc', 'System Administrator');

-- ==================== GRANTS ====================

-- Grant permissions to marketing_user (from docker-compose)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO marketing_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO marketing_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO marketing_user;

-- ==================== COMPLETION MESSAGE ====================

DO $$
BEGIN
    RAISE NOTICE 'Database schema initialized successfully!';
    RAISE NOTICE 'Total tables created: %', (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE');
    RAISE NOTICE 'Total views created: %', (SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public');
END $$;
