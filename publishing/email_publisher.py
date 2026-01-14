"""
Email Publisher via SMTP
Handles sending email newsletters with HTML templates and inline images
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional
from datetime import datetime
import requests
from pathlib import Path
import re


class EmailPublisher:
    """SMTP client for sending email newsletters"""

    def __init__(self, smtp_host: Optional[str] = None, smtp_port: Optional[int] = None,
                 smtp_username: Optional[str] = None, smtp_password: Optional[str] = None,
                 use_tls: bool = True):
        """
        Initialize email publisher

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_username: SMTP username
            smtp_password: SMTP password
            use_tls: Whether to use TLS encryption
        """
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", 587))
        self.smtp_username = smtp_username or os.getenv("SMTP_USERNAME")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")
        self.use_tls = use_tls

        # Default sender
        self.from_email = self.smtp_username
        self.from_name = os.getenv("SMTP_FROM_NAME", "Marketing Automation")

    def send_email(self, to_emails: List[str], subject: str, html_content: str,
                  plain_content: Optional[str] = None,
                  cc_emails: Optional[List[str]] = None,
                  bcc_emails: Optional[List[str]] = None,
                  reply_to: Optional[str] = None,
                  attachments: Optional[List[Dict]] = None,
                  inline_images: Optional[Dict[str, str]] = None) -> Dict:
        """
        Send an email via SMTP

        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            html_content: HTML email content
            plain_content: Plain text fallback content
            cc_emails: CC recipients
            bcc_emails: BCC recipients
            reply_to: Reply-to email address
            attachments: List of attachment dicts with 'filename' and 'url' or 'path'
            inline_images: Dict mapping image CIDs to URLs or paths

        Returns:
            Send result with success status
        """
        # Create message container
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = ", ".join(to_emails)

        if cc_emails:
            msg["Cc"] = ", ".join(cc_emails)

        if reply_to:
            msg["Reply-To"] = reply_to

        # Add plain text version (fallback)
        if plain_content:
            plain_part = MIMEText(plain_content, "plain", "utf-8")
            msg.attach(plain_part)
        else:
            # Strip HTML for plain text version
            plain_text = self._html_to_plain_text(html_content)
            plain_part = MIMEText(plain_text, "plain", "utf-8")
            msg.attach(plain_part)

        # Process inline images
        if inline_images:
            html_content = self._embed_inline_images(msg, html_content, inline_images)

        # Add HTML version
        html_part = MIMEText(html_content, "html", "utf-8")
        msg.attach(html_part)

        # Add attachments
        if attachments:
            for attachment in attachments:
                self._add_attachment(msg, attachment)

        # Send email
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()

                server.login(self.smtp_username, self.smtp_password)

                # Combine all recipients
                all_recipients = to_emails.copy()
                if cc_emails:
                    all_recipients.extend(cc_emails)
                if bcc_emails:
                    all_recipients.extend(bcc_emails)

                server.send_message(msg, to_addrs=all_recipients)

                return {
                    "success": True,
                    "recipients": len(all_recipients),
                    "sent_at": datetime.now().isoformat(),
                    "subject": subject
                }
        except Exception as e:
            raise Exception(f"Failed to send email: {str(e)}")

    def send_newsletter(self, to_emails: List[str], subject: str, content: str,
                       header_image_url: Optional[str] = None,
                       footer_text: Optional[str] = None,
                       unsubscribe_link: Optional[str] = None,
                       preheader: Optional[str] = None) -> Dict:
        """
        Send a formatted newsletter email

        Args:
            to_emails: Recipient email addresses
            subject: Email subject
            content: Newsletter content (HTML or plain text)
            header_image_url: URL for header banner image
            footer_text: Footer text (company info, social links)
            unsubscribe_link: Unsubscribe URL
            preheader: Preview text shown in inbox

        Returns:
            Send result
        """
        # Build newsletter HTML template
        html_content = self._build_newsletter_template(
            content=content,
            header_image_url=header_image_url,
            footer_text=footer_text,
            unsubscribe_link=unsubscribe_link,
            preheader=preheader
        )

        # Prepare inline images
        inline_images = {}
        if header_image_url:
            inline_images["header"] = header_image_url

        return self.send_email(
            to_emails=to_emails,
            subject=subject,
            html_content=html_content,
            inline_images=inline_images
        )

    def send_bulk_emails(self, recipients: List[Dict[str, str]], subject: str,
                        html_template: str, personalization_fields: Optional[List[str]] = None,
                        batch_size: int = 50) -> Dict:
        """
        Send bulk personalized emails

        Args:
            recipients: List of dicts with 'email' and personalization fields
            subject: Email subject (can include {{placeholders}})
            html_template: HTML template with {{placeholders}}
            personalization_fields: List of field names for personalization
            batch_size: Number of emails to send per batch

        Returns:
            Bulk send result with success/failure counts
        """
        success_count = 0
        failure_count = 0
        failures = []

        # Process in batches
        for i in range(0, len(recipients), batch_size):
            batch = recipients[i:i + batch_size]

            for recipient in batch:
                try:
                    # Personalize content
                    personalized_subject = self._personalize_text(
                        subject, recipient
                    )
                    personalized_html = self._personalize_text(
                        html_template, recipient
                    )

                    # Send individual email
                    self.send_email(
                        to_emails=[recipient["email"]],
                        subject=personalized_subject,
                        html_content=personalized_html
                    )

                    success_count += 1
                except Exception as e:
                    failure_count += 1
                    failures.append({
                        "email": recipient["email"],
                        "error": str(e)
                    })

        return {
            "success": True,
            "total": len(recipients),
            "sent": success_count,
            "failed": failure_count,
            "failures": failures,
            "completed_at": datetime.now().isoformat()
        }

    def _build_newsletter_template(self, content: str,
                                   header_image_url: Optional[str] = None,
                                   footer_text: Optional[str] = None,
                                   unsubscribe_link: Optional[str] = None,
                                   preheader: Optional[str] = None) -> str:
        """Build responsive HTML email template"""

        template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Newsletter</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
        }}
        .email-container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
        }}
        .preheader {{
            display: none;
            max-height: 0;
            overflow: hidden;
        }}
        .header {{
            background-color: #667eea;
            padding: 20px;
            text-align: center;
        }}
        .header img {{
            max-width: 100%;
            height: auto;
        }}
        .content {{
            padding: 40px 30px;
            color: #333333;
            line-height: 1.6;
        }}
        .content h1 {{
            color: #667eea;
            font-size: 24px;
            margin-top: 0;
        }}
        .content h2 {{
            color: #333333;
            font-size: 20px;
        }}
        .content p {{
            margin: 15px 0;
        }}
        .content img {{
            max-width: 100%;
            height: auto;
            margin: 20px 0;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 30px;
            text-align: center;
            font-size: 12px;
            color: #666666;
        }}
        .footer a {{
            color: #667eea;
            text-decoration: none;
        }}
        .unsubscribe {{
            margin-top: 15px;
            font-size: 11px;
        }}
        @media only screen and (max-width: 600px) {{
            .content {{
                padding: 20px 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="email-container">
        {"<div class='preheader'>" + preheader + "</div>" if preheader else ""}

        <div class="header">
            {"<img src='cid:header' alt='Newsletter Header' />" if header_image_url else "<h1 style='color: white; margin: 0;'>Newsletter</h1>"}
        </div>

        <div class="content">
            {content}
        </div>

        <div class="footer">
            {footer_text or "© " + datetime.now().strftime("%Y") + " Marketing Automation. All rights reserved."}
            {"<div class='unsubscribe'><a href='" + unsubscribe_link + "'>Unsubscribe</a> from this list</div>" if unsubscribe_link else ""}
        </div>
    </div>
</body>
</html>
"""
        return template

    def _embed_inline_images(self, msg: MIMEMultipart, html_content: str,
                            inline_images: Dict[str, str]) -> str:
        """
        Embed images inline with Content-ID references

        Args:
            msg: Email message object
            html_content: HTML content
            inline_images: Dict mapping CIDs to image URLs/paths

        Returns:
            Updated HTML content with CID references
        """
        for cid, image_source in inline_images.items():
            try:
                # Download or read image
                if image_source.startswith("http"):
                    response = requests.get(image_source, timeout=30)
                    response.raise_for_status()
                    image_data = response.content
                else:
                    with open(image_source, "rb") as f:
                        image_data = f.read()

                # Create image MIME part
                image = MIMEImage(image_data)
                image.add_header("Content-ID", f"<{cid}>")
                image.add_header("Content-Disposition", "inline", filename=cid)

                msg.attach(image)

            except Exception as e:
                print(f"Warning: Failed to embed inline image {cid}: {str(e)}")

        return html_content

    def _add_attachment(self, msg: MIMEMultipart, attachment: Dict):
        """
        Add file attachment to email

        Args:
            msg: Email message object
            attachment: Dict with 'filename' and 'url' or 'path'
        """
        filename = attachment.get("filename")
        source = attachment.get("url") or attachment.get("path")

        try:
            # Download or read file
            if source.startswith("http"):
                response = requests.get(source, timeout=60)
                response.raise_for_status()
                file_data = response.content
            else:
                with open(source, "rb") as f:
                    file_data = f.read()

            # Create attachment
            part = MIMEBase("application", "octet-stream")
            part.set_payload(file_data)
            encoders.encode_base64(part)

            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {filename}"
            )

            msg.attach(part)

        except Exception as e:
            print(f"Warning: Failed to attach file {filename}: {str(e)}")

    def _html_to_plain_text(self, html: str) -> str:
        """Convert HTML to plain text"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)

        # Decode HTML entities
        text = text.replace("&nbsp;", " ")
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')

        # Clean up whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()

        return text

    def _personalize_text(self, text: str, data: Dict[str, str]) -> str:
        """
        Replace {{placeholders}} with personalized data

        Args:
            text: Text with {{placeholders}}
            data: Dict with replacement values

        Returns:
            Personalized text
        """
        for key, value in data.items():
            placeholder = f"{{{{{key}}}}}"
            text = text.replace(placeholder, str(value))

        return text


# Convenience function for FastAPI/n8n integration
def send_email_newsletter(to_emails: List[str], subject: str, content: str,
                         header_image_url: Optional[str] = None,
                         footer_text: Optional[str] = None,
                         unsubscribe_link: Optional[str] = None,
                         smtp_host: Optional[str] = None,
                         smtp_port: Optional[int] = None,
                         smtp_username: Optional[str] = None,
                         smtp_password: Optional[str] = None) -> Dict:
    """
    Send email newsletter

    Args:
        to_emails: Recipient email addresses
        subject: Email subject
        content: Newsletter content
        header_image_url: Header banner URL
        footer_text: Footer text
        unsubscribe_link: Unsubscribe URL
        smtp_host: SMTP server
        smtp_port: SMTP port
        smtp_username: SMTP username
        smtp_password: SMTP password

    Returns:
        Send result
    """
    publisher = EmailPublisher(
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_username=smtp_username,
        smtp_password=smtp_password
    )

    result = publisher.send_newsletter(
        to_emails=to_emails,
        subject=subject,
        content=content,
        header_image_url=header_image_url,
        footer_text=footer_text,
        unsubscribe_link=unsubscribe_link
    )

    return result


if __name__ == "__main__":
    # Example usage
    publisher = EmailPublisher()

    # Test email
    # result = publisher.send_newsletter(
    #     to_emails=["recipient@example.com"],
    #     subject="Your Weekly Marketing Insights",
    #     content="<h1>Hello!</h1><p>Here's your weekly newsletter...</p>",
    #     footer_text="© 2024 Your Company. All rights reserved."
    # )
    # print(result)

    print("Email publisher initialized successfully")
