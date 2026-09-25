import pandas as pd

from app.api.routes import stocks_extended


def _download_frame(close_values, multi_index: bool) -> pd.DataFrame:
    index = pd.date_range("2026-09-24", periods=len(close_values))
    if multi_index:
        columns = pd.MultiIndex.from_tuples([("Close", "AAPL"), ("Open", "AAPL")], names=["Price", "Ticker"])
        return pd.DataFrame({columns[0]: close_values, columns[1]: close_values}, index=index)
    return pd.DataFrame({"Close": close_values, "Open": close_values}, index=index)


def test_yfinance_price_parses_multi_index_columns(monkeypatch):
    frame = _download_frame([330.0, 339.03], multi_index=True)
    monkeypatch.setattr(stocks_extended.yf, "download", lambda **kwargs: frame)

    assert stocks_extended._fetch_yfinance_current_price("AAPL") == 339.03


def test_yfinance_price_parses_flat_columns(monkeypatch):
    frame = _download_frame([330.0, 339.03], multi_index=False)
    monkeypatch.setattr(stocks_extended.yf, "download", lambda **kwargs: frame)

    assert stocks_extended._fetch_yfinance_current_price("AAPL") == 339.03


def test_yfinance_price_returns_none_without_data(monkeypatch):
    monkeypatch.setattr(stocks_extended.yf, "download", lambda **kwargs: pd.DataFrame())

    assert stocks_extended._fetch_yfinance_current_price("AAPL") is None
