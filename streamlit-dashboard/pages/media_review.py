"""
Media Review Page - Image and Video Review Interface
Enables preview, editing, and approval of AI-generated media assets
"""

import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
from PIL import Image
import io
import os

st.set_page_config(page_title="Media Review", page_icon="🎨", layout="wide")

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
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {str(e)}")
        return None


def get_media_for_review() -> List[Dict]:
    """Fetch media assets pending review"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT ma.*, cd.status as draft_status, cd.type as content_type,
                       c.name as campaign_name,
                       (SELECT COUNT(*) FROM media_edits WHERE asset_id = ma.id) as edit_count
                FROM media_assets ma
                JOIN content_drafts cd ON ma.draft_id = cd.id
                JOIN campaigns c ON cd.campaign_id = c.id
                WHERE cd.status IN ('in_review', 'draft')
                ORDER BY ma.created_at DESC
            """)

            return cursor.fetchall()
    except Exception as e:
        st.error(f"Error fetching media: {str(e)}")
        return []


def get_media_by_id(asset_id: int) -> Optional[Dict]:
    """Fetch specific media asset"""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT ma.*, cd.content, cd.status as draft_status,
                       c.name as campaign_name, c.branding_json
                FROM media_assets ma
                JOIN content_drafts cd ON ma.draft_id = cd.id
                JOIN campaigns c ON cd.campaign_id = c.id
                WHERE ma.id = %s
            """, (asset_id,))

            return cursor.fetchone()
    except Exception as e:
        st.error(f"Error fetching media: {str(e)}")
        return None


def get_media_edits(asset_id: int) -> List[Dict]:
    """Fetch edit history for media asset"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT *
                FROM media_edits
                WHERE asset_id = %s
                ORDER BY created_at DESC
            """, (asset_id,))

            return cursor.fetchall()
    except Exception as e:
        st.error(f"Error fetching edits: {str(e)}")
        return []


def submit_media_edit(asset_id: int, edit_params: Dict) -> Optional[Dict]:
    """Submit media edit request via n8n webhook"""

    payload = {
        "asset_id": asset_id,
        **edit_params
    }

    try:
        response = requests.post(
            f"{N8N_WEBHOOK_URL}/media-process",
            json=payload,
            timeout=120
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Edit submission failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error submitting edit: {str(e)}")
        return None


def approve_media_asset(asset_id: int, draft_id: int) -> bool:
    """Approve media asset and update draft status"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            # Update media asset status
            cursor.execute("""
                UPDATE media_assets
                SET metadata_json = jsonb_set(
                    COALESCE(metadata_json, '{}'::jsonb),
                    '{approved}',
                    'true'::jsonb
                )
                WHERE id = %s
            """, (asset_id,))

            # Check if all media for draft is approved
            cursor.execute("""
                SELECT COUNT(*) as total,
                       COUNT(*) FILTER (WHERE metadata_json->>'approved' = 'true') as approved
                FROM media_assets
                WHERE draft_id = %s
            """, (draft_id,))

            result = cursor.fetchone()

            # If all media approved, update draft status
            if result and result[0] == result[1]:
                cursor.execute("""
                    UPDATE content_drafts
                    SET status = 'approved'
                    WHERE id = %s
                """, (draft_id,))

            conn.commit()
            return True
    except Exception as e:
        st.error(f"Error approving media: {str(e)}")
        return False


def main():
    """Main media review interface"""

    st.title("🎨 Media Review Center")
    st.markdown("Review and approve AI-generated images and videos")

    # Session state initialization
    if 'selected_asset_id' not in st.session_state:
        st.session_state['selected_asset_id'] = None

    # Layout
    col_sidebar, col_main = st.columns([1, 3])

    with col_sidebar:
        st.subheader("🖼️ Media Queue")

        # Filter by type
        filter_type = st.selectbox("Filter", ["All", "Images", "Videos"])

        media_list = get_media_for_review()

        if filter_type == "Images":
            media_list = [m for m in media_list if m['type'] == 'image']
        elif filter_type == "Videos":
            media_list = [m for m in media_list if m['type'] == 'video']

        if not media_list:
            st.info("No media pending review")
        else:
            for media in media_list:
                type_emoji = "🖼️" if media['type'] == 'image' else "🎬"

                with st.container():
                    if st.button(
                        f"{type_emoji} {media['type'].upper()}",
                        key=f"media_{media['id']}",
                        use_container_width=True
                    ):
                        st.session_state['selected_asset_id'] = media['id']
                        st.rerun()

                    st.caption(f"{media['campaign_name']}")
                    st.caption(f"{media['edit_count']} edits • {media['api_provider']}")

                    # Thumbnail preview
                    if media.get('url'):
                        try:
                            st.image(media['url'], use_column_width=True)
                        except:
                            st.caption("Preview unavailable")

                    st.markdown("---")

    with col_main:
        if st.session_state['selected_asset_id']:
            show_media_review_interface(st.session_state['selected_asset_id'])
        else:
            st.info("👈 Select media from the sidebar to begin review")

            # Summary stats
            st.markdown("### Media Review Summary")

            col1, col2, col3 = st.columns(3)

            with col1:
                image_count = len([m for m in media_list if m['type'] == 'image'])
                st.metric("Images", image_count)

            with col2:
                video_count = len([m for m in media_list if m['type'] == 'video'])
                st.metric("Videos", video_count)

            with col3:
                total_edits = sum(m['edit_count'] for m in media_list)
                st.metric("Total Edits", total_edits)


def show_media_review_interface(asset_id: int):
    """Display review interface for selected media"""

    media = get_media_by_id(asset_id)
    if not media:
        st.error("Media not found")
        return

    # Header
    col1, col2 = st.columns([3, 1])

    with col1:
        type_emoji = "🖼️" if media['type'] == 'image' else "🎬"
        st.markdown(f"### {type_emoji} {media['type'].upper()} - {media['campaign_name']}")

    with col2:
        if st.button("← Back to List"):
            st.session_state['selected_asset_id'] = None
            st.rerun()

    st.markdown("---")

    # Tabs
    if media['type'] == 'image':
        tab1, tab2, tab3 = st.tabs(["🖼️ Preview & Edit", "📊 Edit History", "ℹ️ Metadata"])
    else:
        tab1, tab2, tab3 = st.tabs(["🎬 Preview & Edit", "📊 Edit History", "ℹ️ Metadata"])

    with tab1:
        if media['type'] == 'image':
            show_image_editor(media)
        else:
            show_video_editor(media)

    with tab2:
        show_edit_history(media)

    with tab3:
        show_media_metadata(media)


def show_image_editor(media: Dict):
    """Image editing interface"""

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### Current Image")

        if media.get('url'):
            st.image(media['url'], use_column_width=True)
        else:
            st.warning("Image URL not available")

    with col2:
        st.markdown("#### Edit Tools")

        # Crop controls
        with st.expander("✂️ Crop", expanded=False):
            crop_x = st.number_input("X Position", min_value=0, value=0, step=10)
            crop_y = st.number_input("Y Position", min_value=0, value=0, step=10)
            crop_width = st.number_input("Width", min_value=100, value=800, step=50)
            crop_height = st.number_input("Height", min_value=100, value=600, step=50)

            if st.button("Apply Crop"):
                result = submit_media_edit(media['id'], {
                    "operation": "crop",
                    "crop_x": crop_x,
                    "crop_y": crop_y,
                    "crop_width": crop_width,
                    "crop_height": crop_height
                })

                if result:
                    st.success("Crop applied!")
                    st.rerun()

        # Resize controls
        with st.expander("📐 Resize", expanded=False):
            resize_width = st.number_input("Width (px)", min_value=100, value=1200, step=50)
            resize_height = st.number_input("Height (px)", min_value=100, value=628, step=50)
            resize_mode = st.selectbox("Resize Mode", ["fitImage", "cover", "contain"])

            if st.button("Apply Resize"):
                result = submit_media_edit(media['id'], {
                    "operation": "resize",
                    "resize_width": resize_width,
                    "resize_height": resize_height,
                    "resize_mode": resize_mode
                })

                if result:
                    st.success("Resize applied!")
                    st.rerun()

        # Filters
        with st.expander("🎨 Filters", expanded=False):
            filter_type = st.selectbox("Filter Type", ["none", "grayscale", "sepia", "brighten", "darken"])
            brightness = st.slider("Brightness", -100, 100, 0)
            contrast = st.slider("Contrast", -100, 100, 0)
            saturation = st.slider("Saturation", -100, 100, 0)

            if st.button("Apply Filter"):
                result = submit_media_edit(media['id'], {
                    "operation": "filter",
                    "filter_type": filter_type,
                    "brightness": brightness,
                    "contrast": contrast,
                    "saturation": saturation
                })

                if result:
                    st.success("Filter applied!")
                    st.rerun()

        # Watermark
        with st.expander("💧 Watermark", expanded=False):
            watermark_text = st.text_input("Text", value=media.get('branding_json', {}).get('company_name', ''))
            watermark_size = st.slider("Font Size", 12, 48, 24)
            watermark_color = st.color_picker("Color", "#FFFFFF")
            watermark_x = st.number_input("X Position", min_value=0, value=20, step=10)
            watermark_y = st.number_input("Y Position", min_value=0, value=20, step=10)

            if st.button("Apply Watermark"):
                result = submit_media_edit(media['id'], {
                    "operation": "watermark",
                    "watermark_text": watermark_text,
                    "watermark_size": watermark_size,
                    "watermark_color": watermark_color,
                    "watermark_x": watermark_x,
                    "watermark_y": watermark_y
                })

                if result:
                    st.success("Watermark applied!")
                    st.rerun()

    # Action buttons
    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✅ Approve Image", type="primary", use_container_width=True):
            if approve_media_asset(media['id'], media['draft_id']):
                st.success("✅ Image approved!")
                st.balloons()
                st.session_state['selected_asset_id'] = None
                st.rerun()

    with col2:
        if st.button("🔄 Reset to Original", use_container_width=True):
            st.warning("Reset functionality coming soon")

    with col3:
        if st.button("❌ Reject", use_container_width=True):
            st.warning("Reject functionality coming soon")


def show_video_editor(media: Dict):
    """Video editing interface"""

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### Current Video")

        if media.get('url'):
            st.video(media['url'])
        else:
            st.warning("Video URL not available")

    with col2:
        st.markdown("#### Edit Tools")

        # Trim controls
        with st.expander("✂️ Trim", expanded=False):
            duration = media.get('metadata_json', {}).get('duration_seconds', 30)

            trim_start = st.number_input("Start Time (sec)", min_value=0.0, max_value=float(duration), value=0.0, step=0.5)
            trim_end = st.number_input("End Time (sec)", min_value=0.0, max_value=float(duration), value=float(duration), step=0.5)

            if st.button("Apply Trim"):
                result = submit_media_edit(media['id'], {
                    "operation": "trim",
                    "trim_start": trim_start,
                    "trim_end": trim_end
                })

                if result:
                    st.success("Trim applied!")
                    st.rerun()

        # Captions
        with st.expander("📝 Captions", expanded=False):
            caption_text = st.text_area("Caption Text", placeholder="Enter captions...")
            caption_font_size = st.slider("Font Size", 12, 48, 24)
            caption_color = st.selectbox("Color", ["white", "black", "yellow"])
            caption_position = st.selectbox("Position", ["bottom", "top", "center"])

            if st.button("Add Captions"):
                captions = [{"text": caption_text, "start": 0, "end": trim_end}]

                result = submit_media_edit(media['id'], {
                    "operation": "captions",
                    "captions": captions,
                    "caption_font_size": caption_font_size,
                    "caption_color": caption_color,
                    "caption_position": caption_position
                })

                if result:
                    st.success("Captions added!")
                    st.rerun()

        # Background music
        with st.expander("🎵 Music", expanded=False):
            music_url = st.text_input("Music URL", placeholder="https://...")
            music_volume = st.slider("Volume", 0.0, 1.0, 0.3, step=0.1)
            music_fade_in = st.number_input("Fade In (sec)", min_value=0, value=2)
            music_fade_out = st.number_input("Fade Out (sec)", min_value=0, value=2)

            if st.button("Add Music"):
                result = submit_media_edit(media['id'], {
                    "operation": "music",
                    "music_url": music_url,
                    "music_volume": music_volume,
                    "music_fade_in": music_fade_in,
                    "music_fade_out": music_fade_out
                })

                if result:
                    st.success("Music added!")
                    st.rerun()

        # Watermark
        with st.expander("💧 Watermark", expanded=False):
            watermark_image_url = st.text_input("Logo URL", placeholder="https://...")
            watermark_position = st.selectbox("Position", ["top-right", "top-left", "bottom-right", "bottom-left"])
            watermark_opacity = st.slider("Opacity", 0.0, 1.0, 0.7, step=0.1)

            if st.button("Add Video Watermark"):
                result = submit_media_edit(media['id'], {
                    "operation": "watermark",
                    "watermark_image_url": watermark_image_url,
                    "watermark_position": watermark_position,
                    "watermark_opacity": watermark_opacity
                })

                if result:
                    st.success("Watermark added!")
                    st.rerun()

    # Action buttons
    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✅ Approve Video", type="primary", use_container_width=True):
            if approve_media_asset(media['id'], media['draft_id']):
                st.success("✅ Video approved!")
                st.balloons()
                st.session_state['selected_asset_id'] = None
                st.rerun()

    with col2:
        if st.button("🔄 Reset to Original", use_container_width=True):
            st.warning("Reset functionality coming soon")

    with col3:
        if st.button("❌ Reject", use_container_width=True):
            st.warning("Reject functionality coming soon")


def show_edit_history(media: Dict):
    """Display edit history"""

    edits = get_media_edits(media['id'])

    if not edits:
        st.info("No edit history")
        return

    st.markdown(f"### Edit History ({len(edits)} edits)")

    for edit in edits:
        with st.expander(f"{edit['edit_type'].upper()} - {edit['created_at'].strftime('%Y-%m-%d %H:%M')}"):
            st.json(edit['edit_params'])

            if edit.get('edited_file_path'):
                st.caption(f"Output: {edit['edited_file_path']}")

                if st.button(f"Use this version", key=f"use_{edit['id']}"):
                    st.info("Version restore coming soon")


def show_media_metadata(media: Dict):
    """Display media metadata"""

    st.markdown("### Media Information")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Type", media['type'].upper())
        st.metric("Provider", media['api_provider'])

        if media.get('metadata_json'):
            metadata = media['metadata_json']

            if 'dimensions' in metadata:
                st.metric("Dimensions", f"{metadata['dimensions'].get('width', 'N/A')} x {metadata['dimensions'].get('height', 'N/A')}")

            if 'duration_seconds' in metadata:
                st.metric("Duration", f"{metadata['duration_seconds']} sec")

    with col2:
        if media.get('prompt'):
            st.markdown("**Generation Prompt:**")
            st.info(media['prompt'])

        st.caption(f"Created: {media['created_at'].strftime('%Y-%m-%d %H:%M')}")

    # Full metadata
    if media.get('metadata_json'):
        with st.expander("View Full Metadata"):
            st.json(media['metadata_json'])


if __name__ == "__main__":
    main()
