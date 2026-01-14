"""
User Onboarding - Profile Setup and Configuration
Conversational wizard for capturing user profile and preferences
"""

import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from typing import Dict, Optional
import requests
import json

# Page configuration
st.set_page_config(
    page_title="Profile Setup - Marketing Dashboard",
    page_icon="👤",
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
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {str(e)}")
        return None


def get_user_profile(user_id: int = 1) -> Optional[Dict]:
    """Fetch user profile from database"""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, email, company, created_at
                FROM users
                WHERE id = %s
            """, (user_id,))
            return cursor.fetchone()
    except Exception as e:
        st.error(f"Error fetching user profile: {str(e)}")
        return None


def create_user_profile(email: str, company: str) -> Optional[int]:
    """Create new user profile"""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (email, company)
                VALUES (%s, %s)
                RETURNING id
            """, (email, company))

            user_id = cursor.fetchone()[0]
            conn.commit()
            return user_id
    except Exception as e:
        st.error(f"Error creating user profile: {str(e)}")
        conn.rollback()
        return None


def update_user_profile(user_id: int, email: str, company: str) -> bool:
    """Update existing user profile"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE users
                SET email = %s, company = %s
                WHERE id = %s
            """, (email, company, user_id))

            conn.commit()
            return True
    except Exception as e:
        st.error(f"Error updating user profile: {str(e)}")
        conn.rollback()
        return False


def trigger_onboarding_workflow(profile_data: Dict) -> bool:
    """Trigger n8n onboarding workflow"""
    try:
        response = requests.post(
            f"{N8N_WEBHOOK_URL}/onboarding",
            json=profile_data,
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error triggering onboarding workflow: {str(e)}")
        return False


def initialize_session_state():
    """Initialize session state for wizard"""
    if 'onboarding_step' not in st.session_state:
        st.session_state['onboarding_step'] = 1

    if 'profile_data' not in st.session_state:
        st.session_state['profile_data'] = {}


def main():
    """Main onboarding application"""

    initialize_session_state()

    # Check if user already exists
    user_profile = get_user_profile(user_id=1)

    if user_profile and not st.session_state.get('force_onboarding', False):
        # User exists - show profile management
        show_profile_management(user_profile)
    else:
        # New user - show onboarding wizard
        show_onboarding_wizard()


def show_profile_management(user_profile: Dict):
    """Show profile management for existing users"""

    st.title("👤 User Profile")
    st.markdown("Manage your account settings and preferences")

    # Option to re-run onboarding
    with st.sidebar:
        st.header("⚙️ Actions")

        if st.button("🔄 Re-run Onboarding", use_container_width=True):
            st.session_state['force_onboarding'] = True
            st.session_state['onboarding_step'] = 1
            st.rerun()

        st.markdown("---")
        st.caption(f"Account created: {user_profile['created_at'].strftime('%Y-%m-%d')}")

    # Display current profile
    st.subheader("📋 Current Profile")

    with st.form("update_profile_form"):
        email = st.text_input("Email Address", value=user_profile['email'])
        company = st.text_input("Company Name", value=user_profile['company'])

        submitted = st.form_submit_button("💾 Save Changes", use_container_width=True)

        if submitted:
            if update_user_profile(user_profile['id'], email, company):
                st.success("Profile updated successfully!")
                st.rerun()
            else:
                st.error("Failed to update profile")

    # Show campaign statistics
    st.markdown("---")
    st.subheader("📊 Account Statistics")

    conn = get_db_connection()
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT
                    COUNT(*) as total_campaigns,
                    COUNT(*) FILTER (WHERE status = 'active') as active_campaigns,
                    (SELECT COUNT(*) FROM content_drafts cd
                     JOIN campaigns c ON cd.campaign_id = c.id
                     WHERE c.user_id = %s) as total_content,
                    (SELECT COUNT(*) FROM content_drafts cd
                     JOIN campaigns c ON cd.campaign_id = c.id
                     WHERE c.user_id = %s AND cd.status = 'published') as published_content
                FROM campaigns
                WHERE user_id = %s
            """, (user_profile['id'], user_profile['id'], user_profile['id']))

            stats = cursor.fetchone()

            if stats:
                col1, col2, col3, col4 = st.columns(4)

                col1.metric("Total Campaigns", stats['total_campaigns'] or 0)
                col2.metric("Active Campaigns", stats['active_campaigns'] or 0)
                col3.metric("Total Content", stats['total_content'] or 0)
                col4.metric("Published Content", stats['published_content'] or 0)


def show_onboarding_wizard():
    """Show multi-step onboarding wizard"""

    st.title("🚀 Welcome to Marketing Automation")
    st.markdown("Let's get you set up in just a few steps")

    # Progress bar
    progress = (st.session_state['onboarding_step'] - 1) / 5
    st.progress(progress)

    st.markdown(f"**Step {st.session_state['onboarding_step']} of 6**")
    st.markdown("---")

    # Show appropriate step
    if st.session_state['onboarding_step'] == 1:
        step_1_basic_info()
    elif st.session_state['onboarding_step'] == 2:
        step_2_business_info()
    elif st.session_state['onboarding_step'] == 3:
        step_3_target_audience()
    elif st.session_state['onboarding_step'] == 4:
        step_4_brand_guidelines()
    elif st.session_state['onboarding_step'] == 5:
        step_5_content_preferences()
    elif st.session_state['onboarding_step'] == 6:
        step_6_review_and_finish()


def step_1_basic_info():
    """Step 1: Basic user information"""

    st.subheader("📧 Let's start with your basic information")

    with st.form("step1_form"):
        email = st.text_input(
            "Email Address *",
            placeholder="your.email@company.com",
            value=st.session_state['profile_data'].get('email', '')
        )

        company = st.text_input(
            "Company Name *",
            placeholder="Your Company Inc.",
            value=st.session_state['profile_data'].get('company', '')
        )

        role = st.selectbox(
            "Your Role",
            ["Marketing Manager", "Content Creator", "Social Media Manager",
             "CMO", "Business Owner", "Other"],
            index=0 if 'role' not in st.session_state['profile_data'] else
                  ["Marketing Manager", "Content Creator", "Social Media Manager",
                   "CMO", "Business Owner", "Other"].index(st.session_state['profile_data']['role'])
        )

        submitted = st.form_submit_button("Next →", use_container_width=True)

        if submitted:
            if not email or not company:
                st.error("Please fill in all required fields")
                return

            st.session_state['profile_data']['email'] = email
            st.session_state['profile_data']['company'] = company
            st.session_state['profile_data']['role'] = role
            st.session_state['onboarding_step'] = 2
            st.rerun()


def step_2_business_info():
    """Step 2: Business information"""

    st.subheader("🏢 Tell us about your business")

    with st.form("step2_form"):
        industry = st.selectbox(
            "Industry",
            ["Technology", "Healthcare", "Finance", "E-commerce", "Education",
             "Manufacturing", "Real Estate", "Professional Services", "Other"],
            index=0 if 'industry' not in st.session_state['profile_data'] else
                  ["Technology", "Healthcare", "Finance", "E-commerce", "Education",
                   "Manufacturing", "Real Estate", "Professional Services", "Other"].index(
                      st.session_state['profile_data']['industry'])
        )

        company_size = st.selectbox(
            "Company Size",
            ["1-10", "11-50", "51-200", "201-500", "500+"],
            index=0 if 'company_size' not in st.session_state['profile_data'] else
                  ["1-10", "11-50", "51-200", "201-500", "500+"].index(
                      st.session_state['profile_data']['company_size'])
        )

        website = st.text_input(
            "Website URL",
            placeholder="https://www.yourcompany.com",
            value=st.session_state['profile_data'].get('website', '')
        )

        business_model = st.radio(
            "Business Model",
            ["B2B", "B2C", "Both"],
            horizontal=True,
            index=0 if 'business_model' not in st.session_state['profile_data'] else
                  ["B2B", "B2C", "Both"].index(st.session_state['profile_data']['business_model'])
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.form_submit_button("← Back"):
                st.session_state['onboarding_step'] = 1
                st.rerun()

        with col2:
            submitted = st.form_submit_button("Next →", use_container_width=True)

            if submitted:
                st.session_state['profile_data']['industry'] = industry
                st.session_state['profile_data']['company_size'] = company_size
                st.session_state['profile_data']['website'] = website
                st.session_state['profile_data']['business_model'] = business_model
                st.session_state['onboarding_step'] = 3
                st.rerun()


def step_3_target_audience():
    """Step 3: Target audience definition"""

    st.subheader("🎯 Who is your target audience?")

    with st.form("step3_form"):
        audience_description = st.text_area(
            "Describe your ideal customer",
            placeholder="e.g., Mid-level marketing managers at B2B tech companies with 50-200 employees...",
            height=120,
            value=st.session_state['profile_data'].get('audience_description', '')
        )

        pain_points = st.text_area(
            "What are their main pain points?",
            placeholder="e.g., Lack of time for content creation, difficulty measuring ROI...",
            height=100,
            value=st.session_state['profile_data'].get('pain_points', '')
        )

        col1, col2 = st.columns(2)

        with col1:
            age_range = st.selectbox(
                "Age Range",
                ["18-24", "25-34", "35-44", "45-54", "55+", "Mixed"],
                index=0 if 'age_range' not in st.session_state['profile_data'] else
                      ["18-24", "25-34", "35-44", "45-54", "55+", "Mixed"].index(
                          st.session_state['profile_data']['age_range'])
            )

        with col2:
            decision_makers = st.checkbox(
                "Targeting decision makers",
                value=st.session_state['profile_data'].get('decision_makers', True)
            )

        col1, col2 = st.columns(2)

        with col1:
            if st.form_submit_button("← Back"):
                st.session_state['onboarding_step'] = 2
                st.rerun()

        with col2:
            submitted = st.form_submit_button("Next →", use_container_width=True)

            if submitted:
                if not audience_description:
                    st.error("Please describe your target audience")
                    return

                st.session_state['profile_data']['audience_description'] = audience_description
                st.session_state['profile_data']['pain_points'] = pain_points
                st.session_state['profile_data']['age_range'] = age_range
                st.session_state['profile_data']['decision_makers'] = decision_makers
                st.session_state['onboarding_step'] = 4
                st.rerun()


def step_4_brand_guidelines():
    """Step 4: Brand guidelines"""

    st.subheader("🎨 Define your brand identity")

    with st.form("step4_form"):
        col1, col2 = st.columns(2)

        with col1:
            brand_voice = st.selectbox(
                "Brand Voice",
                ["Professional", "Casual", "Friendly", "Authoritative", "Humorous"],
                index=0 if 'brand_voice' not in st.session_state['profile_data'] else
                      ["Professional", "Casual", "Friendly", "Authoritative", "Humorous"].index(
                          st.session_state['profile_data']['brand_voice'])
            )

            tone = st.selectbox(
                "Content Tone",
                ["Informative", "Persuasive", "Inspirational", "Educational", "Conversational"],
                index=0 if 'tone' not in st.session_state['profile_data'] else
                      ["Informative", "Persuasive", "Inspirational", "Educational", "Conversational"].index(
                          st.session_state['profile_data']['tone'])
            )

            primary_color = st.color_picker(
                "Primary Brand Color",
                value=st.session_state['profile_data'].get('primary_color', '#667eea')
            )

        with col2:
            keywords = st.text_area(
                "Brand Keywords (one per line)",
                placeholder="innovation\ntechnology\nsolutions",
                height=100,
                value=st.session_state['profile_data'].get('keywords', '')
            )

            secondary_color = st.color_picker(
                "Secondary Brand Color",
                value=st.session_state['profile_data'].get('secondary_color', '#f093fb')
            )

        tagline = st.text_input(
            "Brand Tagline (optional)",
            placeholder="Your company's tagline or mission statement",
            value=st.session_state['profile_data'].get('tagline', '')
        )

        logo_url = st.text_input(
            "Logo URL (optional)",
            placeholder="https://example.com/logo.png",
            value=st.session_state['profile_data'].get('logo_url', '')
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.form_submit_button("← Back"):
                st.session_state['onboarding_step'] = 3
                st.rerun()

        with col2:
            submitted = st.form_submit_button("Next →", use_container_width=True)

            if submitted:
                st.session_state['profile_data']['brand_voice'] = brand_voice
                st.session_state['profile_data']['tone'] = tone
                st.session_state['profile_data']['primary_color'] = primary_color
                st.session_state['profile_data']['secondary_color'] = secondary_color
                st.session_state['profile_data']['keywords'] = keywords
                st.session_state['profile_data']['tagline'] = tagline
                st.session_state['profile_data']['logo_url'] = logo_url
                st.session_state['onboarding_step'] = 5
                st.rerun()


def step_5_content_preferences():
    """Step 5: Content preferences"""

    st.subheader("📝 What type of content do you want to create?")

    with st.form("step5_form"):
        st.markdown("**Select all that apply:**")

        col1, col2, col3 = st.columns(3)

        with col1:
            linkedin_posts = st.checkbox(
                "LinkedIn Posts",
                value=st.session_state['profile_data'].get('linkedin_posts', True)
            )
            blog_posts = st.checkbox(
                "Blog Articles",
                value=st.session_state['profile_data'].get('blog_posts', True)
            )

        with col2:
            social_media = st.checkbox(
                "Social Media (Twitter, Facebook)",
                value=st.session_state['profile_data'].get('social_media', False)
            )
            email_newsletters = st.checkbox(
                "Email Newsletters",
                value=st.session_state['profile_data'].get('email_newsletters', False)
            )

        with col3:
            videos = st.checkbox(
                "Video Content",
                value=st.session_state['profile_data'].get('videos', False)
            )
            infographics = st.checkbox(
                "Infographics",
                value=st.session_state['profile_data'].get('infographics', False)
            )

        st.markdown("---")

        publishing_frequency = st.selectbox(
            "Desired Publishing Frequency",
            ["Daily", "2-3 times per week", "Weekly", "Bi-weekly", "Monthly"],
            index=2 if 'publishing_frequency' not in st.session_state['profile_data'] else
                  ["Daily", "2-3 times per week", "Weekly", "Bi-weekly", "Monthly"].index(
                      st.session_state['profile_data']['publishing_frequency'])
        )

        ai_assistance_level = st.slider(
            "How much AI assistance do you want?",
            1, 5, 3,
            help="1 = AI suggestions only, 5 = Fully automated content generation"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.form_submit_button("← Back"):
                st.session_state['onboarding_step'] = 4
                st.rerun()

        with col2:
            submitted = st.form_submit_button("Next →", use_container_width=True)

            if submitted:
                st.session_state['profile_data']['linkedin_posts'] = linkedin_posts
                st.session_state['profile_data']['blog_posts'] = blog_posts
                st.session_state['profile_data']['social_media'] = social_media
                st.session_state['profile_data']['email_newsletters'] = email_newsletters
                st.session_state['profile_data']['videos'] = videos
                st.session_state['profile_data']['infographics'] = infographics
                st.session_state['profile_data']['publishing_frequency'] = publishing_frequency
                st.session_state['profile_data']['ai_assistance_level'] = ai_assistance_level
                st.session_state['onboarding_step'] = 6
                st.rerun()


def step_6_review_and_finish():
    """Step 6: Review and complete onboarding"""

    st.subheader("✅ Review Your Profile")
    st.markdown("Please review your information before completing setup")

    profile = st.session_state['profile_data']

    # Display profile in organized sections
    with st.expander("📧 Basic Information", expanded=True):
        st.markdown(f"**Email:** {profile.get('email')}")
        st.markdown(f"**Company:** {profile.get('company')}")
        st.markdown(f"**Role:** {profile.get('role')}")

    with st.expander("🏢 Business Information", expanded=True):
        st.markdown(f"**Industry:** {profile.get('industry')}")
        st.markdown(f"**Company Size:** {profile.get('company_size')}")
        st.markdown(f"**Business Model:** {profile.get('business_model')}")
        if profile.get('website'):
            st.markdown(f"**Website:** {profile.get('website')}")

    with st.expander("🎯 Target Audience", expanded=True):
        st.markdown(f"**Description:** {profile.get('audience_description')}")
        if profile.get('pain_points'):
            st.markdown(f"**Pain Points:** {profile.get('pain_points')}")
        st.markdown(f"**Age Range:** {profile.get('age_range')}")

    with st.expander("🎨 Brand Guidelines", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Brand Voice:** {profile.get('brand_voice')}")
            st.markdown(f"**Tone:** {profile.get('tone')}")
        with col2:
            st.color_picker("Primary Color", profile.get('primary_color', '#667eea'), disabled=True)
            st.color_picker("Secondary Color", profile.get('secondary_color', '#f093fb'), disabled=True)

        if profile.get('tagline'):
            st.markdown(f"**Tagline:** {profile.get('tagline')}")

    with st.expander("📝 Content Preferences", expanded=True):
        content_types = []
        if profile.get('linkedin_posts'): content_types.append("LinkedIn Posts")
        if profile.get('blog_posts'): content_types.append("Blog Articles")
        if profile.get('social_media'): content_types.append("Social Media")
        if profile.get('email_newsletters'): content_types.append("Email Newsletters")
        if profile.get('videos'): content_types.append("Videos")
        if profile.get('infographics'): content_types.append("Infographics")

        st.markdown(f"**Content Types:** {', '.join(content_types)}")
        st.markdown(f"**Publishing Frequency:** {profile.get('publishing_frequency')}")
        st.markdown(f"**AI Assistance Level:** {profile.get('ai_assistance_level')}/5")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("← Back to Edit", use_container_width=True):
            st.session_state['onboarding_step'] = 5
            st.rerun()

    with col2:
        if st.button("🚀 Complete Setup", type="primary", use_container_width=True):
            with st.spinner("Creating your profile..."):
                # Create user in database
                user_id = create_user_profile(
                    email=profile['email'],
                    company=profile['company']
                )

                if user_id:
                    # Trigger n8n onboarding workflow
                    profile_data_for_workflow = {
                        **profile,
                        'user_id': user_id
                    }

                    trigger_onboarding_workflow(profile_data_for_workflow)

                    # Clear onboarding state
                    st.session_state['force_onboarding'] = False
                    st.session_state['onboarding_step'] = 1
                    st.session_state['profile_data'] = {}

                    st.success("✅ Profile created successfully!")
                    st.balloons()

                    # Redirect to dashboard
                    st.info("Redirecting to dashboard...")
                    st.rerun()
                else:
                    st.error("Failed to create profile. Please try again.")


if __name__ == "__main__":
    main()
