"""Email service for transactional emails.

In dev/local, logs to console instead of sending.
In production, sends via SMTP using SMTP_* env vars.
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from backend.app.config.logging import get_logger
from backend.app.config.settings import settings

logger = get_logger(__name__)


def _build_reset_email(to_email: str, reset_url: str) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Reset your password — Billing Voice Agent"
    msg["From"] = settings.smtp_from_email
    msg["To"] = to_email

    text_body = (
        f"You requested a password reset.\n\n"
        f"Reset link (expires in 60 minutes):\n{reset_url}\n\n"
        f"If you did not request this, ignore this email."
    )
    html_body = f"""
    <html><body style="font-family:sans-serif;color:#111;max-width:480px;margin:0 auto;padding:24px">
      <h2 style="font-size:20px;font-weight:700;margin-bottom:8px">Reset your password</h2>
      <p style="color:#555;margin-bottom:24px">
        Click the button below to reset your password. The link expires in 60 minutes.
      </p>
      <a href="{reset_url}"
         style="display:inline-block;background:#6366f1;color:#fff;padding:12px 24px;
                border-radius:8px;text-decoration:none;font-weight:600;font-size:14px">
        Reset Password
      </a>
      <p style="color:#999;font-size:12px;margin-top:24px">
        If you didn't request a password reset, you can safely ignore this email.
      </p>
    </body></html>
    """
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))
    return msg


async def send_password_reset_email(to_email: str, reset_token: str) -> None:
    """Send a password reset email.

    In local/dev environments (SMTP_HOST not set), logs the reset URL instead.
    """
    reset_url = f"{settings.frontend_url}/reset-password?token={reset_token}"

    if not settings.smtp_host:
        # Dev fallback — log so developers can use the link
        logger.info(
            "password_reset_email_dev",
            to=to_email,
            reset_url=reset_url,
            note="Set SMTP_* env vars to send real email",
        )
        return

    try:
        msg = _build_reset_email(to_email, reset_url)
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
            smtp.ehlo()
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.sendmail(settings.smtp_from_email, [to_email], msg.as_string())
        logger.info("password_reset_email_sent", to=to_email)
    except Exception as e:
        # Log but don't raise — caller should still return 200 to avoid
        # leaking whether an email address exists in the system.
        logger.error("password_reset_email_failed", to=to_email, error=str(e))
