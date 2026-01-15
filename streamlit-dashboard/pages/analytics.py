"""
Analytics Dashboard - Campaign Performance and Engagement Metrics
Provides visualization and analysis of content performance across channels
"""

import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="Analytics - Marketing Dashboard",
    page_icon="📊",
    layout="wide"
)

# Database connection configuration
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "database": os.getenv("POSTGRES_DB", "marketing_db"),
    "user": os.getenv("POSTGRES_USER", "marketing_user"),
    "password": os.getenv("POSTGRES_PASSWORD", "marketing_pass")
}


@st.cache_resource
def get_db_connection():
    """Create and cache database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True  # Prevent transaction issues
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {str(e)}")
        return None


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_campaign_metrics(campaign_id: Optional[int] = None,
                         date_from: Optional[datetime] = None,
                         date_to: Optional[datetime] = None) -> pd.DataFrame:
    """Get aggregated campaign metrics"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
                SELECT
                    c.id as campaign_id,
                    c.name as campaign_name,
                    c.status,
                    COUNT(DISTINCT cd.id) as total_content,
                    COUNT(DISTINCT pc.id) as published_content,
                    COALESCE(SUM(em.views), 0) as total_views,
                    COALESCE(SUM(em.clicks), 0) as total_clicks,
                    COALESCE(SUM(em.shares), 0) as total_shares,
                    COALESCE(SUM(em.conversions), 0) as total_conversions,
                    CASE
                        WHEN SUM(em.views) > 0 THEN
                            ROUND((SUM(em.clicks)::numeric + SUM(em.shares)::numeric) /
                                  SUM(em.views)::numeric * 100, 2)
                        ELSE 0
                    END as engagement_rate
                FROM campaigns c
                LEFT JOIN content_drafts cd ON c.id = cd.campaign_id
                LEFT JOIN published_content pc ON cd.id = pc.draft_id
                LEFT JOIN engagement_metrics em ON pc.id = em.content_id
                WHERE 1=1
            """
            params = []

            if campaign_id:
                query += " AND c.id = %s"
                params.append(campaign_id)

            if date_from:
                query += " AND pc.published_at >= %s"
                params.append(date_from)

            if date_to:
                query += " AND pc.published_at <= %s"
                params.append(date_to)

            query += """
                GROUP BY c.id, c.name, c.status
                ORDER BY total_views DESC
            """

            cursor.execute(query, params)
            results = cursor.fetchall()

            return pd.DataFrame(results) if results else pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching campaign metrics: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_channel_performance(campaign_id: Optional[int] = None,
                            date_from: Optional[datetime] = None,
                            date_to: Optional[datetime] = None) -> pd.DataFrame:
    """Get performance metrics by channel"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
                SELECT
                    pc.channel,
                    COUNT(DISTINCT pc.id) as published_count,
                    COALESCE(SUM(em.views), 0) as total_views,
                    COALESCE(SUM(em.clicks), 0) as total_clicks,
                    COALESCE(SUM(em.shares), 0) as total_shares,
                    COALESCE(SUM(em.conversions), 0) as total_conversions,
                    CASE
                        WHEN SUM(em.views) > 0 THEN
                            ROUND((SUM(em.clicks)::numeric + SUM(em.shares)::numeric) /
                                  SUM(em.views)::numeric * 100, 2)
                        ELSE 0
                    END as engagement_rate
                FROM published_content pc
                LEFT JOIN engagement_metrics em ON pc.id = em.content_id
                LEFT JOIN content_drafts cd ON pc.draft_id = cd.id
                WHERE 1=1
            """
            params = []

            if campaign_id:
                query += " AND cd.campaign_id = %s"
                params.append(campaign_id)

            if date_from:
                query += " AND pc.published_at >= %s"
                params.append(date_from)

            if date_to:
                query += " AND pc.published_at <= %s"
                params.append(date_to)

            query += " GROUP BY pc.channel ORDER BY total_views DESC"

            cursor.execute(query, params)
            results = cursor.fetchall()

            return pd.DataFrame(results) if results else pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching channel performance: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_content_type_performance(campaign_id: Optional[int] = None,
                                date_from: Optional[datetime] = None,
                                date_to: Optional[datetime] = None) -> pd.DataFrame:
    """Get performance metrics by content type"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
                SELECT
                    cd.type as content_type,
                    COUNT(DISTINCT pc.id) as published_count,
                    COALESCE(SUM(em.views), 0) as total_views,
                    COALESCE(SUM(em.clicks), 0) as total_clicks,
                    COALESCE(SUM(em.shares), 0) as total_shares,
                    COALESCE(SUM(em.conversions), 0) as total_conversions,
                    CASE
                        WHEN SUM(em.views) > 0 THEN
                            ROUND((SUM(em.clicks)::numeric + SUM(em.shares)::numeric) /
                                  SUM(em.views)::numeric * 100, 2)
                        ELSE 0
                    END as engagement_rate
                FROM content_drafts cd
                LEFT JOIN published_content pc ON cd.id = pc.draft_id
                LEFT JOIN engagement_metrics em ON pc.id = em.content_id
                WHERE pc.id IS NOT NULL
            """
            params = []

            if campaign_id:
                query += " AND cd.campaign_id = %s"
                params.append(campaign_id)

            if date_from:
                query += " AND pc.published_at >= %s"
                params.append(date_from)

            if date_to:
                query += " AND pc.published_at <= %s"
                params.append(date_to)

            query += " GROUP BY cd.type ORDER BY total_views DESC"

            cursor.execute(query, params)
            results = cursor.fetchall()

            return pd.DataFrame(results) if results else pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching content type performance: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_time_series_data(campaign_id: Optional[int] = None,
                        date_from: Optional[datetime] = None,
                        date_to: Optional[datetime] = None,
                        granularity: str = 'day') -> pd.DataFrame:
    """Get time series engagement data"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Determine date truncation based on granularity
            date_trunc = {
                'hour': 'hour',
                'day': 'day',
                'week': 'week',
                'month': 'month'
            }.get(granularity, 'day')

            query = f"""
                SELECT
                    DATE_TRUNC('{date_trunc}', em.tracked_at) as time_period,
                    SUM(em.views) as views,
                    SUM(em.clicks) as clicks,
                    SUM(em.shares) as shares,
                    SUM(em.conversions) as conversions
                FROM engagement_metrics em
                JOIN published_content pc ON em.content_id = pc.id
                JOIN content_drafts cd ON pc.draft_id = cd.id
                WHERE 1=1
            """
            params = []

            if campaign_id:
                query += " AND cd.campaign_id = %s"
                params.append(campaign_id)

            if date_from:
                query += " AND em.tracked_at >= %s"
                params.append(date_from)

            if date_to:
                query += " AND em.tracked_at <= %s"
                params.append(date_to)

            query += " GROUP BY time_period ORDER BY time_period"

            cursor.execute(query, params)
            results = cursor.fetchall()

            df = pd.DataFrame(results) if results else pd.DataFrame()

            if not df.empty:
                df['time_period'] = pd.to_datetime(df['time_period'])

            return df
    except Exception as e:
        st.error(f"Error fetching time series data: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_top_performing_content(campaign_id: Optional[int] = None,
                              date_from: Optional[datetime] = None,
                              date_to: Optional[datetime] = None,
                              limit: int = 10) -> pd.DataFrame:
    """Get top performing content pieces"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
                SELECT
                    cd.id,
                    cd.type,
                    LEFT(cd.content, 100) as content_preview,
                    c.name as campaign_name,
                    pc.channel,
                    pc.published_at,
                    COALESCE(SUM(em.views), 0) as views,
                    COALESCE(SUM(em.clicks), 0) as clicks,
                    COALESCE(SUM(em.shares), 0) as shares,
                    COALESCE(SUM(em.conversions), 0) as conversions,
                    CASE
                        WHEN SUM(em.views) > 0 THEN
                            ROUND((SUM(em.clicks)::numeric + SUM(em.shares)::numeric) /
                                  SUM(em.views)::numeric * 100, 2)
                        ELSE 0
                    END as engagement_rate
                FROM content_drafts cd
                JOIN campaigns c ON cd.campaign_id = c.id
                JOIN published_content pc ON cd.id = pc.draft_id
                LEFT JOIN engagement_metrics em ON pc.id = em.content_id
                WHERE 1=1
            """
            params = []

            if campaign_id:
                query += " AND cd.campaign_id = %s"
                params.append(campaign_id)

            if date_from:
                query += " AND pc.published_at >= %s"
                params.append(date_from)

            if date_to:
                query += " AND pc.published_at <= %s"
                params.append(date_to)

            query += """
                GROUP BY cd.id, cd.type, cd.content, c.name, pc.channel, pc.published_at
                ORDER BY engagement_rate DESC, views DESC
                LIMIT %s
            """
            params.append(limit)

            cursor.execute(query, params)
            results = cursor.fetchall()

            return pd.DataFrame(results) if results else pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching top content: {str(e)}")
        return pd.DataFrame()


def get_campaigns() -> List[Dict]:
    """Get all campaigns for filtering"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, name, status
                FROM campaigns
                ORDER BY created_at DESC
            """)
            return cursor.fetchall()
    except Exception as e:
        st.error(f"Error fetching campaigns: {str(e)}")
        return []


def main():
    """Main analytics dashboard"""

    st.title("📊 Analytics Dashboard")
    st.markdown("Track campaign performance and engagement metrics across channels")

    # Sidebar filters
    with st.sidebar:
        st.header("⚙️ Filters")

        # Campaign filter
        campaigns = get_campaigns()
        campaign_options = ["All Campaigns"] + [c['name'] for c in campaigns]
        campaign_filter = st.selectbox("Campaign", campaign_options)

        # Date range preset
        date_preset = st.selectbox(
            "Date Range",
            ["Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom"],
            index=1
        )

        # Calculate date range
        if date_preset == "Custom":
            date_from = st.date_input("From", value=datetime.now() - timedelta(days=30))
            date_to = st.date_input("To", value=datetime.now())
        else:
            days_map = {
                "Last 7 Days": 7,
                "Last 30 Days": 30,
                "Last 90 Days": 90
            }
            days = days_map.get(date_preset, 30)
            date_from = datetime.now() - timedelta(days=days)
            date_to = datetime.now()

        # Time series granularity
        st.markdown("---")
        granularity = st.radio(
            "Time Series View",
            ["Day", "Week", "Month"],
            horizontal=True
        ).lower()

        # Refresh data
        st.markdown("---")
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # Get campaign ID if filtered
    campaign_id = None
    if campaign_filter != "All Campaigns":
        matching_campaign = next((c for c in campaigns if c['name'] == campaign_filter), None)
        if matching_campaign:
            campaign_id = matching_campaign['id']

    # Convert dates to datetime
    date_from_dt = datetime.combine(date_from, datetime.min.time())
    date_to_dt = datetime.combine(date_to, datetime.max.time())

    # Fetch data
    campaign_metrics = get_campaign_metrics(campaign_id, date_from_dt, date_to_dt)
    channel_performance = get_channel_performance(campaign_id, date_from_dt, date_to_dt)
    content_type_performance = get_content_type_performance(campaign_id, date_from_dt, date_to_dt)
    time_series = get_time_series_data(campaign_id, date_from_dt, date_to_dt, granularity)
    top_content = get_top_performing_content(campaign_id, date_from_dt, date_to_dt, limit=10)

    # Overview metrics
    st.subheader("📈 Overview")

    if not campaign_metrics.empty:
        total_views = campaign_metrics['total_views'].sum()
        total_clicks = campaign_metrics['total_clicks'].sum()
        total_shares = campaign_metrics['total_shares'].sum()
        total_conversions = campaign_metrics['total_conversions'].sum()
        avg_engagement = campaign_metrics['engagement_rate'].mean()

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric("Total Views", f"{int(total_views):,}")
        col2.metric("Total Clicks", f"{int(total_clicks):,}")
        col3.metric("Total Shares", f"{int(total_shares):,}")
        col4.metric("Conversions", f"{int(total_conversions):,}")
        col5.metric("Avg Engagement", f"{avg_engagement:.2f}%")
    else:
        st.info("No data available for the selected filters")
        return

    st.markdown("---")

    # Time series visualization
    st.subheader("📊 Engagement Over Time")

    if not time_series.empty:
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=time_series['time_period'],
            y=time_series['views'],
            name='Views',
            mode='lines+markers',
            line=dict(color='#667eea', width=3)
        ))

        fig.add_trace(go.Scatter(
            x=time_series['time_period'],
            y=time_series['clicks'],
            name='Clicks',
            mode='lines+markers',
            line=dict(color='#f093fb', width=2)
        ))

        fig.add_trace(go.Scatter(
            x=time_series['time_period'],
            y=time_series['shares'],
            name='Shares',
            mode='lines+markers',
            line=dict(color='#4facfe', width=2)
        ))

        fig.update_layout(
            height=400,
            hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            margin=dict(l=0, r=0, t=30, b=0)
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No time series data available")

    st.markdown("---")

    # Channel and content type performance
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📱 Performance by Channel")

        if not channel_performance.empty:
            fig = px.bar(
                channel_performance,
                x='channel',
                y=['total_views', 'total_clicks', 'total_shares'],
                barmode='group',
                color_discrete_sequence=['#667eea', '#f093fb', '#4facfe']
            )
            fig.update_layout(
                height=350,
                showlegend=True,
                legend=dict(title='Metric'),
                margin=dict(l=0, r=0, t=0, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)

            # Engagement rate by channel
            st.markdown("**Engagement Rate by Channel**")
            for _, row in channel_performance.iterrows():
                st.metric(
                    row['channel'].upper(),
                    f"{row['engagement_rate']:.2f}%",
                    delta=f"{row['published_count']} posts"
                )
        else:
            st.info("No channel data available")

    with col2:
        st.subheader("📝 Performance by Content Type")

        if not content_type_performance.empty:
            fig = px.pie(
                content_type_performance,
                values='total_views',
                names='content_type',
                color_discrete_sequence=px.colors.sequential.Purples_r
            )
            fig.update_layout(
                height=350,
                margin=dict(l=0, r=0, t=0, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)

            # Engagement rate by content type
            st.markdown("**Engagement Rate by Type**")
            for _, row in content_type_performance.iterrows():
                st.metric(
                    row['content_type'].upper(),
                    f"{row['engagement_rate']:.2f}%",
                    delta=f"{row['published_count']} posts"
                )
        else:
            st.info("No content type data available")

    st.markdown("---")

    # Campaign comparison
    if campaign_id is None:  # Only show when viewing all campaigns
        st.subheader("🎯 Campaign Comparison")

        if not campaign_metrics.empty and len(campaign_metrics) > 1:
            # Sort by engagement rate
            campaign_metrics_sorted = campaign_metrics.sort_values('engagement_rate', ascending=False)

            fig = px.bar(
                campaign_metrics_sorted.head(10),
                x='campaign_name',
                y='engagement_rate',
                color='total_views',
                color_continuous_scale='Purples',
                labels={'engagement_rate': 'Engagement Rate (%)', 'campaign_name': 'Campaign'}
            )
            fig.update_layout(
                height=400,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)

            # Campaign metrics table
            st.markdown("**Detailed Metrics**")
            display_df = campaign_metrics[[
                'campaign_name', 'status', 'total_content', 'published_content',
                'total_views', 'total_clicks', 'total_shares', 'engagement_rate'
            ]].copy()

            display_df.columns = [
                'Campaign', 'Status', 'Content', 'Published',
                'Views', 'Clicks', 'Shares', 'Engagement %'
            ]

            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("Need multiple campaigns to show comparison")

        st.markdown("---")

    # Top performing content
    st.subheader("🏆 Top Performing Content")

    if not top_content.empty:
        for idx, row in top_content.iterrows():
            with st.expander(
                f"#{idx + 1} - {row['type'].upper()} • {row['channel'].upper()} • "
                f"{row['engagement_rate']:.2f}% engagement"
            ):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"**Campaign:** {row['campaign_name']}")
                    st.markdown(f"**Published:** {row['published_at'].strftime('%Y-%m-%d %H:%M')}")
                    st.markdown("**Preview:**")
                    st.caption(row['content_preview'] + "...")

                with col2:
                    st.metric("Views", f"{int(row['views']):,}")
                    st.metric("Clicks", f"{int(row['clicks']):,}")
                    st.metric("Shares", f"{int(row['shares']):,}")
                    st.metric("Conversions", f"{int(row['conversions']):,}")
    else:
        st.info("No published content available")


if __name__ == "__main__":
    main()
