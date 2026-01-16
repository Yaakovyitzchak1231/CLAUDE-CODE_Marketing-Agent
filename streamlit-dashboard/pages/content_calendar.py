"""
Content Calendar - Schedule and Manage Content Publishing Dates
Provides calendar visualization and scheduling capabilities for content across all channels
"""

import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import calendar

# Page configuration
st.set_page_config(
    page_title="Content Calendar - Marketing Dashboard",
    page_icon="📅",
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
def get_scheduled_content(campaign_id: Optional[int] = None,
                         date_from: Optional[datetime] = None,
                         date_to: Optional[datetime] = None,
                         channel: Optional[str] = None) -> pd.DataFrame:
    """Get scheduled content with filters"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
                SELECT
                    cd.id,
                    cd.type as content_type,
                    cd.content,
                    cd.status,
                    cd.scheduled_at,
                    cd.seo_score,
                    cd.created_at,
                    c.id as campaign_id,
                    c.name as campaign_name,
                    c.status as campaign_status,
                    pc.id as published_id,
                    pc.channel,
                    pc.published_at,
                    (SELECT COUNT(*) FROM media_assets WHERE draft_id = cd.id) as media_count,
                    (SELECT COUNT(*) FROM review_feedback WHERE draft_id = cd.id) as feedback_count
                FROM content_drafts cd
                LEFT JOIN campaigns c ON cd.campaign_id = c.id
                LEFT JOIN published_content pc ON cd.id = pc.draft_id
                WHERE cd.scheduled_at IS NOT NULL
            """
            params = []

            if campaign_id:
                query += " AND cd.campaign_id = %s"
                params.append(campaign_id)

            if date_from:
                query += " AND cd.scheduled_at >= %s"
                params.append(date_from)

            if date_to:
                query += " AND cd.scheduled_at <= %s"
                params.append(date_to)

            if channel:
                query += " AND pc.channel = %s"
                params.append(channel)

            query += " ORDER BY cd.scheduled_at ASC"

            cursor.execute(query, params)
            results = cursor.fetchall()

            return pd.DataFrame(results) if results else pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching scheduled content: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_campaigns_for_filter() -> List[Dict]:
    """Get list of campaigns for filter dropdown"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT
                    id,
                    name,
                    status,
                    (SELECT COUNT(*) FROM content_drafts WHERE campaign_id = campaigns.id AND scheduled_at IS NOT NULL) as scheduled_count
                FROM campaigns
                WHERE status = 'active'
                ORDER BY name ASC
            """)
            return cursor.fetchall()
    except Exception as e:
        st.error(f"Error fetching campaigns: {str(e)}")
        return []


def get_content_by_id(draft_id: int) -> Optional[Dict]:
    """Fetch specific content draft by ID"""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT
                    cd.id,
                    cd.type as content_type,
                    cd.content,
                    cd.status,
                    cd.scheduled_at,
                    cd.seo_score,
                    cd.created_at,
                    c.id as campaign_id,
                    c.name as campaign_name,
                    c.status as campaign_status,
                    c.target_audience,
                    c.branding_json,
                    pc.id as published_id,
                    pc.channel,
                    pc.published_at,
                    (SELECT COUNT(*) FROM media_assets WHERE draft_id = cd.id) as media_count,
                    (SELECT COUNT(*) FROM review_feedback WHERE draft_id = cd.id) as feedback_count
                FROM content_drafts cd
                LEFT JOIN campaigns c ON cd.campaign_id = c.id
                LEFT JOIN published_content pc ON cd.id = pc.draft_id
                WHERE cd.id = %s
            """, (draft_id,))

            return cursor.fetchone()
    except Exception as e:
        st.error(f"Error fetching content: {str(e)}")
        return None


def update_content_schedule(draft_id: int, new_scheduled_at: datetime) -> bool:
    """Update the scheduled_at timestamp for a content draft"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE content_drafts
                SET scheduled_at = %s
                WHERE id = %s
            """, (new_scheduled_at, draft_id))

            conn.commit()
            return True
    except Exception as e:
        st.error(f"Error updating schedule: {str(e)}")
        conn.rollback()
        return False


def main():
    """Main content calendar application"""

    # Session state initialization
    if 'selected_content_id' not in st.session_state:
        st.session_state['selected_content_id'] = None
    if 'edit_scheduled_date' not in st.session_state:
        st.session_state['edit_scheduled_date'] = None
    if 'edit_scheduled_time' not in st.session_state:
        st.session_state['edit_scheduled_time'] = None

    # Custom CSS for calendar styling
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: 700;
            color: #1E3A8A;
            margin-bottom: 1rem;
        }
        .calendar-day {
            border: 1px solid #E5E7EB;
            border-radius: 5px;
            padding: 0.5rem;
            min-height: 100px;
            background-color: #FFFFFF;
        }
        .calendar-day-header {
            font-weight: 600;
            color: #374151;
            margin-bottom: 0.5rem;
        }
        .content-item {
            background-color: #EEF2FF;
            border-left: 3px solid #6366F1;
            padding: 0.3rem;
            margin-bottom: 0.3rem;
            border-radius: 3px;
            font-size: 0.85rem;
        }
        .channel-badge {
            display: inline-block;
            padding: 0.1rem 0.4rem;
            border-radius: 3px;
            font-size: 0.7rem;
            font-weight: 600;
            margin-right: 0.2rem;
        }
        .badge-linkedin { background-color: #0A66C2; color: white; }
        .badge-twitter { background-color: #1DA1F2; color: white; }
        .badge-instagram { background-color: #E4405F; color: white; }
        .badge-wordpress { background-color: #21759B; color: white; }
        .badge-email { background-color: #EA4335; color: white; }
        </style>
    """, unsafe_allow_html=True)

    # Sidebar filters and content detail editor
    with st.sidebar:
        st.markdown("### 📅 Calendar Filters")

        # Campaign filter
        campaigns = get_campaigns_for_filter()
        campaign_options = {"All Campaigns": None}
        for camp in campaigns:
            campaign_options[f"{camp['name']} ({camp['scheduled_count']})"] = camp['id']

        selected_campaign_name = st.selectbox(
            "Campaign",
            options=list(campaign_options.keys()),
            index=0
        )
        selected_campaign_id = campaign_options[selected_campaign_name]

        # Channel filter
        channel_options = {
            "All Channels": None,
            "LinkedIn": "linkedin",
            "Twitter": "twitter",
            "Instagram": "instagram",
            "WordPress": "wordpress",
            "Email": "email"
        }
        selected_channel_name = st.selectbox(
            "Channel",
            options=list(channel_options.keys()),
            index=0
        )
        selected_channel = channel_options[selected_channel_name]

        # Month/Year selector
        st.markdown("---")
        st.markdown("### 📆 Date Range")

        current_date = datetime.now()
        selected_year = st.selectbox(
            "Year",
            options=range(current_date.year - 1, current_date.year + 2),
            index=1
        )
        selected_month = st.selectbox(
            "Month",
            options=range(1, 13),
            format_func=lambda x: calendar.month_name[x],
            index=current_date.month - 1
        )

        # Calculate date range for selected month
        first_day = datetime(selected_year, selected_month, 1)
        last_day = datetime(selected_year, selected_month, calendar.monthrange(selected_year, selected_month)[1], 23, 59, 59)

        st.markdown("---")
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        # Content Detail Editor
        if st.session_state.get('selected_content_id'):
            st.markdown("---")
            st.markdown("### ✏️ Edit Schedule")

            selected_content = get_content_by_id(st.session_state['selected_content_id'])

            if selected_content:
                st.markdown(f"**{selected_content.get('content_type', 'Content').upper()}**")
                st.caption(f"Campaign: {selected_content.get('campaign_name', 'N/A')}")

                # Display current schedule
                current_schedule = selected_content.get('scheduled_at')
                if current_schedule:
                    current_dt = pd.to_datetime(current_schedule)
                    st.info(f"Current: {current_dt.strftime('%Y-%m-%d %I:%M %p')}")

                    # Initialize edit fields if not already set
                    if st.session_state['edit_scheduled_date'] is None:
                        st.session_state['edit_scheduled_date'] = current_dt.date()
                    if st.session_state['edit_scheduled_time'] is None:
                        st.session_state['edit_scheduled_time'] = current_dt.time()
                else:
                    st.warning("No schedule set")
                    # Set defaults
                    if st.session_state['edit_scheduled_date'] is None:
                        st.session_state['edit_scheduled_date'] = datetime.now().date()
                    if st.session_state['edit_scheduled_time'] is None:
                        st.session_state['edit_scheduled_time'] = datetime.now().time()

                # Edit form
                with st.form(key="edit_schedule_form"):
                    new_date = st.date_input(
                        "Schedule Date",
                        value=st.session_state['edit_scheduled_date'],
                        key="form_date"
                    )

                    new_time = st.time_input(
                        "Schedule Time",
                        value=st.session_state['edit_scheduled_time'],
                        key="form_time"
                    )

                    # Form buttons
                    col_save, col_cancel = st.columns(2)

                    with col_save:
                        save_clicked = st.form_submit_button(
                            "💾 Save",
                            use_container_width=True,
                            type="primary"
                        )

                    with col_cancel:
                        cancel_clicked = st.form_submit_button(
                            "❌ Cancel",
                            use_container_width=True
                        )

                    # Handle form submission
                    if save_clicked:
                        # Combine date and time
                        new_scheduled_at = datetime.combine(new_date, new_time)

                        # Update database
                        if update_content_schedule(st.session_state['selected_content_id'], new_scheduled_at):
                            st.success("✅ Schedule updated successfully!")

                            # Clear cache to refresh calendar
                            st.cache_data.clear()

                            # Reset selection
                            st.session_state['selected_content_id'] = None
                            st.session_state['edit_scheduled_date'] = None
                            st.session_state['edit_scheduled_time'] = None

                            st.rerun()
                        else:
                            st.error("Failed to update schedule")

                    if cancel_clicked:
                        # Reset selection without saving
                        st.session_state['selected_content_id'] = None
                        st.session_state['edit_scheduled_date'] = None
                        st.session_state['edit_scheduled_time'] = None
                        st.rerun()

                # Show content preview
                st.markdown("---")
                st.markdown("**Content Preview:**")
                content_text = selected_content.get('content', '')
                if content_text:
                    preview_text = content_text[:200] + "..." if len(content_text) > 200 else content_text
                    st.text_area("", value=preview_text, height=150, disabled=True, key="content_preview")
                else:
                    st.caption("No content available")

                # Metadata
                st.markdown("---")
                st.markdown("**Metadata:**")
                st.caption(f"Status: {selected_content.get('status', 'unknown')}")
                if selected_content.get('channel'):
                    st.caption(f"Channel: {selected_content.get('channel', 'N/A')}")
                if selected_content.get('seo_score'):
                    st.caption(f"SEO Score: {selected_content.get('seo_score', 0)}/100")
                st.caption(f"Media: {selected_content.get('media_count', 0)} assets")
                st.caption(f"Feedback: {selected_content.get('feedback_count', 0)} reviews")
            else:
                st.error("Content not found")
                st.session_state['selected_content_id'] = None

    # Main content area
    st.markdown('<h1 class="main-header">📅 Content Calendar</h1>', unsafe_allow_html=True)
    st.markdown(f"**{calendar.month_name[selected_month]} {selected_year}** - Scheduled Content Overview")

    # Fetch scheduled content
    scheduled_content = get_scheduled_content(
        campaign_id=selected_campaign_id,
        date_from=first_day,
        date_to=last_day,
        channel=selected_channel
    )

    # Display statistics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_scheduled = len(scheduled_content) if not scheduled_content.empty else 0
        st.metric("Total Scheduled", total_scheduled)

    with col2:
        if not scheduled_content.empty:
            published_count = scheduled_content[scheduled_content['published_at'].notna()].shape[0]
        else:
            published_count = 0
        st.metric("Published", published_count)

    with col3:
        if not scheduled_content.empty:
            pending_count = scheduled_content[scheduled_content['published_at'].isna()].shape[0]
        else:
            pending_count = 0
        st.metric("Pending", pending_count)

    with col4:
        if not scheduled_content.empty and 'channel' in scheduled_content.columns:
            unique_channels = scheduled_content['channel'].dropna().nunique()
        else:
            unique_channels = 0
        st.metric("Active Channels", unique_channels)

    st.markdown("---")

    # Prepare content data for calendar grid
    content_by_date = {}
    if not scheduled_content.empty:
        scheduled_content['date'] = pd.to_datetime(scheduled_content['scheduled_at']).dt.date
        for date, items in scheduled_content.groupby('date'):
            content_by_date[date] = items.to_dict('records')

    # Generate calendar grid
    st.markdown(f"### 📆 {calendar.month_name[selected_month]} {selected_year}")

    # Get calendar matrix for the month
    cal = calendar.monthcalendar(selected_year, selected_month)

    # Display day headers
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    header_cols = st.columns(7)
    for idx, day_name in enumerate(day_names):
        with header_cols[idx]:
            st.markdown(f"**{day_name}**")

    # Display calendar grid
    for week in cal:
        week_cols = st.columns(7)
        for idx, day in enumerate(week):
            with week_cols[idx]:
                if day == 0:
                    # Empty day (from previous/next month)
                    st.markdown('<div class="calendar-day" style="background-color: #F9FAFB; min-height: 120px;"></div>', unsafe_allow_html=True)
                else:
                    # Valid day in current month
                    current_date = datetime(selected_year, selected_month, day).date()
                    day_content_list = content_by_date.get(current_date, [])

                    # Build day cell HTML
                    day_html = f'<div class="calendar-day" style="min-height: 120px;">'
                    day_html += f'<div class="calendar-day-header">{day}</div>'

                    if day_content_list:
                        # Display content items for this day
                        for item in day_content_list[:3]:  # Limit to 3 items per day for space
                            content_type = item.get('content_type', 'unknown').upper()
                            campaign_name = item.get('campaign_name', 'No Campaign')
                            channel = item.get('channel', '')

                            # Channel badge
                            channel_badge_html = ''
                            if channel:
                                channel_class = f"badge-{channel}"
                                channel_badge_html = f'<span class="channel-badge {channel_class}">{channel.upper()}</span>'

                            day_html += f'<div class="content-item">'
                            day_html += f'{channel_badge_html}'
                            day_html += f'<div style="font-weight: 600; font-size: 0.75rem;">{content_type}</div>'
                            day_html += f'<div style="font-size: 0.7rem; color: #6B7280;">{campaign_name[:20]}...</div>'
                            day_html += f'</div>'

                        # Show count if more items exist
                        if len(day_content_list) > 3:
                            day_html += f'<div style="font-size: 0.7rem; color: #6B7280; margin-top: 0.3rem;">+{len(day_content_list) - 3} more</div>'

                    day_html += '</div>'
                    st.markdown(day_html, unsafe_allow_html=True)

    # Detailed list view below calendar
    if not scheduled_content.empty:
        st.markdown("---")
        st.markdown(f"### 📋 Detailed Schedule ({len(scheduled_content)} items)")

        # Display content grouped by date
        for date in sorted(scheduled_content['date'].unique()):
            day_content = scheduled_content[scheduled_content['date'] == date]

            with st.expander(f"📅 {date.strftime('%A, %B %d, %Y')} ({len(day_content)} items)", expanded=False):
                for _, item in day_content.iterrows():
                    col_a, col_b, col_c, col_d = st.columns([3, 2, 1, 1])

                    with col_a:
                        # Content type and campaign
                        type_badge = item['content_type'].upper() if pd.notna(item['content_type']) else "UNKNOWN"
                        campaign_name = item['campaign_name'] if pd.notna(item['campaign_name']) else "No Campaign"
                        st.markdown(f"**{type_badge}** - {campaign_name}")

                        # Content preview (first 100 chars)
                        if pd.notna(item['content']):
                            content_preview = str(item['content'])[:100] + "..." if len(str(item['content'])) > 100 else str(item['content'])
                            st.caption(content_preview)

                    with col_b:
                        # Channel and time
                        if pd.notna(item['channel']):
                            channel_class = f"badge-{item['channel']}"
                            st.markdown(f'<span class="channel-badge {channel_class}">{item["channel"].upper()}</span>', unsafe_allow_html=True)

                        scheduled_time = pd.to_datetime(item['scheduled_at']).strftime('%I:%M %p')
                        st.caption(f"⏰ {scheduled_time}")

                    with col_c:
                        # Status
                        status = item['status'] if pd.notna(item['status']) else "draft"
                        status_emoji = {
                            'draft': '📝',
                            'in_review': '👀',
                            'approved': '✅',
                            'published': '🚀',
                            'rejected': '❌'
                        }
                        st.caption(f"{status_emoji.get(status, '❓')} {status}")

                    with col_d:
                        # Edit button
                        if st.button("✏️ Edit", key=f"edit_{item['id']}", use_container_width=True):
                            st.session_state['selected_content_id'] = item['id']
                            st.session_state['edit_scheduled_date'] = None
                            st.session_state['edit_scheduled_time'] = None
                            st.rerun()

                    st.markdown("---")
    else:
        st.info(f"No scheduled content found for {calendar.month_name[selected_month]} {selected_year} with the selected filters.")


if __name__ == "__main__":
    main()
