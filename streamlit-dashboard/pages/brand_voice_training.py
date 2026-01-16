"""
Brand Voice Training - Upload and Analyze Brand Voice Examples
Interface for training AI to match your brand's unique voice and style
"""

import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from typing import Dict, List, Optional
import json
import requests

# Page configuration
st.set_page_config(
    page_title="Brand Voice Training - Marketing Dashboard",
    page_icon="🎙️",
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


def get_campaigns() -> List[Dict]:
    """Fetch all campaigns for selection"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, name, status
                FROM campaigns
                WHERE status IN ('active', 'paused')
                ORDER BY name ASC
            """)
            return cursor.fetchall()
    except Exception as e:
        st.error(f"Error fetching campaigns: {str(e)}")
        return []


def get_brand_voice_profiles(campaign_id: Optional[str] = None) -> List[Dict]:
    """Fetch brand voice profiles"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            if campaign_id:
                cursor.execute("""
                    SELECT bvp.id, bvp.campaign_id, bvp.profile_name,
                           bvp.example_content, bvp.calculated_profile, bvp.created_at,
                           c.name as campaign_name
                    FROM brand_voice_profiles bvp
                    JOIN campaigns c ON bvp.campaign_id = c.id
                    WHERE bvp.campaign_id = %s
                    ORDER BY bvp.created_at DESC
                """, (campaign_id,))
            else:
                cursor.execute("""
                    SELECT bvp.id, bvp.campaign_id, bvp.profile_name,
                           bvp.example_content, bvp.calculated_profile, bvp.created_at,
                           c.name as campaign_name
                    FROM brand_voice_profiles bvp
                    JOIN campaigns c ON bvp.campaign_id = c.id
                    ORDER BY bvp.created_at DESC
                """)
            return cursor.fetchall()
    except Exception as e:
        st.error(f"Error fetching brand voice profiles: {str(e)}")
        return []


def create_brand_voice_profile(campaign_id: str, profile_name: str,
                               example_content: str) -> Optional[str]:
    """Create a new brand voice profile"""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO brand_voice_profiles (campaign_id, profile_name, example_content)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (campaign_id, profile_name, example_content))

            profile_id = cursor.fetchone()[0]
            conn.commit()
            return profile_id
    except Exception as e:
        st.error(f"Error creating brand voice profile: {str(e)}")
        conn.rollback()
        return None


def update_brand_voice_analysis(profile_id: str, calculated_profile: Dict) -> bool:
    """Update brand voice profile with AI analysis"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE brand_voice_profiles
                SET calculated_profile = %s
                WHERE id = %s
            """, (json.dumps(calculated_profile), profile_id))

            conn.commit()
            return True
    except Exception as e:
        st.error(f"Error updating brand voice analysis: {str(e)}")
        conn.rollback()
        return False


def delete_brand_voice_profile(profile_id: str) -> bool:
    """Delete a brand voice profile"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM brand_voice_profiles WHERE id = %s", (profile_id,))
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Error deleting brand voice profile: {str(e)}")
        conn.rollback()
        return False


def trigger_voice_analysis(profile_id: str, example_content: str) -> Optional[Dict]:
    """Trigger n8n workflow for brand voice analysis"""
    try:
        response = requests.post(
            f"{N8N_WEBHOOK_URL}/brand-voice-analysis",
            json={
                "profile_id": profile_id,
                "example_content": example_content
            },
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error triggering voice analysis: {str(e)}")
        return None


def initialize_session_state():
    """Initialize session state"""
    if 'show_upload_form' not in st.session_state:
        st.session_state['show_upload_form'] = False

    if 'selected_profile_id' not in st.session_state:
        st.session_state['selected_profile_id'] = None


def main():
    """Main brand voice training application"""

    initialize_session_state()

    st.title("🎙️ Brand Voice Training")
    st.markdown("Upload examples of your brand's writing to train AI content generation")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Actions")

        if st.button("➕ Upload Training Example", use_container_width=True):
            st.session_state['show_upload_form'] = True
            st.session_state['selected_profile_id'] = None

        st.markdown("---")

        # Campaign filter
        campaigns = get_campaigns()
        campaign_options = ["All Campaigns"] + [c['name'] for c in campaigns]
        selected_campaign_name = st.selectbox("Filter by Campaign", campaign_options)

        if selected_campaign_name != "All Campaigns":
            selected_campaign = next(c for c in campaigns if c['name'] == selected_campaign_name)
            campaign_filter = selected_campaign['id']
        else:
            campaign_filter = None

        st.markdown("---")
        st.caption("📋 Training Guidelines")
        st.caption("• Upload 3-5 examples minimum")
        st.caption("• Use your best content")
        st.caption("• Include variety of formats")
        st.caption("• Analyze to extract patterns")

    # Show upload form if triggered
    if st.session_state.get('show_upload_form', False):
        show_upload_form(campaigns)
        return

    # Show profile details if one is selected
    if st.session_state.get('selected_profile_id'):
        show_profile_details(st.session_state['selected_profile_id'])
        return

    # Main list view
    st.subheader("📚 Training Examples")

    profiles = get_brand_voice_profiles(campaign_filter)

    if not profiles:
        st.info("No training examples yet. Upload your first example to get started!")
        return

    # Display profiles as cards
    for profile in profiles:
        render_profile_card(profile)


def render_profile_card(profile: Dict):
    """Render a brand voice profile as a card"""

    # Determine if analyzed
    has_analysis = profile.get('calculated_profile') is not None
    status_icon = "✅" if has_analysis else "⏳"
    status_text = "Analyzed" if has_analysis else "Pending Analysis"

    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

        with col1:
            st.markdown(f"### {profile['profile_name']}")
            st.caption(f"{status_icon} {status_text}")
            st.caption(f"Campaign: {profile['campaign_name']}")

        with col2:
            st.caption(f"Created: {profile['created_at'].strftime('%Y-%m-%d')}")
            content_length = len(profile['example_content']) if profile['example_content'] else 0
            st.caption(f"Content: {content_length} characters")

        with col3:
            if has_analysis:
                analysis = profile['calculated_profile']
                if isinstance(analysis, str):
                    analysis = json.loads(analysis)

                tone = analysis.get('tone', 'N/A')
                st.metric("Tone", tone)

        with col4:
            if st.button("👁️ View", key=f"view_{profile['id']}", use_container_width=True):
                st.session_state['selected_profile_id'] = profile['id']
                st.rerun()

            if not has_analysis:
                if st.button("🔍 Analyze", key=f"analyze_{profile['id']}", use_container_width=True):
                    with st.spinner("Analyzing brand voice..."):
                        result = trigger_voice_analysis(
                            str(profile['id']),
                            profile['example_content']
                        )

                        if result:
                            st.success("Analysis complete!")
                            st.rerun()
                        else:
                            st.warning("Analysis queued - check back in a moment")

        st.markdown("---")


def show_upload_form(campaigns: List[Dict]):
    """Show form to upload a new training example"""

    st.title("➕ Upload Training Example")

    if st.button("← Back"):
        st.session_state['show_upload_form'] = False
        st.rerun()

    st.markdown("---")

    with st.form("upload_form"):
        st.subheader("📝 Example Details")

        # Campaign selection
        campaign_names = [c['name'] for c in campaigns]
        if not campaign_names:
            st.error("No campaigns found. Please create a campaign first.")
            return

        selected_campaign_name = st.selectbox(
            "Campaign *",
            campaign_names,
            help="Select the campaign this example belongs to"
        )

        selected_campaign = next(c for c in campaigns if c['name'] == selected_campaign_name)

        # Profile name
        profile_name = st.text_input(
            "Example Name *",
            placeholder="e.g., LinkedIn Post - Product Launch",
            help="A descriptive name for this training example"
        )

        # Example content
        example_content = st.text_area(
            "Example Content *",
            placeholder="Paste your example content here...\n\nThis should be representative of your brand's voice and style.",
            height=300,
            help="Paste the full content you want to use as a training example"
        )

        # Character count
        char_count = len(example_content)
        st.caption(f"Characters: {char_count} (recommended: 200+)")

        st.markdown("---")

        col1, col2 = st.columns([3, 1])

        with col1:
            st.info("💡 **Tip:** Use high-quality examples that best represent your brand voice for optimal results")

        with col2:
            submitted = st.form_submit_button("✅ Upload", use_container_width=True)

        if submitted:
            # Validate
            if not profile_name or not example_content:
                st.error("Please fill in all required fields")
                return

            if char_count < 50:
                st.error("Example content is too short. Please provide at least 50 characters.")
                return

            # Create profile
            profile_id = create_brand_voice_profile(
                campaign_id=str(selected_campaign['id']),
                profile_name=profile_name,
                example_content=example_content
            )

            if profile_id:
                st.success(f"Training example '{profile_name}' uploaded successfully!")

                # Ask if they want to analyze now
                if st.button("🔍 Analyze Now", use_container_width=True):
                    with st.spinner("Analyzing brand voice..."):
                        result = trigger_voice_analysis(profile_id, example_content)

                        if result:
                            st.success("Analysis complete!")
                        else:
                            st.info("Analysis queued - you can view results shortly")

                st.session_state['show_upload_form'] = False
                st.rerun()
            else:
                st.error("Failed to upload training example")


def show_profile_details(profile_id: str):
    """Show detailed view of a brand voice profile"""

    # Back button
    if st.button("← Back to Training Examples"):
        st.session_state['selected_profile_id'] = None
        st.rerun()

    # Fetch profile
    profiles = get_brand_voice_profiles()
    profile = next((p for p in profiles if str(p['id']) == str(profile_id)), None)

    if not profile:
        st.error("Training example not found")
        return

    st.markdown("---")
    st.title(f"🎙️ {profile['profile_name']}")

    # Metadata
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"**Campaign:** {profile['campaign_name']}")

    with col2:
        st.markdown(f"**Created:** {profile['created_at'].strftime('%Y-%m-%d %H:%M')}")

    with col3:
        if st.button("🗑️ Delete", use_container_width=True):
            if delete_brand_voice_profile(str(profile['id'])):
                st.success("Training example deleted")
                st.session_state['selected_profile_id'] = None
                st.rerun()
            else:
                st.error("Failed to delete training example")

    st.markdown("---")

    # Example content
    st.subheader("📄 Example Content")

    with st.expander("View Example Content", expanded=True):
        st.text_area(
            "Content",
            value=profile['example_content'],
            height=200,
            disabled=True,
            label_visibility="collapsed"
        )

    st.markdown("---")

    # Analysis
    st.subheader("🔍 Brand Voice Analysis")

    calculated_profile = profile.get('calculated_profile')

    if calculated_profile:
        if isinstance(calculated_profile, str):
            calculated_profile = json.loads(calculated_profile)

        # Display analysis results
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Voice Characteristics:**")

            if 'tone' in calculated_profile:
                st.metric("Tone", calculated_profile['tone'])

            if 'formality' in calculated_profile:
                st.metric("Formality Level", calculated_profile['formality'])

            if 'sentiment' in calculated_profile:
                st.metric("Sentiment", calculated_profile['sentiment'])

        with col2:
            st.markdown("**Style Attributes:**")

            if 'vocabulary_level' in calculated_profile:
                st.metric("Vocabulary Level", calculated_profile['vocabulary_level'])

            if 'sentence_structure' in calculated_profile:
                st.metric("Sentence Structure", calculated_profile['sentence_structure'])

            if 'perspective' in calculated_profile:
                st.metric("Perspective", calculated_profile['perspective'])

        # Full analysis
        with st.expander("View Full Analysis"):
            st.json(calculated_profile)
    else:
        st.info("This example has not been analyzed yet.")

        if st.button("🔍 Analyze Now", use_container_width=True):
            with st.spinner("Analyzing brand voice..."):
                result = trigger_voice_analysis(
                    str(profile['id']),
                    profile['example_content']
                )

                if result and isinstance(result, dict):
                    # Use actual API response for analysis
                    analysis_data = result.get('analysis', result)

                    # Ensure required fields have defaults if not present
                    voice_analysis = {
                        "tone": analysis_data.get("tone", "Not analyzed"),
                        "formality": analysis_data.get("formality", "Not analyzed"),
                        "sentiment": analysis_data.get("sentiment", "Neutral"),
                        "vocabulary_level": analysis_data.get("vocabulary_level", "Standard"),
                        "sentence_structure": analysis_data.get("sentence_structure", "Mixed"),
                        "perspective": analysis_data.get("perspective", "Third Person"),
                        "key_phrases": analysis_data.get("key_phrases", []),
                        "avg_sentence_length": analysis_data.get("avg_sentence_length", 0),
                        "readability_score": analysis_data.get("readability_score", 0)
                    }

                    if update_brand_voice_analysis(str(profile['id']), voice_analysis):
                        st.success("Analysis complete!")
                        st.rerun()
                    else:
                        st.error("Failed to save analysis")
                elif result:
                    st.warning("Analysis queued - check back in a moment")
                else:
                    st.error("Failed to start analysis - please try again")


if __name__ == "__main__":
    main()
