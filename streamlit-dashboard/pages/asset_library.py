"""
Asset Library - Search, Browse, and Reuse Media Assets
Provides interface for finding and reusing previously generated images and videos
"""

import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
from typing import Dict, List, Optional
import requests
from urllib.parse import urlencode

# Page configuration
st.set_page_config(
    page_title="Asset Library - Marketing Dashboard",
    page_icon="📚",
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

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://n8n:5678/webhook")


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


def search_assets(search_query: str = "", asset_type: Optional[str] = None,
                 provider: Optional[str] = None, date_from: Optional[datetime] = None,
                 date_to: Optional[datetime] = None, campaign_id: Optional[int] = None,
                 limit: int = 50) -> List[Dict]:
    """Search media assets with filters"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
                SELECT
                    ma.id, ma.type, ma.file_path, ma.url, ma.prompt,
                    ma.api_provider, ma.metadata_json, ma.created_at,
                    cd.id as draft_id, cd.type as content_type,
                    c.id as campaign_id, c.name as campaign_name,
                    (SELECT COUNT(*) FROM media_edits WHERE asset_id = ma.id) as edit_count,
                    (SELECT COUNT(*) FROM published_content pc
                     JOIN content_drafts cd2 ON pc.draft_id = cd2.id
                     WHERE cd2.id = ma.draft_id) as usage_count
                FROM media_assets ma
                JOIN content_drafts cd ON ma.draft_id = cd.id
                JOIN campaigns c ON cd.campaign_id = c.id
                WHERE 1=1
            """
            params = []

            # Search query filter (prompt or campaign name)
            if search_query:
                query += " AND (ma.prompt ILIKE %s OR c.name ILIKE %s)"
                params.extend([f"%{search_query}%", f"%{search_query}%"])

            # Asset type filter
            if asset_type:
                query += " AND ma.type = %s"
                params.append(asset_type)

            # Provider filter
            if provider:
                query += " AND ma.api_provider = %s"
                params.append(provider)

            # Date range filter
            if date_from:
                query += " AND ma.created_at >= %s"
                params.append(date_from)
            if date_to:
                query += " AND ma.created_at <= %s"
                params.append(date_to)

            # Campaign filter
            if campaign_id:
                query += " AND c.id = %s"
                params.append(campaign_id)

            query += " ORDER BY ma.created_at DESC LIMIT %s"
            params.append(limit)

            cursor.execute(query, params)
            return cursor.fetchall()
    except Exception as e:
        st.error(f"Error searching assets: {str(e)}")
        return []


def get_asset_usage(asset_id: int) -> List[Dict]:
    """Get all published content using this asset"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT
                    pc.channel, pc.url as published_url, pc.published_at,
                    em.views, em.clicks, em.shares, em.conversions,
                    cd.type as content_type, cd.content
                FROM published_content pc
                JOIN content_drafts cd ON pc.draft_id = cd.id
                JOIN media_assets ma ON ma.draft_id = cd.id
                LEFT JOIN engagement_metrics em ON em.content_id = pc.id
                WHERE ma.id = %s
                ORDER BY pc.published_at DESC
            """, (asset_id,))
            return cursor.fetchall()
    except Exception as e:
        st.error(f"Error fetching asset usage: {str(e)}")
        return []


def get_asset_edits(asset_id: int) -> List[Dict]:
    """Get edit history for an asset"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, edit_type, edit_params, edited_file_path, created_at
                FROM media_edits
                WHERE asset_id = %s
                ORDER BY created_at DESC
            """, (asset_id,))
            return cursor.fetchall()
    except Exception as e:
        st.error(f"Error fetching edit history: {str(e)}")
        return []


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


def attach_asset_to_draft(asset_id: int, draft_id: int) -> bool:
    """Create a reference to reuse an existing asset in a new draft"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            # Get original asset details
            cursor.execute("""
                SELECT type, file_path, url, prompt, api_provider, metadata_json
                FROM media_assets
                WHERE id = %s
            """, (asset_id,))

            original = cursor.fetchone()
            if not original:
                return False

            # Create new asset record linked to new draft
            cursor.execute("""
                INSERT INTO media_assets
                (draft_id, type, file_path, url, prompt, api_provider, metadata_json)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (draft_id, original[0], original[1], original[2],
                  original[3], original[4], original[5]))

            conn.commit()
            return True
    except Exception as e:
        st.error(f"Error attaching asset: {str(e)}")
        conn.rollback()
        return False


def main():
    """Main asset library application"""

    # Custom CSS
    st.markdown("""
        <style>
        .asset-card {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .asset-card:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            border-color: #667eea;
        }
        .asset-thumbnail {
            width: 100%;
            border-radius: 4px;
            margin-bottom: 0.5rem;
        }
        .asset-meta {
            font-size: 0.85rem;
            color: #666;
        }
        .usage-badge {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-right: 0.5rem;
        }
        .usage-high {
            background: #dcfce7;
            color: #166534;
        }
        .usage-medium {
            background: #fef9c3;
            color: #854d0e;
        }
        .usage-low {
            background: #e5e7eb;
            color: #374151;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("📚 Asset Library")
    st.markdown("Search, browse, and reuse previously generated media assets")

    # Sidebar filters
    with st.sidebar:
        st.header("🔍 Filters")

        # Search query
        search_query = st.text_input("Search", placeholder="Keywords in prompt or campaign...", key="search")

        # Asset type filter
        asset_type = st.selectbox(
            "Asset Type",
            ["All", "image", "video"],
            key="asset_type"
        )

        # Provider filter
        provider = st.selectbox(
            "Provider",
            ["All", "dalle3", "midjourney", "runway", "pika", "stable_diffusion"],
            key="provider"
        )

        # Date range
        st.markdown("**Date Range**")
        date_from = st.date_input("From", value=None, key="date_from")
        date_to = st.date_input("To", value=None, key="date_to")

        # Campaign filter
        campaigns = get_campaigns()
        campaign_options = ["All"] + [c['name'] for c in campaigns]
        campaign_filter = st.selectbox("Campaign", campaign_options, key="campaign")

        # View mode
        st.markdown("---")
        st.markdown("**View Mode**")
        view_mode = st.radio("", ["Grid", "List"], horizontal=True, key="view_mode")

        # Results per page
        limit = st.slider("Results", 10, 100, 50, 10, key="limit")

        # Apply filters button
        apply_filters = st.button("🔍 Apply Filters", use_container_width=True)

    # Get filtered assets
    campaign_id = None
    if campaign_filter != "All":
        matching_campaign = next((c for c in campaigns if c['name'] == campaign_filter), None)
        if matching_campaign:
            campaign_id = matching_campaign['id']

    assets = search_assets(
        search_query=search_query if search_query else "",
        asset_type=asset_type if asset_type != "All" else None,
        provider=provider if provider != "All" else None,
        date_from=datetime.combine(date_from, datetime.min.time()) if date_from else None,
        date_to=datetime.combine(date_to, datetime.max.time()) if date_to else None,
        campaign_id=campaign_id,
        limit=limit
    )

    # Results header
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"### Found {len(assets)} assets")
    with col2:
        # Batch selection
        if st.button("Select All", key="select_all"):
            st.session_state['selected_assets'] = [a['id'] for a in assets]
    with col3:
        # Clear selection
        if st.button("Clear Selection", key="clear_selection"):
            st.session_state['selected_assets'] = []

    if not assets:
        st.info("No assets found. Try adjusting your filters.")
        return

    # Initialize selected assets in session state
    if 'selected_assets' not in st.session_state:
        st.session_state['selected_assets'] = []

    # Display assets
    if view_mode == "Grid":
        # Grid view (3 columns)
        cols_per_row = 3
        for i in range(0, len(assets), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < len(assets):
                    asset = assets[i + j]
                    with col:
                        render_asset_card(asset)
    else:
        # List view
        for asset in assets:
            render_asset_list_item(asset)

    # Batch actions (if assets selected)
    if st.session_state.get('selected_assets'):
        st.markdown("---")
        st.subheader(f"Batch Actions ({len(st.session_state['selected_assets'])} selected)")

        col1, col2, col3 = st.columns(3)

        with col1:
            # Attach to draft
            all_drafts = get_all_drafts()
            draft_options = [f"{d['id']}: {d['type']} - {d['campaign_name']}" for d in all_drafts]

            if draft_options:
                selected_draft = st.selectbox("Attach to Draft", draft_options, key="batch_draft")
                if st.button("📎 Attach Selected", use_container_width=True):
                    draft_id = int(selected_draft.split(":")[0])
                    success_count = 0
                    for asset_id in st.session_state['selected_assets']:
                        if attach_asset_to_draft(asset_id, draft_id):
                            success_count += 1
                    st.success(f"Attached {success_count} assets to draft {draft_id}")
                    st.session_state['selected_assets'] = []
                    st.rerun()

        with col2:
            # Download batch
            if st.button("💾 Download Selected", use_container_width=True):
                st.info("Batch download will be implemented via ZIP archive")

        with col3:
            # Export metadata
            if st.button("📄 Export Metadata", use_container_width=True):
                st.info("Metadata export will be implemented as CSV")


def render_asset_card(asset: Dict):
    """Render asset as card in grid view"""

    # Checkbox for selection
    is_selected = asset['id'] in st.session_state.get('selected_assets', [])
    selected = st.checkbox(
        "Select",
        value=is_selected,
        key=f"select_{asset['id']}",
        label_visibility="collapsed"
    )

    if selected and asset['id'] not in st.session_state.get('selected_assets', []):
        st.session_state['selected_assets'].append(asset['id'])
    elif not selected and asset['id'] in st.session_state.get('selected_assets', []):
        st.session_state['selected_assets'].remove(asset['id'])

    # Asset thumbnail
    if asset['url']:
        st.image(asset['url'])
    else:
        st.markdown(f"**{asset['type'].upper()}**")
        st.caption(f"No preview available")

    # Asset metadata
    st.caption(f"**{asset['campaign_name']}**")
    st.caption(f"{asset['type']} • {asset['api_provider']}")

    # Usage badge
    usage_count = asset.get('usage_count', 0)
    if usage_count >= 5:
        badge_class = "usage-high"
    elif usage_count >= 2:
        badge_class = "usage-medium"
    else:
        badge_class = "usage-low"

    st.markdown(
        f'<span class="usage-badge {badge_class}">Used {usage_count}x</span>',
        unsafe_allow_html=True
    )

    # View details button
    if st.button("View Details", key=f"view_{asset['id']}", use_container_width=True):
        st.session_state['selected_asset_id'] = asset['id']
        st.rerun()


def render_asset_list_item(asset: Dict):
    """Render asset as list item"""

    with st.container():
        col1, col2, col3, col4 = st.columns([0.5, 2, 3, 2])

        with col1:
            # Selection checkbox
            is_selected = asset['id'] in st.session_state.get('selected_assets', [])
            selected = st.checkbox(
                "Select",
                value=is_selected,
                key=f"select_list_{asset['id']}",
                label_visibility="collapsed"
            )

            if selected and asset['id'] not in st.session_state.get('selected_assets', []):
                st.session_state['selected_assets'].append(asset['id'])
            elif not selected and asset['id'] in st.session_state.get('selected_assets', []):
                st.session_state['selected_assets'].remove(asset['id'])

        with col2:
            # Thumbnail
            if asset['url']:
                st.image(asset['url'], width=150)
            else:
                st.markdown(f"**{asset['type'].upper()}**")

        with col3:
            # Details
            st.markdown(f"**{asset['campaign_name']}**")
            st.caption(f"Type: {asset['type']} • Provider: {asset['api_provider']}")
            st.caption(f"Created: {asset['created_at'].strftime('%Y-%m-%d %H:%M')}")

            # Prompt preview
            if asset['prompt']:
                prompt_preview = asset['prompt'][:100] + "..." if len(asset['prompt']) > 100 else asset['prompt']
                st.caption(f"Prompt: {prompt_preview}")

        with col4:
            # Usage stats
            usage_count = asset.get('usage_count', 0)
            edit_count = asset.get('edit_count', 0)

            st.metric("Used", usage_count)
            st.caption(f"{edit_count} edits")

            if st.button("View Details", key=f"view_list_{asset['id']}", use_container_width=True):
                st.session_state['selected_asset_id'] = asset['id']
                st.rerun()

        st.markdown("---")


def get_all_drafts() -> List[Dict]:
    """Get all content drafts for batch attachment"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT cd.id, cd.type, c.name as campaign_name
                FROM content_drafts cd
                JOIN campaigns c ON cd.campaign_id = c.id
                WHERE cd.status IN ('draft', 'in_review')
                ORDER BY cd.created_at DESC
                LIMIT 50
            """)
            return cursor.fetchall()
    except Exception as e:
        st.error(f"Error fetching drafts: {str(e)}")
        return []


# Asset detail view (modal-like)
if st.session_state.get('selected_asset_id'):
    asset_id = st.session_state['selected_asset_id']

    # Get asset details
    conn = get_db_connection()
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT
                    ma.id, ma.type, ma.file_path, ma.url, ma.prompt,
                    ma.api_provider, ma.metadata_json, ma.created_at,
                    cd.id as draft_id, cd.type as content_type, cd.content,
                    c.id as campaign_id, c.name as campaign_name
                FROM media_assets ma
                JOIN content_drafts cd ON ma.draft_id = cd.id
                JOIN campaigns c ON cd.campaign_id = c.id
                WHERE ma.id = %s
            """, (asset_id,))

            asset_detail = cursor.fetchone()

    if asset_detail:
        # Back button
        if st.button("← Back to Library"):
            del st.session_state['selected_asset_id']
            st.rerun()

        st.markdown("---")
        st.title(f"{asset_detail['type'].upper()} Asset Details")

        # Main content
        col1, col2 = st.columns([2, 1])

        with col1:
            # Asset preview
            st.subheader("Preview")
            if asset_detail['url']:
                if asset_detail['type'] == 'image':
                    st.image(asset_detail['url'])
                elif asset_detail['type'] == 'video':
                    st.video(asset_detail['url'])
            else:
                st.info("No preview available")

            # Generation prompt
            st.subheader("Generation Prompt")
            st.text_area("", value=asset_detail['prompt'] or "No prompt available", height=100, disabled=True, label_visibility="collapsed")

        with col2:
            # Metadata
            st.subheader("Metadata")
            st.markdown(f"**Campaign:** {asset_detail['campaign_name']}")
            st.markdown(f"**Provider:** {asset_detail['api_provider']}")
            st.markdown(f"**Created:** {asset_detail['created_at'].strftime('%Y-%m-%d %H:%M')}")

            metadata = asset_detail.get('metadata_json') or {}
            if metadata:
                if 'dimensions' in metadata:
                    st.markdown(f"**Dimensions:** {metadata['dimensions'].get('width')}x{metadata['dimensions'].get('height')}")
                if 'duration' in metadata:
                    st.markdown(f"**Duration:** {metadata['duration']}s")
                if 'format' in metadata:
                    st.markdown(f"**Format:** {metadata['format']}")
                if 'size_bytes' in metadata:
                    size_mb = metadata['size_bytes'] / (1024 * 1024)
                    st.markdown(f"**Size:** {size_mb:.2f} MB")

            st.markdown("---")

            # Actions
            st.subheader("Actions")

            # Attach to draft
            all_drafts = get_all_drafts()
            if all_drafts:
                draft_options = [f"{d['id']}: {d['type']} - {d['campaign_name']}" for d in all_drafts]
                selected_draft = st.selectbox("Attach to Draft", draft_options, key="detail_draft")

                if st.button("📎 Attach to Draft", use_container_width=True):
                    draft_id = int(selected_draft.split(":")[0])
                    if attach_asset_to_draft(asset_id, draft_id):
                        st.success(f"Attached asset to draft {draft_id}")
                    else:
                        st.error("Failed to attach asset")

            # Download
            if st.button("💾 Download", use_container_width=True):
                st.info(f"Download: {asset_detail['url']}")

        # Tabs for additional info
        tab1, tab2 = st.tabs(["📊 Usage Analytics", "✏️ Edit History"])

        with tab1:
            # Usage analytics
            st.subheader("Where This Asset Was Published")

            usage = get_asset_usage(asset_id)

            if usage:
                for pub in usage:
                    with st.expander(f"{pub['channel'].upper()} - {pub['published_at'].strftime('%Y-%m-%d')}"):
                        st.markdown(f"**URL:** [{pub['published_url']}]({pub['published_url']})")
                        st.markdown(f"**Content Type:** {pub['content_type']}")

                        # Engagement metrics
                        if pub.get('views') is not None:
                            col1, col2, col3, col4 = st.columns(4)
                            col1.metric("Views", pub['views'] or 0)
                            col2.metric("Clicks", pub['clicks'] or 0)
                            col3.metric("Shares", pub['shares'] or 0)
                            col4.metric("Conversions", pub['conversions'] or 0)
                        else:
                            st.caption("No engagement data yet")
            else:
                st.info("This asset has not been published yet")

        with tab2:
            # Edit history
            st.subheader("Edit History")

            edits = get_asset_edits(asset_id)

            if edits:
                for edit in edits:
                    with st.expander(f"{edit['edit_type']} - {edit['created_at'].strftime('%Y-%m-%d %H:%M')}"):
                        st.json(edit['edit_params'])
                        if edit['edited_file_path']:
                            st.caption(f"Output: {edit['edited_file_path']}")
            else:
                st.info("No edits have been made to this asset")


if __name__ == "__main__":
    main()
