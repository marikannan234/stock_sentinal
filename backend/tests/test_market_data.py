import math

import pandas as pd

from app.api.routes import stocks_extended


def _history_frame(close_values, multi_index: bool = False) -> pd.DataFrame:
    index = pd.date_range("2026-09-24", periods=len(close_values))
    if multi_index:
        columns = pd.MultiIndex.from_tuples([("Close", "AAPL"), ("Close", "MSFT")], names=["Price", "Ticker"])
        return pd.DataFrame({columns[0]: close_values, columns[1]: close_values}, index=index)
    return pd.DataFrame({"Close": close_values, "Open": close_values}, index=index)


def _fake_ticker(frame):
    class FakeTicker:
        def __init__(self, symbol):
            self.symbol = symbol

        def history(self, **kwargs):
            return frame

    return FakeTicker


def test_yfinance_price_reads_latest_close(monkeypatch):
    monkeypatch.setattr(stocks_extended.yf, "Ticker", _fake_ticker(_history_frame([330.0, 339.03])))

    assert stocks_extended._fetch_yfinance_current_price("AAPL") == 339.03


def test_yfinance_price_skips_trailing_missing_close(monkeypatch):
    frame = _history_frame([330.0, 339.03, math.nan])
    monkeypatch.setattr(stocks_extended.yf, "Ticker", _fake_ticker(frame))

    assert stocks_extended._fetch_yfinance_current_price("AAPL") == 339.03


def test_yfinance_price_rejects_multi_ticker_data(monkeypatch):
    # Several tickers' columns are ambiguous: never guess which one is ours.
    frame = _history_frame([330.0, 339.03], multi_index=True)
    monkeypatch.setattr(stocks_extended.yf, "Ticker", _fake_ticker(frame))

    assert stocks_extended._fetch_yfinance_current_price("AAPL") is None


def test_yfinance_price_returns_none_without_data(monkeypatch):
    monkeypatch.setattr(stocks_extended.yf, "Ticker", _fake_ticker(pd.DataFrame()))

    assert stocks_extended._fetch_yfinance_current_price("AAPL") is None


def test_yfinance_quote_fallback_includes_daily_change_and_bar_date(monkeypatch):
    monkeypatch.setattr(
        stocks_extended.yf,
        "Ticker",
        _fake_ticker(_history_frame([100.0, 110.0])),
    )

    quote = stocks_extended._fetch_yfinance_quote_data("AAPL")

    assert quote is not None
    assert quote["price"] == 110.0
    assert quote["change"] == 10.0
    assert quote["change_percent"] == 10.0
    assert quote["price_as_of"].date().isoformat() == "2026-09-25"


def test_live_quote_marks_yfinance_fallback_as_daily_data(monkeypatch):
    from datetime import datetime, timezone

    monkeypatch.setattr(stocks_extended, "_get_stock_price_from_cache", lambda symbol: None)
    monkeypatch.setattr(stocks_extended, "_fetch_finnhub_quote", lambda symbol: None)
    monkeypatch.setattr(
        stocks_extended,
        "_fetch_yfinance_quote_data",
        lambda symbol: {
            "price": 110.0,
            "change": 10.0,
            "change_percent": 10.0,
            "high": 112.0,
            "low": 98.0,
            "volume": 1234,
            "price_as_of": datetime(2026, 9, 25, tzinfo=timezone.utc),
        },
    )

    quote = stocks_extended._build_live_quote("AAPL")

    assert quote.source == "Yahoo Finance"
    assert quote.quote_type == "daily_bar"
    assert quote.price_as_of.isoformat() == "2026-09-25T00:00:00+00:00"
    assert quote.change == 10.0
