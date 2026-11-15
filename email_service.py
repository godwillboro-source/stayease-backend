from html import escape

from flask import current_app
import resend
from resend.exceptions import ResendError


class EmailDeliveryError(Exception):
    pass


def send_email(recipient, subject, text, html):
    api_key = current_app.config.get("RESEND_API_KEY")
    from_email = current_app.config.get("RESEND_FROM_EMAIL")
    if not api_key or not from_email:
        raise EmailDeliveryError("Resend is not configured")

    resend.api_key = api_key
    try:
        resend.Emails.send({
            "from": from_email,
            "to": [recipient],
            "subject": subject,
            "text": text,
            "html": html,
        })
    except ResendError as exc:
        message = f"Resend returned HTTP {exc.code}: {exc.message}"
        cloudflare_ray = next(
            (value for key, value in exc.headers.items() if key.lower() == "cf-ray"),
            None,
        )
        if cloudflare_ray:
            message += f" (Cloudflare Ray ID: {cloudflare_ray})"
        raise EmailDeliveryError(message) from exc

    current_app.logger.info("Resend accepted email request")


def send_welcome_email(recipient, name):
    safe_name = escape(name)
    send_email(
        recipient,
        "Welcome to StayEase",
        f"Hi {name},\n\nWelcome to StayEase. Your account is ready to use.",
        (
            f"<p>Hi {safe_name},</p>"
            "<p>Welcome to StayEase. Your account is ready to use.</p>"
        ),
    )


def send_sign_in_notification(recipient, name):
    safe_name = escape(name)
    send_email(
        recipient,
        "New sign-in to your StayEase account",
        (
            f"Hi {name},\n\nA sign-in to your StayEase account just occurred. "
            "If you don't recognize it, please review your account."
        ),
        (
            f"<p>Hi {safe_name},</p>"
            "<p>A sign-in to your StayEase account just occurred. "
            "If you don't recognize it, please review your account.</p>"
        ),
    )
