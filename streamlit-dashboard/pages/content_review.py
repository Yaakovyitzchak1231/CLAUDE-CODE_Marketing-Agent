"""
Content Review Page - Human-in-the-Loop Review Interface
Enables side-by-side editing, version comparison, and approval workflow
"""

import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
import difflib
import os

st.set_page_config(page_title="Content Review", page_icon="✍️", layout="wide")

# Database configuration
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "database": os.getenv("POSTGRES_DB", "marketing_db"),
    "user": os.getenv("POSTGRES_USER", "marketing_user"),
    "password": os.getenv("POSTGRES_PASSWORD", "marketing_pass")
}

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook")


@st.cache_resource
def get_db_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True  # Prevent transaction issues
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {str(e)}")
        return None


def get_drafts_for_review() -> List[Dict]:
    """Fetch all content drafts in review status"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT cd.*, c.name as campaign_name, c.branding_json,
                       (SELECT COUNT(*) FROM content_versions WHERE draft_id = cd.id) as version_count,
                       (SELECT COUNT(*) FROM media_assets WHERE draft_id = cd.id) as media_count,
                       (SELECT COUNT(*) FROM review_feedback WHERE draft_id = cd.id) as feedback_count
                FROM content_drafts cd
                JOIN campaigns c ON cd.campaign_id = c.id
                WHERE cd.status IN ('in_review', 'draft')
                ORDER BY cd.created_at DESC
            """)

            return cursor.fetchall()
    except Exception as e:
        st.error(f"Error fetching drafts: {str(e)}")
        return []


def get_draft_by_id(draft_id: int) -> Optional[Dict]:
    """Fetch specific draft by ID"""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT cd.*, c.name as campaign_name, c.branding_json, c.target_audience
                FROM content_drafts cd
                JOIN campaigns c ON cd.campaign_id = c.id
                WHERE cd.id = %s
            """, (draft_id,))

            return cursor.fetchone()
    except Exception as e:
        st.error(f"Error fetching draft: {str(e)}")
        return None


def get_draft_versions(draft_id: int) -> List[Dict]:
    """Fetch all versions of a draft"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT *
                FROM content_versions
                WHERE draft_id = %s
                ORDER BY version_number DESC
            """, (draft_id,))

            return cursor.fetchall()
    except Exception as e:
        st.error(f"Error fetching versions: {str(e)}")
        return []


def get_draft_feedback(draft_id: int) -> List[Dict]:
    """Fetch feedback history for a draft"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT *
                FROM review_feedback
                WHERE draft_id = %s
                ORDER BY created_at DESC
            """, (draft_id,))

            return cursor.fetchall()
    except Exception as e:
        st.error(f"Error fetching feedback: {str(e)}")
        return []


def submit_review_feedback(draft_id: int, action: str, feedback_text: str = "",
                          rating: Optional[int] = None, suggested_edits: Optional[List] = None):
    """Submit review feedback via n8n webhook"""

    payload = {
        "draft_id": draft_id,
        "action": action,
        "reviewer_id": st.session_state.get('user_id', 1),
        "feedback_text": feedback_text,
        "rating": rating,
        "suggested_edits": suggested_edits or [],
        "reviewed_at": datetime.now().isoformat()
    }

    try:
        response = requests.post(
            f"{N8N_WEBHOOK_URL}/review-feedback",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Review submission failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error submitting review: {str(e)}")
        return None


def show_diff_view(original: str, modified: str):
    """Display side-by-side diff of two text versions"""

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Original")
        st.text_area("", value=original, height=400, disabled=True, key="diff_original")

    with col2:
        st.markdown("### Modified")
        st.text_area("", value=modified, height=400, disabled=True, key="diff_modified")

    # Show line-by-line diff
    st.markdown("### Changes")

    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        modified.splitlines(keepends=True),
        lineterm=''
    )

    diff_text = ''.join(diff)

    if diff_text:
        st.code(diff_text, language="diff")
    else:
        st.info("No changes detected")


def main():
    """Main content review interface"""

    st.title("✍️ Content Review Center")
    st.markdown("Review and approve AI-generated content with inline editing and feedback")

    # Session state initialization
    if 'selected_draft_id' not in st.session_state:
        st.session_state['selected_draft_id'] = None
    if 'edited_content' not in st.session_state:
        st.session_state['edited_content'] = ""

    # Layout: Sidebar for draft list, main area for review
    col_sidebar, col_main = st.columns([1, 3])

    with col_sidebar:
        st.subheader("📋 Pending Reviews")

        drafts = get_drafts_for_review()

        if not drafts:
            st.info("No content pending review")
        else:
            for draft in drafts:
                status_emoji = "🟡" if draft['status'] == 'in_review' else "⚪"
                with st.container():
                    if st.button(
                        f"{status_emoji} {draft['type'].upper()}",
                        key=f"draft_{draft['id']}",
                        use_container_width=True
                    ):
                        st.session_state['selected_draft_id'] = draft['id']
                        st.rerun()

                    st.caption(f"{draft['campaign_name']}")
                    st.caption(f"v{draft['version_count']} • {draft['media_count']} media • {draft['feedback_count']} feedback")
                    st.markdown("---")

    with col_main:
        if st.session_state['selected_draft_id']:
            show_review_interface(st.session_state['selected_draft_id'])
        else:
            st.info("👈 Select a draft from the sidebar to begin review")

            # Show summary statistics
            st.markdown("### Review Queue Summary")

            col1, col2, col3 = st.columns(3)

            with col1:
                in_review = len([d for d in drafts if d['status'] == 'in_review'])
                st.metric("In Review", in_review)

            with col2:
                drafts_count = len([d for d in drafts if d['status'] == 'draft'])
                st.metric("Drafts", drafts_count)

            with col3:
                total_media = sum(d['media_count'] for d in drafts)
                st.metric("Media Assets", total_media)


def show_review_interface(draft_id: int):
    """Display review interface for selected draft"""

    draft = get_draft_by_id(draft_id)
    if not draft:
        st.error("Draft not found")
        return

    # Header with draft info
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown(f"### {draft['type'].upper()} - {draft['campaign_name']}")

    with col2:
        status_color = {
            'draft': 'gray',
            'in_review': 'orange',
            'approved': 'green',
            'rejected': 'red'
        }.get(draft['status'], 'gray')

        st.markdown(f"**Status:** :{status_color}[{draft['status'].upper()}]")

    with col3:
        if st.button("← Back to List"):
            st.session_state['selected_draft_id'] = None
            st.rerun()

    st.markdown("---")

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Edit & Review", "📊 Versions", "💬 Feedback", "🎯 SEO & Metadata"])

    with tab1:
        show_edit_tab(draft)

    with tab2:
        show_versions_tab(draft)

    with tab3:
        show_feedback_tab(draft)

    with tab4:
        show_metadata_tab(draft)


def show_edit_tab(draft: Dict):
    """Show editing interface with side-by-side view"""

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Original Content")
        st.text_area(
            "Original",
            value=draft['content'],
            height=400,
            disabled=True,
            key="original_content",
            label_visibility="collapsed"
        )

    with col2:
        st.markdown("#### Your Edits")

        # Initialize edited content from session state or original
        if 'edited_content' not in st.session_state or not st.session_state['edited_content']:
            st.session_state['edited_content'] = draft['content']

        edited = st.text_area(
            "Edited",
            value=st.session_state['edited_content'],
            height=400,
            key="edit_area",
            label_visibility="collapsed"
        )

        st.session_state['edited_content'] = edited

    # Character count and reading time
    col1, col2 = st.columns(2)
    with col1:
        char_count = len(st.session_state['edited_content'])
        word_count = len(st.session_state['edited_content'].split())
        st.caption(f"📝 {word_count} words • {char_count} characters")

    with col2:
        reading_time = max(1, word_count // 200)
        st.caption(f"⏱️ ~{reading_time} min read")

    # Inline comments
    st.markdown("---")
    st.markdown("#### 💬 Add Review Comments")

    feedback_text = st.text_area(
        "Feedback",
        placeholder="Add your review comments, suggestions, or revision requests...",
        height=100,
        key="feedback_input"
    )

    # Rating
    rating = st.select_slider(
        "Content Quality Rating",
        options=[1, 2, 3, 4, 5],
        value=3,
        help="1 = Needs major revision, 5 = Excellent"
    )

    # Suggested edits (structured)
    st.markdown("#### ✏️ Suggested Edits (Optional)")

    with st.expander("Add structured edit suggestions"):
        edit_section = st.text_input("Section/Paragraph", placeholder="e.g., Introduction, Paragraph 2")
        edit_suggestion = st.text_area("Suggested change", placeholder="Describe the edit needed")

        if st.button("Add Edit Suggestion"):
            if 'suggested_edits' not in st.session_state:
                st.session_state['suggested_edits'] = []

            st.session_state['suggested_edits'].append({
                "section": edit_section,
                "suggestion": edit_suggestion
            })

            st.success("Edit suggestion added")

        # Display current suggestions
        if 'suggested_edits' in st.session_state and st.session_state['suggested_edits']:
            st.markdown("**Current Suggestions:**")
            for i, edit in enumerate(st.session_state['suggested_edits']):
                st.markdown(f"- **{edit['section']}**: {edit['suggestion']}")

    # Action buttons
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("✅ Approve & Publish", type="primary", use_container_width=True):
            result = submit_review_feedback(
                draft_id=draft['id'],
                action='approve',
                feedback_text=feedback_text,
                rating=rating
            )

            if result:
                st.success("✅ Content approved and queued for publishing!")
                st.balloons()
                st.session_state['selected_draft_id'] = None
                st.rerun()

    with col2:
        if st.button("🔄 Request Revisions", use_container_width=True):
            suggested_edits = st.session_state.get('suggested_edits', [])

            result = submit_review_feedback(
                draft_id=draft['id'],
                action='revise',
                feedback_text=feedback_text,
                rating=rating,
                suggested_edits=suggested_edits
            )

            if result:
                st.success("🔄 Revision request sent to AI agent!")
                st.info("A new version will be generated based on your feedback")
                st.session_state['suggested_edits'] = []
                st.session_state['selected_draft_id'] = None
                st.rerun()

    with col3:
        if st.button("❌ Reject", use_container_width=True):
            if feedback_text:
                result = submit_review_feedback(
                    draft_id=draft['id'],
                    action='reject',
                    feedback_text=feedback_text,
                    rating=rating
                )

                if result:
                    st.warning("❌ Content rejected")
                    st.session_state['selected_draft_id'] = None
                    st.rerun()
            else:
                st.error("Please provide feedback explaining why you're rejecting this content")

    with col4:
        if st.button("💾 Save Draft", use_container_width=True):
            # Update draft in database with edited content
            conn = get_db_connection()
            if conn:
                try:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            UPDATE content_drafts
                            SET content = %s, updated_at = NOW()
                            WHERE id = %s
                        """, (st.session_state['edited_content'], draft['id']))

                        conn.commit()
                        st.success("💾 Draft saved!")
                except Exception as e:
                    st.error(f"Error saving draft: {str(e)}")


def show_versions_tab(draft: Dict):
    """Show version history with comparison"""

    versions = get_draft_versions(draft['id'])

    if not versions:
        st.info("No version history available")
        return

    st.markdown(f"### Version History ({len(versions)} versions)")

    # Version selector for comparison
    col1, col2 = st.columns(2)

    with col1:
        version_options_1 = {f"v{v['version_number']} - {v['created_at'].strftime('%Y-%m-%d %H:%M')}": v
                            for v in versions}
        selected_v1 = st.selectbox("Compare from", options=list(version_options_1.keys()), index=0)

    with col2:
        version_options_2 = {f"v{v['version_number']} - {v['created_at'].strftime('%Y-%m-%d %H:%M')}": v
                            for v in versions}
        selected_v2 = st.selectbox("Compare to", options=list(version_options_2.keys()),
                                   index=min(1, len(versions)-1))

    if st.button("Show Comparison"):
        v1 = version_options_1[selected_v1]
        v2 = version_options_2[selected_v2]

        show_diff_view(v1['content'], v2['content'])

    # Timeline view
    st.markdown("---")
    st.markdown("### Version Timeline")

    for version in versions:
        with st.expander(f"v{version['version_number']} - {version['created_at'].strftime('%Y-%m-%d %H:%M')}"):
            st.caption(f"Created by: {version.get('created_by', 'AI Agent')}")

            # Preview content
            content_preview = version['content'][:300] + "..." if len(version['content']) > 300 else version['content']
            st.markdown(content_preview)

            if st.button(f"Restore v{version['version_number']}", key=f"restore_{version['id']}"):
                st.session_state['edited_content'] = version['content']
                st.success(f"Restored to version {version['version_number']}")
                st.rerun()


def show_feedback_tab(draft: Dict):
    """Show feedback history"""

    feedback_list = get_draft_feedback(draft['id'])

    if not feedback_list:
        st.info("No feedback yet")
        return

    st.markdown(f"### Feedback History ({len(feedback_list)} entries)")

    for feedback in feedback_list:
        with st.container():
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**{feedback['reviewer']}** - {feedback['created_at'].strftime('%Y-%m-%d %H:%M')}")

            with col2:
                if feedback.get('rating'):
                    st.markdown("⭐" * feedback['rating'])

            st.markdown(feedback['feedback_text'])

            if feedback.get('suggested_edits'):
                with st.expander("View suggested edits"):
                    for edit in feedback['suggested_edits']:
                        st.markdown(f"- **{edit.get('section', 'General')}**: {edit.get('suggestion', '')}")

            st.markdown("---")


def show_metadata_tab(draft: Dict):
    """Show SEO and metadata information"""

    st.markdown("### SEO & Metadata")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("SEO Score", f"{draft.get('seo_score', 0)}/100")
        st.metric("Word Count", draft.get('word_count', 0))

        if draft.get('meta_keywords'):
            st.markdown("**Keywords:**")
            st.write(draft['meta_keywords'])

    with col2:
        if draft.get('meta_description'):
            st.markdown("**Meta Description:**")
            st.info(draft['meta_description'])

        reading_time = max(1, draft.get('word_count', 0) // 200)
        st.metric("Reading Time", f"{reading_time} min")

    # Target audience
    st.markdown("---")
    st.markdown("### Target Audience")
    st.write(draft.get('target_audience', 'Not specified'))

    # Brand voice
    if draft.get('branding_json'):
        st.markdown("### Brand Guidelines")
        st.json(draft['branding_json'])


if __name__ == "__main__":
    main()
