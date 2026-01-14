"""
Publishing Package
Multi-channel content publishing (LinkedIn, WordPress, Email)
"""

from .linkedin_publisher import LinkedInPublisher, publish_to_linkedin
from .wordpress_publisher import WordPressPublisher, publish_to_wordpress
from .email_publisher import EmailPublisher, send_email_newsletter

__all__ = [
    "LinkedInPublisher",
    "publish_to_linkedin",
    "WordPressPublisher",
    "publish_to_wordpress",
    "EmailPublisher",
    "send_email_newsletter"
]

__version__ = "1.0.0"
