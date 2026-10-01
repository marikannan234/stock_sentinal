"""
Concurrent quote lookups must never return another symbol's price, and the
market snapshot must never contain hard-coded placeholder prices.

Only the network layer is faked: `yfinance.Ticker.history` returns a known
price per symbol after a short delay. Everything above it runs for real,
including yfinance's own `download()`, which assembles its result from
module-level shared state. That is the code path that mixed symbols up when
two lookups overlapped (e.g. NVDA returned GOOGL's price).
"""

import threading
import time
from decimal import Decimal

import pandas as pd
import pytest
import yfinance
from fastapi import HTTPException

from app.api.routes import stocks_extended
from app.models.trading import Trade
from app.services import trading_service
from app.services.trading_service import (
    MarketDataUnavailableError,
    get_market_price as real_get_market_price,
)

PRICES = {"AAPL": 101.0, "MSFT": 202.0, "GOOGL": 303.0, "NVDA": 404.0, "AMZN": 505.0, "TSLA": 606.0}
SYMBOLS = ["AAPL", "MSFT", "GOOGL", "NVDA"]
ROUNDS = 5


def _frame(price: float) -> pd.DataFrame:
    index = pd.date_range("2026-09-29", periods=2, tz="America/New_York")
    return pd.DataFrame(
        {
            "Open": [price - 2, price - 1],
            "High": [price, price + 1],
            "Low": [price - 3, price - 2],
            "Close": [price - 1, price],
            "Volume": [1_000, 2_000],
        },
        index=index,
    )


def _reset_caches():
    stocks_extended._stock_price_cache.clear()
    with stocks_extended._top_movers_cache_lock:
        stocks_extended.top_movers_cache.update(data=None, timestamp=0.0)
    with stocks_extended._market_summary_cache_lock:
        stocks_extended._market_summary_cache.update(data=None, timestamp=0.0)


@pytest.fixture()
def fake_yahoo(monkeypatch):
    """Per-symbol prices from a fake Yahoo; unknown symbols fail like a real lookup."""

    def history(self, *args, **kwargs):
        time.sleep(0.05)  # keep concurrent lookups overlapping
        price = PRICES.get(self.ticker)
        if price is None:
            raise ValueError(f"{self.ticker}: possibly delisted; no price data found")
        return _frame(price)

    monkeypatch.setattr(yfinance.Ticker, "history", history)
    monkeypatch.setattr(stocks_extended.settings, "FINNHUB_API_KEY", None)
    _reset_caches()
    yield
    _reset_caches()


def _run_concurrently(fn, symbols, rounds=ROUNDS):
    """Call fn(symbol) for every symbol at the same instant, `rounds` times."""
    results, errors = [], []
    lock = threading.Lock()

    for _ in range(rounds):
        stocks_extended._stock_price_cache.clear()
        barrier = threading.Barrier(len(symbols))

        def run(symbol):
            barrier.wait()
            try:
                value = fn(symbol)
                with lock:
                    results.append((symbol, value))
            except Exception as exc:  # collected and asserted by the caller
                with lock:
                    errors.append((symbol, exc))

        threads = [threading.Thread(target=run, args=(s,)) for s in symbols]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)

    return results, errors


# ---------------------------------------------------------------------------
# single-symbol quotes (GET /stocks/{symbol}/price, trading engine)
# ---------------------------------------------------------------------------

def test_concurrent_quotes_return_each_symbols_own_price(fake_yahoo):
    results, errors = _run_concurrently(stocks_extended._build_live_quote, SYMBOLS)

    assert errors == []
    assert len(results) == len(SYMBOLS) * ROUNDS
    for requested, quote in results:
        assert quote.symbol == requested
        assert quote.price == PRICES[requested], f"{requested} got {quote.price}"


def test_concurrent_price_endpoint_returns_matching_prices(fake_yahoo, client):
    results, errors = _run_concurrently(
        lambda symbol: client.get(f"/api/stocks/{symbol}/price").json(), SYMBOLS
    )

    assert errors == []
    for requested, body in results:
        assert body["symbol"] == requested
        assert body["price"] == PRICES[requested], f"{requested} got {body['price']}"


def test_concurrent_trading_prices_match_symbol(fake_yahoo):
    results, errors = _run_concurrently(real_get_market_price, SYMBOLS)

    assert errors == []
    for requested, price in results:
        assert price == Decimal(str(PRICES[requested])), f"{requested} got {price}"


def test_unavailable_quote_fails_instead_of_borrowing_another_price(fake_yahoo):
    results, errors = _run_concurrently(stocks_extended._build_live_quote, SYMBOLS + ["NOPRICE"])

    for requested, quote in results:
        assert requested != "NOPRICE", f"NOPRICE was priced at {quote.price}"
        assert quote.price == PRICES[requested]
    assert [symbol for symbol, _ in errors] == ["NOPRICE"] * ROUNDS
    assert all(isinstance(exc, HTTPException) and exc.status_code == 502 for _, exc in errors)


def test_unavailable_quote_cannot_be_traded(fake_yahoo):
    with pytest.raises(MarketDataUnavailableError):
        real_get_market_price("NOPRICE")


# ---------------------------------------------------------------------------
# trades use the real quote path while other lookups run
# ---------------------------------------------------------------------------

BUYS = 10


def _hammer_other_quotes(stop: threading.Event):
    while not stop.is_set():
        for symbol in ("MSFT", "GOOGL", "NVDA"):
            stocks_extended._stock_price_cache.pop(symbol, None)
            stocks_extended._build_live_quote(symbol)


def test_buy_fills_at_its_own_symbols_price_during_concurrent_lookups(
    fake_yahoo, client, auth_headers, db_session, monkeypatch
):
    monkeypatch.setattr(trading_service, "get_market_price", real_get_market_price)
    stop = threading.Event()
    background = [threading.Thread(target=_hammer_other_quotes, args=(stop,)) for _ in range(4)]
    for thread in background:
        thread.start()
    try:
        for _ in range(BUYS):
            stocks_extended._stock_price_cache.pop("AAPL", None)
            response = client.post(
                "/api/trade/",
                headers=auth_headers,
                # entry_price is client input and must be ignored
                json={"symbol": "AAPL", "quantity": 1, "trade_type": "BUY", "entry_price": 1.0},
            )
            assert response.status_code == 201, response.text
    finally:
        stop.set()
        for thread in background:
            thread.join(timeout=30)

    db_session.expire_all()
    prices = [trade.entry_price for trade in db_session.query(Trade).filter(Trade.symbol == "AAPL")]
    assert prices == [Decimal("101.000000")] * BUYS


def test_buy_without_a_valid_quote_writes_nothing(fake_yahoo, client, auth_headers, db_session, monkeypatch):
    monkeypatch.setattr(trading_service, "get_market_price", real_get_market_price)

    response = client.post(
        "/api/trade/",
        headers=auth_headers,
        json={"symbol": "NOPRICE", "quantity": 1, "trade_type": "BUY", "entry_price": 10.0},
    )

    assert response.status_code == 503
    db_session.expire_all()
    assert db_session.query(Trade).count() == 0


# ---------------------------------------------------------------------------
# market snapshot (ribbon / market summary / dashboard)
# ---------------------------------------------------------------------------

def test_batch_snapshot_stays_complete_and_correct_during_single_lookups(fake_yahoo):
    batch_symbols = list(PRICES)
    batches = []

    def run_batch():
        for _ in range(3):
            batches.append(stocks_extended._fetch_market_quotes_batch(batch_symbols))

    batch_thread = threading.Thread(target=run_batch)
    batch_thread.start()
    results, errors = _run_concurrently(stocks_extended._build_live_quote, SYMBOLS, rounds=3)
    batch_thread.join(timeout=60)

    assert errors == []
    for requested, quote in results:
        assert quote.price == PRICES[requested]
    for quotes in batches:
        assert sorted(q.symbol for q in quotes) == sorted(batch_symbols)
        for quote in quotes:
            assert quote.price == PRICES[quote.symbol]


def test_no_hard_coded_placeholder_quotes_exist():
    assert not hasattr(stocks_extended, "FALLBACK_MARKET_QUOTES")
    assert not hasattr(stocks_extended, "_get_fallback_market_quotes")


def test_snapshot_is_empty_not_fake_when_live_data_is_unavailable(monkeypatch):
    _reset_caches()
    monkeypatch.setattr(stocks_extended, "_fetch_market_quotes_batch", lambda symbols: [])

    assert stocks_extended._get_market_snapshot_quotes() == []
    summary = stocks_extended._build_market_summary_from_quotes([])
    assert summary.top_gainers == summary.top_losers == summary.most_active == []
    _reset_caches()


def test_partial_snapshot_is_not_padded_with_placeholders(monkeypatch, fake_yahoo):
    live = [q for q in stocks_extended._fetch_market_quotes_batch(["AAPL", "MSFT"])]
    _reset_caches()
    monkeypatch.setattr(stocks_extended, "_fetch_market_quotes_batch", lambda symbols: live)

    quotes = stocks_extended._get_market_snapshot_quotes()

    assert [(q.symbol, q.price) for q in quotes] == [("AAPL", 101.0), ("MSFT", 202.0)]


def test_failed_refresh_keeps_last_real_snapshot(monkeypatch, fake_yahoo):
    live = stocks_extended._fetch_market_quotes_batch(["AAPL", "MSFT"])
    _reset_caches()
    monkeypatch.setattr(stocks_extended, "_fetch_market_quotes_batch", lambda symbols: live)
    first = stocks_extended._get_market_snapshot_quotes()

    # The cached snapshot expires and the next live fetch returns nothing.
    with stocks_extended._top_movers_cache_lock:
        stocks_extended.top_movers_cache["timestamp"] = 0.0
    monkeypatch.setattr(stocks_extended, "_fetch_market_quotes_batch", lambda symbols: [])

    assert stocks_extended._get_market_snapshot_quotes() == first


def test_simultaneous_snapshot_requests_share_one_download(monkeypatch, fake_yahoo):
    live = stocks_extended._fetch_market_quotes_batch(["AAPL", "MSFT"])
    _reset_caches()
    calls = []

    def slow_batch(symbols):
        calls.append(symbols)
        time.sleep(0.2)
        return live

    monkeypatch.setattr(stocks_extended, "_fetch_market_quotes_batch", slow_batch)
    results, errors = _run_concurrently(lambda _: stocks_extended._get_market_snapshot_quotes(), ["ribbon", "market", "other"], rounds=1)

    assert errors == []
    assert len(calls) == 1
    assert all(quotes == live for _, quotes in results)


def test_dashboard_sections_show_no_placeholder_prices(client, auth_headers, monkeypatch):
    _reset_caches()
    monkeypatch.setattr(stocks_extended, "_fetch_market_quotes_batch", lambda symbols: [])

    ribbon = client.get("/api/dashboard/ribbon", headers=auth_headers)
    market = client.get("/api/dashboard/market", headers=auth_headers)

    assert ribbon.status_code == 200 and market.status_code == 200
    assert ribbon.json()["stocks"] == [] and ribbon.json()["total_count"] == 0
    body = market.json()
    assert body["top_gainers"] == body["top_losers"] == body["most_active"] == []
    _reset_caches()


def test_dashboard_fallbacks_on_error_show_no_placeholder_prices(client, auth_headers, monkeypatch):
    from app.api.routes import dashboard

    def boom(*args, **kwargs):
        raise RuntimeError("market data down")

    monkeypatch.setattr(dashboard, "get_live_stock_quotes", boom)
    monkeypatch.setattr(dashboard, "get_market_summary", boom)

    ribbon = client.get("/api/dashboard/ribbon", headers=auth_headers).json()
    market = client.get("/api/dashboard/market", headers=auth_headers).json()

    assert ribbon["stocks"] == []
    assert market["top_gainers"] == market["top_losers"] == market["most_active"] == []
