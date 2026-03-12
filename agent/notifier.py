"""
Notifier — sends the rendered HTML digest via Brevo (Sendinblue) SMTP.
Credentials are loaded from environment variables.
"""

import logging
import os
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

SMTP_HOST = "smtp-relay.brevo.com"
SMTP_PORT = 587  # STARTTLS


def send_email(html_body: str, subject: str | None = None) -> bool:
    """
    Send an HTML email via Brevo SMTP.

    Environment variables required:
        BREVO_LOGIN     — your Brevo account email (login)
        BREVO_SMTP_KEY  — Brevo SMTP key (generated in Brevo dashboard)
        BREVO_SENDER    — the From address shown in the email
        BREVO_RECIPIENT — the To address

    Args:
        html_body: Complete HTML string to send.
        subject:   Optional subject override. Defaults to a dated digest subject.

    Returns:
        True on success, False on failure.
    """
    login = os.getenv("BREVO_LOGIN", "")
    smtp_key = os.getenv("BREVO_SMTP_KEY", "")
    sender = os.getenv("BREVO_SENDER", login)
    recipient = os.getenv("BREVO_RECIPIENT", "")

    if not login or not smtp_key or not recipient:
        logger.error(
            "Brevo credentials incomplete. "
            "Set BREVO_LOGIN, BREVO_SMTP_KEY, and BREVO_RECIPIENT in .env"
        )
        return False

    if not html_body:
        logger.error("Empty HTML body — refusing to send email.")
        return False

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if subject is None:
        subject = f"AI Radar Daily Digest — {date_str}"

    # Build the MIME message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"AI Radar <{sender}>"
    msg["To"] = recipient

    html_part = MIMEText(html_body, "html", "utf-8")
    msg.attach(html_part)

    # Send via STARTTLS
    try:
        logger.info("Connecting to %s:%d …", SMTP_HOST, SMTP_PORT)
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(login, smtp_key)
            server.sendmail(sender, recipient, msg.as_string())

        logger.info("Email sent successfully to %s", recipient)
        return True

    except smtplib.SMTPAuthenticationError as exc:
        logger.error("Brevo authentication failed: %s", exc)
        return False

    except smtplib.SMTPRecipientsRefused as exc:
        logger.error("Recipient refused: %s", exc)
        return False

    except smtplib.SMTPException as exc:
        logger.error("SMTP error while sending email: %s", exc)
        return False

    except OSError as exc:
        logger.error("Network error while connecting to Brevo: %s", exc)
        return False

    except Exception as exc:
        logger.error("Unexpected error sending email: %s", exc)
        return False
