"""
Campaign Management - Create, Edit, and Manage Marketing Campaigns
Provides interface for campaign CRUD operations and content overview
"""

import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
from typing import Dict, List, Optional
import json

# Page configuration
st.set_page_config(
    page_title="Campaigns - Marketing Dashboard",
    page_icon="🎯",
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


def get_campaigns(user_id: Optional[int] = None, status: Optional[str] = None) -> List[Dict]:
    """Fetch campaigns with filters"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
                SELECT
                    c.id, c.name, c.status, c.target_audience, c.branding_json, c.created_at,
                    (SELECT COUNT(*) FROM content_drafts WHERE campaign_id = c.id) as content_count,
                    (SELECT COUNT(*) FROM content_drafts WHERE campaign_id = c.id AND status = 'published') as published_count,
                    (SELECT COUNT(*) FROM content_drafts WHERE campaign_id = c.id AND status = 'in_review') as review_count
                FROM campaigns c
                WHERE 1=1
            """
            params = []

            if user_id:
                query += " AND c.user_id = %s"
                params.append(user_id)

            if status:
                query += " AND c.status = %s"
                params.append(status)

            query += " ORDER BY c.created_at DESC"

            cursor.execute(query, params)
            return cursor.fetchall()
    except Exception as e:
        st.error(f"Error fetching campaigns: {str(e)}")
        return []


def get_campaign_details(campaign_id: int) -> Optional[Dict]:
    """Get detailed campaign information"""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT
                    c.id, c.user_id, c.name, c.status, c.target_audience,
                    c.branding_json, c.brand_voice_profile_id, c.created_at,
                    bvp.profile_name, bvp.calculated_profile,
                    (SELECT COUNT(*) FROM content_drafts WHERE campaign_id = c.id) as total_content,
                    (SELECT COUNT(*) FROM content_drafts WHERE campaign_id = c.id AND status = 'draft') as draft_count,
                    (SELECT COUNT(*) FROM content_drafts WHERE campaign_id = c.id AND status = 'in_review') as review_count,
                    (SELECT COUNT(*) FROM content_drafts WHERE campaign_id = c.id AND status = 'approved') as approved_count,
                    (SELECT COUNT(*) FROM content_drafts WHERE campaign_id = c.id AND status = 'published') as published_count
                FROM campaigns c
                LEFT JOIN brand_voice_profiles bvp ON c.brand_voice_profile_id = bvp.id
                WHERE c.id = %s
            """, (campaign_id,))
            return cursor.fetchone()
    except Exception as e:
        st.error(f"Error fetching campaign details: {str(e)}")
        return None


def get_campaign_content(campaign_id: int, status: Optional[str] = None) -> List[Dict]:
    """Get content drafts for a campaign"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
                SELECT
                    cd.id, cd.type, cd.content, cd.status, cd.seo_score, cd.created_at,
                    (SELECT COUNT(*) FROM media_assets WHERE draft_id = cd.id) as media_count,
                    (SELECT COUNT(*) FROM review_feedback WHERE draft_id = cd.id) as feedback_count,
                    pc.channel, pc.published_at
                FROM content_drafts cd
                LEFT JOIN published_content pc ON cd.id = pc.draft_id
                WHERE cd.campaign_id = %s
            """
            params = [campaign_id]

            if status:
                query += " AND cd.status = %s"
                params.append(status)

            query += " ORDER BY cd.created_at DESC"

            cursor.execute(query, params)
            return cursor.fetchall()
    except Exception as e:
        st.error(f"Error fetching campaign content: {str(e)}")
        return []


def get_brand_voice_profiles(campaign_id: Optional[int] = None) -> List[Dict]:
    """Fetch brand voice profiles, optionally filtered by campaign"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            if campaign_id:
                cursor.execute("""
                    SELECT id, campaign_id, profile_name, example_content, calculated_profile, created_at
                    FROM brand_voice_profiles
                    WHERE campaign_id = %s
                    ORDER BY created_at DESC
                """, (campaign_id,))
            else:
                cursor.execute("""
                    SELECT id, campaign_id, profile_name, example_content, calculated_profile, created_at
                    FROM brand_voice_profiles
                    ORDER BY created_at DESC
                """)
            return cursor.fetchall()
    except Exception as e:
        st.error(f"Error fetching brand voice profiles: {str(e)}")
        return []


def get_brand_voice_profile(profile_id: str) -> Optional[Dict]:
    """Get a specific brand voice profile by ID"""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, campaign_id, profile_name, example_content, calculated_profile, created_at
                FROM brand_voice_profiles
                WHERE id = %s
            """, (profile_id,))
            return cursor.fetchone()
    except Exception as e:
        st.error(f"Error fetching brand voice profile: {str(e)}")
        return None


def create_campaign(name: str, target_audience: str, branding_json: Dict,
                   user_id: int = 1, brand_voice_profile_id: Optional[str] = None) -> Optional[int]:
    """Create a new campaign"""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO campaigns (user_id, name, target_audience, branding_json, status, brand_voice_profile_id)
                VALUES (%s, %s, %s, %s, 'active', %s)
                RETURNING id
            """, (user_id, name, target_audience, json.dumps(branding_json), brand_voice_profile_id))

            campaign_id = cursor.fetchone()[0]
            conn.commit()
            return campaign_id
    except Exception as e:
        st.error(f"Error creating campaign: {str(e)}")
        conn.rollback()
        return None


def update_campaign(campaign_id: int, name: str, target_audience: str,
                   branding_json: Dict, status: str, brand_voice_profile_id: Optional[str] = None) -> bool:
    """Update an existing campaign"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE campaigns
                SET name = %s, target_audience = %s, branding_json = %s, status = %s, brand_voice_profile_id = %s
                WHERE id = %s
            """, (name, target_audience, json.dumps(branding_json), status, brand_voice_profile_id, campaign_id))

            conn.commit()
            return True
    except Exception as e:
        st.error(f"Error updating campaign: {str(e)}")
        conn.rollback()
        return False


def delete_campaign(campaign_id: int) -> bool:
    """Delete a campaign and all associated content"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            # Delete in order due to foreign key constraints
            cursor.execute("DELETE FROM review_feedback WHERE draft_id IN (SELECT id FROM content_drafts WHERE campaign_id = %s)", (campaign_id,))
            cursor.execute("DELETE FROM media_assets WHERE draft_id IN (SELECT id FROM content_drafts WHERE campaign_id = %s)", (campaign_id,))
            cursor.execute("DELETE FROM content_drafts WHERE campaign_id = %s", (campaign_id,))
            cursor.execute("DELETE FROM campaigns WHERE id = %s", (campaign_id,))

            conn.commit()
            return True
    except Exception as e:
        st.error(f"Error deleting campaign: {str(e)}")
        conn.rollback()
        return False


def main():
    """Main campaigns management application"""

    st.title("🎯 Campaign Management")
    st.markdown("Create and manage marketing campaigns")

    # Sidebar navigation
    with st.sidebar:
        st.header("⚙️ Actions")

        if st.button("➕ Create New Campaign", use_container_width=True):
            st.session_state['show_create_form'] = True

        st.markdown("---")

        # Filter by status
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "active", "paused", "completed"]
        )

        st.markdown("---")
        st.caption("Campaign Actions")
        st.caption("• Click a campaign to view details")
        st.caption("• Use Edit to modify settings")
        st.caption("• Use Delete to remove permanently")

    # Show create form if triggered
    if st.session_state.get('show_create_form', False):
        show_create_campaign_form()
        return

    # Show edit form if campaign selected for editing
    if st.session_state.get('edit_campaign_id'):
        show_edit_campaign_form(st.session_state['edit_campaign_id'])
        return

    # Show campaign details if one is selected
    if st.session_state.get('selected_campaign_id'):
        show_campaign_details(st.session_state['selected_campaign_id'])
        return

    # Main campaign list view
    st.subheader("📋 All Campaigns")

    # Fetch campaigns
    campaigns = get_campaigns(
        status=status_filter if status_filter != "All" else None
    )

    if not campaigns:
        st.info("No campaigns found. Create your first campaign to get started!")
        return

    # Display campaigns as cards
    for campaign in campaigns:
        render_campaign_card(campaign)


def render_campaign_card(campaign: Dict):
    """Render a campaign as a card"""

    # Status badge color
    status_colors = {
        "active": "🟢",
        "paused": "🟡",
        "completed": "🔵"
    }

    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

        with col1:
            st.markdown(f"### {campaign['name']}")
            st.caption(f"{status_colors.get(campaign['status'], '⚪')} {campaign['status'].upper()}")
            st.caption(f"Created: {campaign['created_at'].strftime('%Y-%m-%d')}")

        with col2:
            st.metric("Total Content", campaign['content_count'])
            st.caption(f"{campaign['published_count']} published")

        with col3:
            st.metric("In Review", campaign['review_count'])
            # Handle JSONB target_audience - display as readable string
            audience = campaign.get('target_audience') or {}
            if isinstance(audience, dict):
                audience_str = ', '.join(f"{k}: {v}" for k, v in list(audience.items())[:2])
            else:
                audience_str = str(audience)[:30]
            st.caption(f"Target: {audience_str[:40]}...")

        with col4:
            if st.button("👁️ View", key=f"view_{campaign['id']}", use_container_width=True):
                st.session_state['selected_campaign_id'] = campaign['id']
                st.rerun()

            if st.button("✏️ Edit", key=f"edit_{campaign['id']}", use_container_width=True):
                st.session_state['edit_campaign_id'] = campaign['id']
                st.rerun()

        st.markdown("---")


def show_campaign_details(campaign_id: int):
    """Show detailed view of a campaign"""

    # Back button
    if st.button("← Back to Campaigns"):
        del st.session_state['selected_campaign_id']
        st.rerun()

    # Fetch campaign details
    campaign = get_campaign_details(campaign_id)

    if not campaign:
        st.error("Campaign not found")
        return

    st.markdown("---")
    st.title(f"📊 {campaign['name']}")

    # Campaign metadata
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"**Status:** {campaign['status'].upper()}")
        st.markdown(f"**Created:** {campaign['created_at'].strftime('%Y-%m-%d %H:%M')}")

    with col2:
        # Handle JSONB target_audience
        audience = campaign.get('target_audience') or {}
        if isinstance(audience, dict):
            audience_display = ', '.join(f"{k}: {v}" for k, v in audience.items())
        else:
            audience_display = str(audience)
        st.markdown(f"**Target Audience:** {audience_display}")

    with col3:
        # Quick actions
        if st.button("✏️ Edit Campaign", use_container_width=True):
            st.session_state['edit_campaign_id'] = campaign_id
            st.rerun()

    # Metrics
    st.markdown("---")
    st.subheader("📈 Content Metrics")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Content", campaign['total_content'])
    col2.metric("Published", campaign['published_count'])
    col3.metric("In Review", campaign['review_count'])
    col4.metric("Approved", campaign['approved_count'])

    # Branding information
    st.markdown("---")
    st.subheader("🎨 Brand Guidelines")

    branding = campaign.get('branding_json') or {}

    if branding:
        col1, col2 = st.columns(2)

        with col1:
            if 'brand_voice' in branding:
                st.markdown(f"**Brand Voice:** {branding['brand_voice']}")
            if 'primary_color' in branding:
                st.markdown(f"**Primary Color:** {branding['primary_color']}")
            if 'secondary_color' in branding:
                st.markdown(f"**Secondary Color:** {branding['secondary_color']}")

        with col2:
            if 'tone' in branding:
                st.markdown(f"**Tone:** {branding['tone']}")
            if 'keywords' in branding:
                st.markdown(f"**Keywords:** {', '.join(branding['keywords'])}")

        # Display full branding JSON
        with st.expander("View Full Branding Configuration"):
            st.json(branding)
    else:
        st.info("No branding guidelines configured")

    # Brand Voice Profile
    st.markdown("---")
    st.subheader("🎤 Brand Voice Profile")

    if campaign.get('brand_voice_profile_id'):
        profile_name = campaign.get('profile_name')
        calculated_profile = campaign.get('calculated_profile') or {}

        if profile_name:
            st.markdown(f"**Active Profile:** {profile_name}")

            if calculated_profile:
                col1, col2 = st.columns(2)

                with col1:
                    if 'tone' in calculated_profile:
                        st.markdown(f"**Tone:** {calculated_profile['tone']}")
                    if 'style' in calculated_profile:
                        st.markdown(f"**Style:** {calculated_profile['style']}")

                with col2:
                    if 'formality' in calculated_profile:
                        st.markdown(f"**Formality:** {calculated_profile['formality']}")
                    if 'vocabulary_level' in calculated_profile:
                        st.markdown(f"**Vocabulary:** {calculated_profile['vocabulary_level']}")

                # Display full calculated profile
                with st.expander("View Full Brand Voice Analysis"):
                    st.json(calculated_profile)
            else:
                st.info("Profile analysis not yet available")
        else:
            st.info("Brand voice profile assigned but details not available")
    else:
        st.info("No brand voice profile assigned to this campaign")

    # Content list
    st.markdown("---")
    st.subheader("📝 Campaign Content")

    # Filter by status
    content_status_filter = st.selectbox(
        "Filter Content",
        ["All", "draft", "in_review", "approved", "published"],
        key="content_status_filter"
    )

    content_items = get_campaign_content(
        campaign_id,
        status=content_status_filter if content_status_filter != "All" else None
    )

    if content_items:
        for item in content_items:
            with st.expander(
                f"{item['type'].upper()} - {item['status'].upper()} - "
                f"{item['created_at'].strftime('%Y-%m-%d')}"
            ):
                col1, col2 = st.columns([3, 1])

                with col1:
                    # Content preview
                    preview = item['content'][:300] + "..." if len(item['content']) > 300 else item['content']
                    st.markdown(preview)

                with col2:
                    st.metric("Media Assets", item['media_count'])
                    st.metric("Feedback Count", item['feedback_count'])

                    if item['seo_score']:
                        st.metric("SEO Score", f"{item['seo_score']}/100")

                    if item['published_at']:
                        st.markdown(f"**Published:** {item['published_at'].strftime('%Y-%m-%d')}")
                        st.markdown(f"**Channel:** {item['channel'].upper()}")

                # Actions
                btn_col1, btn_col2, btn_col3 = st.columns(3)

                with btn_col1:
                    if st.button("📝 Review", key=f"review_content_{item['id']}"):
                        st.info(f"Navigate to content review for draft {item['id']}")

                with btn_col2:
                    if st.button("📊 Analytics", key=f"analytics_content_{item['id']}"):
                        st.info(f"Navigate to analytics for content {item['id']}")

                with btn_col3:
                    if st.button("🗑️ Delete", key=f"delete_content_{item['id']}"):
                        st.warning(f"Delete content {item['id']}? (Not implemented)")
    else:
        st.info("No content in this campaign yet. Generate some content to get started!")


def show_create_campaign_form():
    """Show form to create a new campaign"""

    st.title("➕ Create New Campaign")

    if st.button("← Cancel"):
        st.session_state['show_create_form'] = False
        st.rerun()

    st.markdown("---")

    with st.form("create_campaign_form"):
        # Basic info
        st.subheader("📋 Basic Information")

        name = st.text_input("Campaign Name *", placeholder="e.g., Q1 2024 Product Launch")

        target_audience = st.text_area(
            "Target Audience *",
            placeholder="Describe your target audience: demographics, interests, pain points...",
            height=100
        )

        # Branding
        st.subheader("🎨 Brand Guidelines")

        col1, col2 = st.columns(2)

        with col1:
            brand_voice = st.selectbox(
                "Brand Voice",
                ["Professional", "Casual", "Friendly", "Authoritative", "Humorous"]
            )

            tone = st.selectbox(
                "Tone",
                ["Informative", "Persuasive", "Inspirational", "Educational", "Conversational"]
            )

            primary_color = st.color_picker("Primary Brand Color", "#667eea")

        with col2:
            keywords_input = st.text_area(
                "Keywords (one per line)",
                placeholder="innovation\ntechnology\nsolutions",
                height=100
            )

            secondary_color = st.color_picker("Secondary Brand Color", "#f093fb")

        # Advanced branding (optional)
        with st.expander("Advanced Brand Settings"):
            logo_url = st.text_input("Logo URL", placeholder="https://example.com/logo.png")
            website_url = st.text_input("Website URL", placeholder="https://example.com")
            tagline = st.text_input("Brand Tagline", placeholder="Your brand's tagline")

        # Brand Voice Profile
        st.subheader("🎤 Brand Voice Profile (Optional)")

        # Fetch available brand voice profiles
        all_profiles = get_brand_voice_profiles()

        if all_profiles:
            profile_options = {"None": None}
            profile_options.update({p['profile_name']: str(p['id']) for p in all_profiles})

            selected_profile_name = st.selectbox(
                "Select Brand Voice Profile",
                options=list(profile_options.keys()),
                help="Choose a trained brand voice profile to use for this campaign"
            )

            selected_profile_id = profile_options[selected_profile_name]

            # Show profile details if selected
            if selected_profile_id:
                selected_profile = next((p for p in all_profiles if str(p['id']) == selected_profile_id), None)
                if selected_profile and selected_profile.get('calculated_profile'):
                    with st.expander("📊 View Profile Details"):
                        st.json(selected_profile['calculated_profile'])
        else:
            selected_profile_id = None
            st.info("No brand voice profiles available. Create one from the Brand Voice page first.")

        # Submit
        st.markdown("---")
        submitted = st.form_submit_button("✅ Create Campaign", use_container_width=True)

        if submitted:
            # Validate
            if not name or not target_audience:
                st.error("Please fill in all required fields")
                return

            # Parse keywords
            keywords = [k.strip() for k in keywords_input.split('\n') if k.strip()]

            # Build branding JSON
            branding_json = {
                "brand_voice": brand_voice,
                "tone": tone,
                "primary_color": primary_color,
                "secondary_color": secondary_color,
                "keywords": keywords
            }

            if logo_url:
                branding_json["logo_url"] = logo_url
            if website_url:
                branding_json["website_url"] = website_url
            if tagline:
                branding_json["tagline"] = tagline

            # Create campaign
            campaign_id = create_campaign(
                name=name,
                target_audience=target_audience,
                branding_json=branding_json,
                user_id=st.session_state.get('user_id', 1),
                brand_voice_profile_id=selected_profile_id
            )

            if campaign_id:
                st.success(f"Campaign '{name}' created successfully!")
                st.session_state['show_create_form'] = False
                st.session_state['selected_campaign_id'] = campaign_id
                st.rerun()
            else:
                st.error("Failed to create campaign")


def show_edit_campaign_form(campaign_id: int):
    """Show form to edit an existing campaign"""

    # Fetch campaign
    campaign = get_campaign_details(campaign_id)

    if not campaign:
        st.error("Campaign not found")
        return

    st.title(f"✏️ Edit Campaign: {campaign['name']}")

    if st.button("← Cancel"):
        del st.session_state['edit_campaign_id']
        st.rerun()

    st.markdown("---")

    branding = campaign.get('branding_json') or {}

    with st.form("edit_campaign_form"):
        # Basic info
        st.subheader("📋 Basic Information")

        name = st.text_input("Campaign Name *", value=campaign['name'])

        # Convert JSONB to string for editing
        existing_audience = campaign.get('target_audience') or {}
        if isinstance(existing_audience, dict):
            audience_text = json.dumps(existing_audience, indent=2)
        else:
            audience_text = str(existing_audience)
        target_audience = st.text_area(
            "Target Audience *",
            value=audience_text,
            height=100
        )

        status = st.selectbox(
            "Status",
            ["active", "paused", "completed"],
            index=["active", "paused", "completed"].index(campaign['status'])
        )

        # Branding
        st.subheader("🎨 Brand Guidelines")

        col1, col2 = st.columns(2)

        with col1:
            brand_voice = st.selectbox(
                "Brand Voice",
                ["Professional", "Casual", "Friendly", "Authoritative", "Humorous"],
                index=["Professional", "Casual", "Friendly", "Authoritative", "Humorous"].index(
                    branding.get("brand_voice", "Professional")
                )
            )

            tone = st.selectbox(
                "Tone",
                ["Informative", "Persuasive", "Inspirational", "Educational", "Conversational"],
                index=["Informative", "Persuasive", "Inspirational", "Educational", "Conversational"].index(
                    branding.get("tone", "Informative")
                )
            )

            primary_color = st.color_picker(
                "Primary Brand Color",
                branding.get("primary_color", "#667eea")
            )

        with col2:
            keywords_input = st.text_area(
                "Keywords (one per line)",
                value='\n'.join(branding.get("keywords", [])),
                height=100
            )

            secondary_color = st.color_picker(
                "Secondary Brand Color",
                branding.get("secondary_color", "#f093fb")
            )

        # Advanced branding
        with st.expander("Advanced Brand Settings"):
            logo_url = st.text_input("Logo URL", value=branding.get("logo_url", ""))
            website_url = st.text_input("Website URL", value=branding.get("website_url", ""))
            tagline = st.text_input("Brand Tagline", value=branding.get("tagline", ""))

        # Brand Voice Profile
        st.subheader("🎤 Brand Voice Profile (Optional)")

        # Fetch available brand voice profiles
        all_profiles = get_brand_voice_profiles()

        if all_profiles:
            profile_options = {"None": None}
            profile_options.update({p['profile_name']: str(p['id']) for p in all_profiles})

            # Get current profile ID as string for comparison
            current_profile_id = str(campaign.get('brand_voice_profile_id')) if campaign.get('brand_voice_profile_id') else None

            # Find current profile name
            current_profile_name = "None"
            if current_profile_id:
                for name, pid in profile_options.items():
                    if pid == current_profile_id:
                        current_profile_name = name
                        break

            selected_profile_name = st.selectbox(
                "Select Brand Voice Profile",
                options=list(profile_options.keys()),
                index=list(profile_options.keys()).index(current_profile_name),
                help="Choose a trained brand voice profile to use for this campaign"
            )

            selected_profile_id = profile_options[selected_profile_name]

            # Show profile details if selected
            if selected_profile_id:
                selected_profile = next((p for p in all_profiles if str(p['id']) == selected_profile_id), None)
                if selected_profile and selected_profile.get('calculated_profile'):
                    with st.expander("📊 View Profile Details"):
                        st.json(selected_profile['calculated_profile'])
        else:
            selected_profile_id = None
            st.info("No brand voice profiles available. Create one from the Brand Voice page first.")

        # Submit
        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            submitted = st.form_submit_button("✅ Save Changes", use_container_width=True)

        with col2:
            delete_btn = st.form_submit_button("🗑️ Delete Campaign", use_container_width=True, type="secondary")

        if submitted:
            # Validate
            if not name or not target_audience:
                st.error("Please fill in all required fields")
                return

            # Parse keywords
            keywords = [k.strip() for k in keywords_input.split('\n') if k.strip()]

            # Build branding JSON
            branding_json = {
                "brand_voice": brand_voice,
                "tone": tone,
                "primary_color": primary_color,
                "secondary_color": secondary_color,
                "keywords": keywords
            }

            if logo_url:
                branding_json["logo_url"] = logo_url
            if website_url:
                branding_json["website_url"] = website_url
            if tagline:
                branding_json["tagline"] = tagline

            # Update campaign
            if update_campaign(campaign_id, name, target_audience, branding_json, status, selected_profile_id):
                st.success("Campaign updated successfully!")
                del st.session_state['edit_campaign_id']
                st.session_state['selected_campaign_id'] = campaign_id
                st.rerun()
            else:
                st.error("Failed to update campaign")

        if delete_btn:
            # Confirm deletion
            st.warning(f"⚠️ Are you sure you want to delete campaign '{campaign['name']}'?")
            st.caption("This will permanently delete the campaign and all associated content.")

            confirm_col1, confirm_col2 = st.columns(2)

            with confirm_col1:
                if st.button("✅ Yes, Delete", key="confirm_delete"):
                    if delete_campaign(campaign_id):
                        st.success("Campaign deleted successfully")
                        del st.session_state['edit_campaign_id']
                        st.rerun()
                    else:
                        st.error("Failed to delete campaign")

            with confirm_col2:
                if st.button("❌ Cancel", key="cancel_delete"):
                    st.info("Deletion cancelled")


if __name__ == "__main__":
    main()
