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
