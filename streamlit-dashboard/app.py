"""
Marketing Automation Dashboard - Main Application
Streamlit-based UI for content review, analytics, and campaign management
"""

import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
from typing import Dict, List, Optional

# Page configuration
st.set_page_config(
    page_title="Marketing Automation Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
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


def reset_db_connection():
    """Reset database connection if in bad state"""
    try:
        conn = get_db_connection()
        if conn and conn.closed == 0:
            conn.rollback()  # Clear any failed transaction state
    except Exception:
        pass


def get_user_campaigns(user_id: Optional[int] = None) -> List[Dict]:
    """Fetch campaigns for the current user"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            if user_id:
                cursor.execute("""
                    SELECT id, name, status, target_audience, created_at,
                           (SELECT COUNT(*) FROM content_drafts WHERE campaign_id = campaigns.id) as content_count
                    FROM campaigns
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT id, name, status, target_audience, created_at,
                           (SELECT COUNT(*) FROM content_drafts WHERE campaign_id = campaigns.id) as content_count
                    FROM campaigns
                    ORDER BY created_at DESC
                """)

            return cursor.fetchall()
    except Exception as e:
        st.error(f"Error fetching campaigns: {str(e)}")
        return []


def get_pending_reviews() -> Dict[str, int]:
    """Get count of pending reviews by type"""
    conn = get_db_connection()
    if not conn:
        return {}

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE status = 'in_review') as content_reviews,
                    COUNT(*) FILTER (WHERE status = 'draft') as drafts,
                    COUNT(*) FILTER (WHERE status = 'approved') as approved,
                    COUNT(*) FILTER (WHERE status = 'rejected') as rejected
                FROM content_drafts
            """)

            result = cursor.fetchone()
            return dict(result) if result else {}
    except Exception as e:
        st.error(f"Error fetching review counts: {str(e)}")
        return {}


def get_media_review_count() -> int:
    """Get count of media assets pending review"""
    conn = get_db_connection()
    if not conn:
        return 0

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*)
                FROM media_assets ma
                JOIN content_drafts cd ON ma.draft_id = cd.id
                WHERE cd.status = 'in_review'
            """)

            result = cursor.fetchone()
            return result[0] if result else 0
    except Exception as e:
        st.error(f"Error fetching media review count: {str(e)}")
        return 0


def main():
    """Main dashboard application"""

    # Custom CSS for better styling
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: 700;
            color: #1E3A8A;
            margin-bottom: 1rem;
        }
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 10px;
            color: white;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
        }
        .metric-label {
            font-size: 0.9rem;
            opacity: 0.9;
        }
        .sidebar .sidebar-content {
            background-color: #f8f9fa;
        }
        .stButton>button {
            width: 100%;
            border-radius: 5px;
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)

    # Sidebar with quick stats
    with st.sidebar:
        st.image("https://via.placeholder.com/200x60/1E3A8A/FFFFFF?text=Marketing+AI")
        st.markdown("---")

        # Quick stats in sidebar
        review_counts = get_pending_reviews()
        media_count = get_media_review_count()

        st.markdown("### Quick Stats")
        if review_counts:
            st.metric("Pending Reviews", review_counts.get('content_reviews', 0))
            st.metric("Media to Review", media_count)
            st.metric("Approved", review_counts.get('approved', 0))

        st.markdown("---")
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # Show main dashboard
    show_dashboard()


def show_dashboard():
    """Display main dashboard overview"""

    st.markdown('<h1 class="main-header">📊 Marketing Automation Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("Welcome to your AI-powered marketing command center")

    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)

    review_counts = get_pending_reviews()
    media_count = get_media_review_count()

    with col1:
        st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{}</div>
                <div class="metric-label">Pending Reviews</div>
            </div>
        """.format(review_counts.get('content_reviews', 0)), unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                <div class="metric-value">{}</div>
                <div class="metric-label">Media Assets</div>
            </div>
        """.format(media_count), unsafe_allow_html=True)

    with col3:
        st.markdown("""
            <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                <div class="metric-value">{}</div>
                <div class="metric-label">Approved Content</div>
            </div>
        """.format(review_counts.get('approved', 0)), unsafe_allow_html=True)

    with col4:
        campaigns = get_user_campaigns()
        active_campaigns = len([c for c in campaigns if c['status'] == 'active'])
        st.markdown("""
            <div class="metric-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
                <div class="metric-value">{}</div>
                <div class="metric-label">Active Campaigns</div>
            </div>
        """.format(active_campaigns), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Recent activity section
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📝 Recent Content")

        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT cd.id, cd.type, cd.content, cd.status, cd.created_at,
                               c.name as campaign_name,
                               (SELECT COUNT(*) FROM media_assets WHERE draft_id = cd.id) as media_count
                        FROM content_drafts cd
                        JOIN campaigns c ON cd.campaign_id = c.id
                        ORDER BY cd.created_at DESC
                        LIMIT 10
                    """)

                    drafts = cursor.fetchall()

                    for draft in drafts:
                        with st.expander(f"**{draft['type'].upper()}** - {draft['campaign_name']} ({draft['status']})"):
                            st.caption(f"Created: {draft['created_at'].strftime('%Y-%m-%d %H:%M')}")
                            st.caption(f"Media: {draft['media_count']} assets")

                            # Preview content (first 200 chars)
                            content_preview = draft['content'][:200] + "..." if len(draft['content']) > 200 else draft['content']
                            st.markdown(content_preview)

                            # Action buttons
                            btn_col1, btn_col2, btn_col3 = st.columns(3)
                            with btn_col1:
                                if st.button("📝 Review", key=f"review_{draft['id']}"):
                                    st.session_state['review_draft_id'] = draft['id']
                                    st.rerun()
                            with btn_col2:
                                if st.button("📊 Analytics", key=f"analytics_{draft['id']}"):
                                    st.info(f"Analytics for draft {draft['id']}")
                            with btn_col3:
                                if st.button("🗑️ Delete", key=f"delete_{draft['id']}"):
                                    st.warning(f"Delete draft {draft['id']}?")

            except Exception as e:
                st.error(f"Error loading recent content: {str(e)}")

    with col2:
        st.subheader("🎯 Active Campaigns")

        campaigns = get_user_campaigns()
        active_campaigns = [c for c in campaigns if c['status'] == 'active']

        if active_campaigns:
            for campaign in active_campaigns[:5]:
                with st.container():
                    st.markdown(f"**{campaign['name']}**")
                    st.caption(f"{campaign['content_count']} content pieces")
                    st.progress(min(campaign['content_count'] / 10, 1.0))
                    st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.info("No active campaigns. Create one to get started!")
            if st.button("➕ Create Campaign"):
                st.info("Navigate to Campaigns page")

    # Quick actions
    st.markdown("---")
    st.subheader("⚡ Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("✨ Generate Content", use_container_width=True):
            st.info("Navigate to Content Generation")

    with col2:
        if st.button("🎨 Create Image", use_container_width=True):
            st.info("Navigate to Image Generation")

    with col3:
        if st.button("🎬 Create Video", use_container_width=True):
            st.info("Navigate to Video Generation")

    with col4:
        if st.button("🔍 Trend Analysis", use_container_width=True):
            st.info("Navigate to Trend Monitoring")


if __name__ == "__main__":
    main()
