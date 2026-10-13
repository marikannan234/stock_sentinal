from app.config import settings
from app.services import email_smtp


def test_dashboard_url_prefers_explicit_frontend_url(monkeypatch):
    monkeypatch.setattr(settings, "FRONTEND_URL", "https://stocksentinel.example/")
    assert email_smtp._dashboard_url() == "https://stocksentinel.example/dashboard"


def test_alert_email_escapes_html_and_uses_configured_dashboard(monkeypatch):
    monkeypatch.setattr(settings, "FRONTEND_URL", "https://stocksentinel.example")
    captured = {}
    monkeypatch.setattr(
        email_smtp,
        "send_alert_email_smtp",
        lambda **kwargs: captured.update(kwargs) or True,
    )

    assert email_smtp.send_alert_notification(
        user_email="user@example.com",
        symbol="<img src=x>",
        current_price=123.45,
        condition="",
        target_value=None,
        triggered_at="2026-10-13T10:00:00<script>",
        alert_type="custom",
        description="<script>alert(1)</script>",
    )

    body = captured["html_body"]
    assert "<img src=x>" not in body
    assert "<script>" not in body
    assert "&lt;img src=x&gt;" in body
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in body
    assert 'href="https://stocksentinel.example/dashboard"' in body
    assert "http://localhost:3000/dashboard" not in body
    assert "https://stocksentinel.example/dashboard" in captured["text_body"]


def test_smtp_uses_implicit_ssl_when_configured(monkeypatch):
    calls = []

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            calls.append(("connect", host, port, timeout))

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def starttls(self):
            calls.append(("starttls",))

        def login(self, username, password):
            calls.append(("login", username, password))

        def send_message(self, message):
            calls.append(("send", message["To"]))

    monkeypatch.setattr(settings, "ENABLE_EMAIL_NOTIFICATIONS", True)
    monkeypatch.setattr(settings, "MAIL_SSL_TLS", True)
    monkeypatch.setattr(settings, "MAIL_STARTTLS", True)
    monkeypatch.setattr(email_smtp.smtplib, "SMTP_SSL", FakeSMTP)

    assert email_smtp.send_alert_email_smtp(
        "user@example.com", "Subject", "<p>Alert</p>", "Alert"
    )
    assert calls[0][0] == "connect"
    assert not any(call[0] == "starttls" for call in calls)
    assert any(call[0] == "send" for call in calls)
