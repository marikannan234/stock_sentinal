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
