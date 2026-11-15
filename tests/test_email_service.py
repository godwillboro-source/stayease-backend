from unittest.mock import MagicMock, patch

import pytest
from resend.exceptions import ResendError

from email_service import EmailDeliveryError, send_email


def test_send_email_posts_to_resend(app, caplog):
    app.config.update(
        RESEND_API_KEY="re_test_key",
        RESEND_FROM_EMAIL="StayEase <noreply@example.com>",
    )

    caplog.set_level("INFO")
    with app.app_context(), patch(
        "email_service.resend.Emails.send",
        return_value=MagicMock(id="email_123"),
    ) as send:
        send_email("carl@test.com", "Subject", "Text body", "<p>HTML body</p>")

    assert "Resend accepted email request" in caplog.text
    assert send.call_args.args[0] == {
        "from": "StayEase <noreply@example.com>",
        "to": ["carl@test.com"],
        "subject": "Subject",
        "text": "Text body",
        "html": "<p>HTML body</p>",
    }


def test_send_email_logs_resend_error_detail(app):
    app.config.update(
        RESEND_API_KEY="re_test_key",
        RESEND_FROM_EMAIL="StayEase <noreply@example.com>",
    )
    error = ResendError(
        code=403,
        error_type="access_denied",
        message="Sender domain is not verified",
        suggested_action="Verify your sender domain",
    )

    with app.app_context(), patch("email_service.resend.Emails.send", side_effect=error):
        with pytest.raises(
            EmailDeliveryError,
            match="HTTP 403: Sender domain is not verified",
        ):
            send_email("carl@test.com", "Subject", "Text body", "<p>HTML body</p>")


def test_send_email_logs_cloudflare_ray_id(app):
    app.config.update(
        RESEND_API_KEY="re_test_key",
        RESEND_FROM_EMAIL="StayEase <noreply@example.com>",
    )
    error = ResendError(
        code=403,
        error_type="application_error",
        message="Expected JSON response but got: text/html",
        suggested_action="",
        headers={"cf-ray": "abc123"},
    )

    with app.app_context(), patch("email_service.resend.Emails.send", side_effect=error):
        with pytest.raises(
            EmailDeliveryError,
            match="HTTP 403: Expected JSON response.*Cloudflare Ray ID: abc123",
        ):
            send_email("carl@test.com", "Subject", "Text body", "<p>HTML body</p>")
