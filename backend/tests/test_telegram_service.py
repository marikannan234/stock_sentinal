import pytest

from app.config import settings
from app.services import telegram_service


def test_telegram_notification_is_disabled_by_default(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_TELEGRAM_NOTIFICATIONS", False)
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "test-token")
    assert telegram_service.send_telegram_notification(chat_id="123", message="hello") is False


def test_telegram_notification_sends_and_checks_api_response(monkeypatch):
    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"ok": True}

    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return Response()

    monkeypatch.setattr(settings, "ENABLE_TELEGRAM_NOTIFICATIONS", True)
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setattr(telegram_service.requests, "post", fake_post)

    assert telegram_service.send_telegram_notification(chat_id="123", message="hello") is True
    assert captured["json"]["chat_id"] == "123"
    assert captured["json"]["text"] == "hello"
    assert captured["timeout"] == 5


def test_telegram_notification_returns_false_when_api_rejects(monkeypatch):
    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"ok": False}

    monkeypatch.setattr(settings, "ENABLE_TELEGRAM_NOTIFICATIONS", True)
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setattr(telegram_service.requests, "post", lambda *args, **kwargs: Response())
    assert telegram_service.send_telegram_notification(chat_id="123", message="hello") is False
