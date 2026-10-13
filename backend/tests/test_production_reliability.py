from app.api.routes import stocks_extended
from app.services import indicator_service


def test_empty_market_snapshot_is_negative_cached(monkeypatch):
    with stocks_extended._top_movers_cache_lock:
        stocks_extended.top_movers_cache.update(data=None, timestamp=0.0)

    calls = []

    def unavailable(symbols):
        calls.append(list(symbols))
        return []

    monkeypatch.setattr(stocks_extended, "_fetch_market_quotes_batch", unavailable)

    assert stocks_extended._get_market_snapshot_quotes() == []
    assert stocks_extended._get_market_snapshot_quotes() == []
    assert len(calls) == 1

    with stocks_extended._top_movers_cache_lock:
        stocks_extended.top_movers_cache.update(data=None, timestamp=0.0)


def test_indicator_history_window_scales_with_requested_period():
    assert indicator_service._history_window(14) == "3mo"
    assert indicator_service._history_window(50) == "6mo"
    assert indicator_service._history_window(100) == "1y"
    assert indicator_service._history_window(200) == "2y"
    assert indicator_service._history_window(300) == "5y"
