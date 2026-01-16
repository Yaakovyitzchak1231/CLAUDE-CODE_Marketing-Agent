"""
Email Publisher
Handles sending email newsletters via SMTP
"""

import aiosmtplib
import httpx
import structlog
from typing import Optional, List, Dict, Any
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import formataddr

logger = structlog.get_logger()


class EmailPublisher:
    """
    Email newsletter publisher

    Uses SMTP to send HTML email newsletters
    """

    async def send(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
        from_email: str,
        from_name: Optional[str],
        to_list: List[str],
        subject: str,
        html_content: str,
        inline_images: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Send email newsletter

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_username: SMTP authentication username
            smtp_password: SMTP authentication password
            from_email: Sender email address
            from_name: Optional sender display name
            to_list: List of recipient email addresses
            subject: Email subject line
            html_content: HTML content of the email
            inline_images: Optional list of inline images with url and cid

        Returns:
            Dictionary with send results
        """
        try:
            # Track results
            sent_count = 0
            failed_recipients = []

            # Download and prepare inline images
            image_attachments = []
            if inline_images:
                image_attachments = await self._prepare_inline_images(inline_images)

            # Send to each recipient
            for recipient in to_list:
                try:
                    await self._send_single_email(
                        smtp_host=smtp_host,
                        smtp_port=smtp_port,
                        smtp_username=smtp_username,
                        smtp_password=smtp_password,
                        from_email=from_email,
                        from_name=from_name,
                        to_email=recipient,
                        subject=subject,
                        html_content=html_content,
                        image_attachments=image_attachments
                    )
                    sent_count += 1

                except Exception as e:
                    logger.warning(
                        "email_send_failed",
                        recipient=recipient,
                        error=str(e)
                    )
                    failed_recipients.append(recipient)

            logger.info(
                "email_newsletter_sent",
                sent_count=sent_count,
                failed_count=len(failed_recipients)
            )

            return {
                "platform": "email",
                "sent_count": sent_count,
                "total_recipients": len(to_list),
                "failed_recipients": failed_recipients,
                "subject": subject,
                "has_inline_images": len(image_attachments) > 0
            }

        except Exception as e:
            logger.error("email_send_error", error=str(e))
            raise

    async def _send_single_email(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
        from_email: str,
        from_name: Optional[str],
        to_email: str,
        subject: str,
        html_content: str,
        image_attachments: List[Dict[str, Any]]
    ):
        """Send a single email"""
        # Create the message
        msg = MIMEMultipart('related')
        msg['Subject'] = subject
        msg['From'] = formataddr((from_name or '', from_email))
        msg['To'] = to_email

        # Create the HTML part
        msg_alternative = MIMEMultipart('alternative')
        msg.attach(msg_alternative)

        # Plain text fallback
        plain_text = "This email requires an HTML-compatible email client."
        msg_alternative.attach(MIMEText(plain_text, 'plain'))

        # HTML content
        msg_alternative.attach(MIMEText(html_content, 'html'))

        # Attach inline images
        for img_data in image_attachments:
            image = MIMEImage(img_data['data'])
            image.add_header('Content-ID', f"<{img_data['cid']}>")
            image.add_header(
                'Content-Disposition',
                'inline',
                filename=img_data.get('filename', 'image.jpg')
            )
            msg.attach(image)

        # Send the email
        await aiosmtplib.send(
            msg,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_username,
            password=smtp_password,
            start_tls=True
        )

    async def _prepare_inline_images(
        self,
        inline_images: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Download and prepare inline images

        Args:
            inline_images: List of dicts with 'url' and 'cid' keys

        Returns:
            List of prepared image data
        """
        prepared_images = []

        async with httpx.AsyncClient() as client:
            for img_info in inline_images:
                try:
                    url = img_info.get('url')
                    cid = img_info.get('cid')

                    if not url or not cid:
                        continue

                    response = await client.get(url)
                    if response.status_code != 200:
                        logger.warning("email_image_download_failed", url=url)
                        continue

                    # Get filename from URL
                    filename = url.split('/')[-1].split('?')[0] or 'image.jpg'

                    prepared_images.append({
                        'data': response.content,
                        'cid': cid,
                        'filename': filename
                    })

                except Exception as e:
                    logger.warning(
                        "email_image_prepare_error",
                        url=img_info.get('url'),
                        error=str(e)
                    )

        return prepared_images
