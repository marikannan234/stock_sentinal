import threading
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import text

from app.models.portfolio import Portfolio
from app.models.trading import Trade, TradeHistory, TradeStatus, TradeType
from app.models.user import User
from app.schemas.trading import TradeTypeStr
from app.services import trading_service
from app.services.trading_service import (
    InsufficientFundsError,
    InsufficientSharesError,
    MarketDataUnavailableError,
    TradeRequest,
    get_market_price as real_get_market_price,
)
from tests.conftest import STARTING_CASH, requires_postgres


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _trade(client, headers, trade_type, quantity, symbol="AAPL", **extra):
    return client.post(
        "/api/trade/",
        headers=headers,
        json={"symbol": symbol, "quantity": quantity, "trade_type": trade_type, **extra},
    )


def _close(client, headers, trade_id, **params):
    return client.post(f"/api/trade/{trade_id}/close", headers=headers, params=params)


def _position(db_session, symbol="AAPL"):
    db_session.expire_all()
    return db_session.query(Portfolio).filter(Portfolio.ticker == symbol).first()


def _cash(db_session, user_id=1):
    db_session.expire_all()
    return db_session.get(User, user_id).cash_balance


def _open_lots(db_session, symbol="AAPL"):
    db_session.expire_all()
    return (
        db_session.query(Trade)
        .filter(Trade.symbol == symbol, Trade.status == TradeStatus.OPEN)
        .order_by(Trade.id)
        .all()
    )


# ---------------------------------------------------------------------------
# cash balance
# ---------------------------------------------------------------------------

def test_new_user_starts_with_configured_cash(client, registered_user, db_session):
    assert _cash(db_session, registered_user["id"]) == STARTING_CASH


def test_buying_power_reports_cash(client, auth_headers, market):
    market.set("AAPL", "100")
    _trade(client, auth_headers, "BUY", 10)

    summary = client.get("/api/portfolio/summary", headers=auth_headers).json()

    assert summary["buying_power"] == pytest.approx(9000.0)


# ---------------------------------------------------------------------------
# server-side execution price
# ---------------------------------------------------------------------------

def test_buy_executes_at_server_price(client, auth_headers, db_session, market):
    market.set("AAPL", "150.00")

    response = _trade(client, auth_headers, "BUY", 10)

    assert response.status_code == 201, response.text
    assert response.json()["entry_price"] == pytest.approx(150.0)
    position = _position(db_session)
    assert position.quantity == Decimal("10")
    assert position.average_price == Decimal("150")


def test_client_price_cannot_set_execution_price(client, auth_headers, db_session, market):
    market.set("AAPL", "150.00")

    response = _trade(client, auth_headers, "BUY", 10, entry_price=1.0)

    assert response.status_code == 201, response.text
    assert response.json()["entry_price"] == pytest.approx(150.0)
    assert _cash(db_session) == STARTING_CASH - Decimal("1500.00")


def test_client_exit_price_on_close_is_ignored(client, auth_headers, db_session, market):
    market.set("AAPL", "100")
    trade_id = _trade(client, auth_headers, "BUY", 10).json()["id"]
    market.set("AAPL", "90")

    history = _close(client, auth_headers, trade_id, exit_price=1_000_000).json()

    assert history["exit_price"] == pytest.approx(90.0)
    assert history["profit_loss"] == pytest.approx(-100.0)
    assert _cash(db_session) == STARTING_CASH - Decimal("100.00")


def test_trade_is_refused_without_market_price(client, auth_headers, db_session):
    response = _trade(client, auth_headers, "BUY", 1, symbol="NOPRICE", entry_price=10)

    assert response.status_code == 503
    assert db_session.query(Trade).count() == 0
    assert _cash(db_session) == STARTING_CASH


class _Quote:
    def __init__(self, price):
        self.price = price


def test_market_price_rejects_zero_quotes(monkeypatch):
    from app.api.routes import stocks_extended

    monkeypatch.setattr(stocks_extended, "_build_live_quote", lambda symbol: _Quote(0.0))

    with pytest.raises(MarketDataUnavailableError):
        real_get_market_price("AAPL")


def test_market_price_maps_quote_failure(monkeypatch):
    from app.api.routes import stocks_extended

    def _fail(symbol):
        raise HTTPException(status_code=502, detail="both providers failed")

    monkeypatch.setattr(stocks_extended, "_build_live_quote", _fail)

    with pytest.raises(MarketDataUnavailableError):
        real_get_market_price("AAPL")


def test_market_price_returns_decimal(monkeypatch):
    from app.api.routes import stocks_extended

    monkeypatch.setattr(stocks_extended, "_build_live_quote", lambda symbol: _Quote(187.4321))

    assert real_get_market_price("AAPL") == Decimal("187.432100")


# ---------------------------------------------------------------------------
# BUY / SELL / positions
# ---------------------------------------------------------------------------

def test_buy_decreases_cash(client, auth_headers, db_session, market):
    market.set("AAPL", "123.45")

    _trade(client, auth_headers, "BUY", 4)

    assert _cash(db_session) == STARTING_CASH - Decimal("493.80")


def test_second_buy_updates_quantity_and_average_price(client, auth_headers, db_session, market):
    market.set("AAPL", "100")
    _trade(client, auth_headers, "BUY", 10)
    market.set("AAPL", "200")
    _trade(client, auth_headers, "BUY", 10)

    position = _position(db_session)
    assert position.quantity == Decimal("20")
    assert position.average_price == Decimal("150")


def test_insufficient_cash_rejects_buy(client, auth_headers, db_session, market):
    market.set("AAPL", "1000")

    response = _trade(client, auth_headers, "BUY", 11)  # $11,000 > $10,000

    assert response.status_code == 400
    assert "Insufficient cash" in response.json()["detail"]
    assert _cash(db_session) == STARTING_CASH
    assert _position(db_session) is None
    assert db_session.query(Trade).count() == 0


def test_buy_spending_exactly_all_cash_is_allowed(client, auth_headers, db_session, market):
    market.set("AAPL", "1000")

    response = _trade(client, auth_headers, "BUY", 10)

    assert response.status_code == 201
    assert _cash(db_session) == Decimal("0.00")


def test_sell_increases_cash_and_reduces_position(client, auth_headers, db_session, market):
    market.set("AAPL", "100")
    _trade(client, auth_headers, "BUY", 10)
    market.set("AAPL", "120")

    response = _trade(client, auth_headers, "SELL", 4)

    assert response.status_code == 201, response.text
    assert response.json()["status"] == "executed"
    assert _position(db_session).quantity == Decimal("6")
    assert _cash(db_session) == STARTING_CASH - Decimal("1000") + Decimal("480")


def test_selling_entire_position_removes_it(client, auth_headers, db_session, market):
    market.set("AAPL", "100")
    _trade(client, auth_headers, "BUY", 10)

    _trade(client, auth_headers, "SELL", 10)

    assert _position(db_session) is None
    assert _open_lots(db_session) == []


def test_sell_more_than_owned_is_rejected(client, auth_headers, db_session, market):
    market.set("AAPL", "100")
    _trade(client, auth_headers, "BUY", 5)
    cash_before = _cash(db_session)

    response = _trade(client, auth_headers, "SELL", 6)

    assert response.status_code == 400
    assert "Insufficient shares" in response.json()["detail"]
    assert _position(db_session).quantity == Decimal("5")
    assert _cash(db_session) == cash_before
    assert db_session.query(Trade).count() == 1


def test_sell_without_position_is_rejected(client, auth_headers, db_session, market):
    market.set("AAPL", "100")

    response = _trade(client, auth_headers, "SELL", 1)

    assert response.status_code == 400
    assert db_session.query(Trade).count() == 0


def test_sell_closes_lots_oldest_first_with_correct_pnl(client, auth_headers, db_session, market):
    market.set("AAPL", "100")
    first = _trade(client, auth_headers, "BUY", 10).json()["id"]
    market.set("AAPL", "200")
    second = _trade(client, auth_headers, "BUY", 10).json()["id"]
    market.set("AAPL", "150")

    _trade(client, auth_headers, "SELL", 15)

    db_session.expire_all()
    history = db_session.query(TradeHistory).order_by(TradeHistory.id).all()
    assert [(h.trade_id, h.quantity, h.profit_loss) for h in history] == [
        (first, Decimal("10"), Decimal("500.00")),   # 10 x (150 - 100)
        (second, Decimal("5"), Decimal("-250.00")),  # 5 x (150 - 200)
    ]
    lots = _open_lots(db_session)
    assert [(lot.id, lot.quantity) for lot in lots] == [(second, Decimal("5"))]
    position = _position(db_session)
    assert (position.quantity, position.average_price) == (Decimal("5"), Decimal("200"))
    # 10,000 - 1,000 - 2,000 + 15 x 150
    assert _cash(db_session) == Decimal("9250.00")


def test_trade_type_is_stored_as_canonical_value(client, auth_headers, db_session, market):
    market.set("AAPL", "10")
    _trade(client, auth_headers, "BUY", 2)
    response = _trade(client, auth_headers, "SELL", 1)

    assert response.json()["trade_type"] == "SELL"
    stored = db_session.execute(text("SELECT trade_type FROM trades ORDER BY id")).scalars().all()
    assert stored == ["BUY", "SELL"]


def test_invalid_trade_type_is_rejected(client, auth_headers):
    response = _trade(client, auth_headers, "TradeTypeStr.BUY", 1)

    assert response.status_code == 422


@pytest.mark.parametrize("trade_type", [TradeTypeStr.BUY, TradeType.BUY, "BUY"])
def test_engine_accepts_every_trade_type_form(db_session, registered_user, market, trade_type):
    market.set("MSFT", "10")

    trading_service.execute_trade(
        db_session,
        registered_user["id"],
        TradeRequest(symbol="msft", quantity=3, trade_type=trade_type),
    )

    assert _position(db_session, "MSFT").quantity == Decimal("3")


# ---------------------------------------------------------------------------
# closing trades, SHORT, CLOSE
# ---------------------------------------------------------------------------

def test_closing_long_trade_records_profit_and_clears_position(client, auth_headers, db_session, market):
    market.set("AAPL", "100")
    trade_id = _trade(client, auth_headers, "BUY", 10).json()["id"]
    market.set("AAPL", "110")

    history = _close(client, auth_headers, trade_id).json()

    assert history["profit_loss"] == pytest.approx(100.0)
    assert history["profit_loss_percent"] == pytest.approx(10.0)
    assert history["status"] == "closed"
    assert _position(db_session) is None
    assert _cash(db_session) == STARTING_CASH + Decimal("100.00")


def test_short_opens_negative_position_and_reserves_collateral(client, auth_headers, db_session, market):
    market.set("TSLA", "200")

    response = _trade(client, auth_headers, "SHORT", 5, symbol="TSLA")

    assert response.status_code == 201, response.text
    position = _position(db_session, "TSLA")
    assert position.quantity == Decimal("-5")
    assert position.average_price == Decimal("200")
    assert _cash(db_session) == STARTING_CASH - Decimal("1000.00")


def test_closing_short_profits_when_price_falls(client, auth_headers, db_session, market):
    market.set("TSLA", "100")
    trade_id = _trade(client, auth_headers, "SHORT", 10, symbol="TSLA").json()["id"]
    market.set("TSLA", "90")

    history = _close(client, auth_headers, trade_id).json()

    assert history["profit_loss"] == pytest.approx(100.0)
    assert history["profit_loss_percent"] == pytest.approx(10.0)
    assert _position(db_session, "TSLA") is None
    assert _cash(db_session) == STARTING_CASH + Decimal("100.00")


def test_closing_short_loses_when_price_rises(client, auth_headers, db_session, market):
    market.set("TSLA", "100")
    trade_id = _trade(client, auth_headers, "SHORT", 10, symbol="TSLA").json()["id"]
    market.set("TSLA", "120")

    history = _close(client, auth_headers, trade_id).json()

    assert history["profit_loss"] == pytest.approx(-200.0)
    assert history["profit_loss_percent"] == pytest.approx(-20.0)
    assert _position(db_session, "TSLA") is None
    assert _cash(db_session) == STARTING_CASH - Decimal("200.00")


def test_cannot_buy_while_short_or_short_while_long(client, auth_headers, market):
    market.set("TSLA", "100")
    market.set("AAPL", "100")
    _trade(client, auth_headers, "SHORT", 1, symbol="TSLA")
    _trade(client, auth_headers, "BUY", 1, symbol="AAPL")

    assert _trade(client, auth_headers, "BUY", 1, symbol="TSLA").status_code == 400
    assert _trade(client, auth_headers, "SHORT", 1, symbol="AAPL").status_code == 400


def test_close_type_flattens_whole_position(client, auth_headers, db_session, market):
    market.set("AAPL", "100")
    _trade(client, auth_headers, "BUY", 3)
    _trade(client, auth_headers, "BUY", 2)
    market.set("AAPL", "110")

    response = _trade(client, auth_headers, "CLOSE", 1)

    assert response.status_code == 201, response.text
    assert response.json()["quantity"] == pytest.approx(5.0)
    assert _position(db_session) is None
    assert _open_lots(db_session) == []
    assert _cash(db_session) == STARTING_CASH + Decimal("50.00")


def test_close_type_without_position_is_rejected(client, auth_headers, market):
    market.set("AAPL", "100")

    assert _trade(client, auth_headers, "CLOSE", 1).status_code == 400


def test_closed_trade_cannot_be_reopened_and_closed_twice(client, auth_headers, db_session, market):
    market.set("AAPL", "100")
    trade_id = _trade(client, auth_headers, "BUY", 1).json()["id"]
    assert _close(client, auth_headers, trade_id).status_code == 200

    reopen = client.put(f"/api/trade/{trade_id}", headers=auth_headers, json={"status": "open"})
    second_close = _close(client, auth_headers, trade_id)

    assert reopen.status_code == 400
    assert second_close.status_code == 400
    assert len(client.get("/api/trade/history/list", headers=auth_headers).json()) == 1
    assert _cash(db_session) == STARTING_CASH


def test_update_cannot_change_status_or_price(client, auth_headers, market):
    market.set("AAPL", "100")
    trade_id = _trade(client, auth_headers, "BUY", 1).json()["id"]

    for payload in ({"status": "closed"}, {"status": "cancelled"}, {"current_price": 1}):
        response = client.put(f"/api/trade/{trade_id}", headers=auth_headers, json=payload)
        assert response.status_code == 400, payload

    notes = client.put(f"/api/trade/{trade_id}", headers=auth_headers, json={"notes": "long term"})
    assert notes.status_code == 200
    assert notes.json()["notes"] == "long term"


def test_executed_sell_record_cannot_be_closed(client, auth_headers, market):
    market.set("AAPL", "100")
    _trade(client, auth_headers, "BUY", 2)
    sell_id = _trade(client, auth_headers, "SELL", 1).json()["id"]

    assert _close(client, auth_headers, sell_id).status_code == 400


def test_trade_endpoints_require_authentication(client):
    assert _trade(client, {}, "BUY", 1).status_code == 401


# ---------------------------------------------------------------------------
# /portfolio writes go through the same engine
# ---------------------------------------------------------------------------

@pytest.fixture()
def symbol_search_ok(monkeypatch):
    from app.api.routes import portfolio

    monkeypatch.setattr(portfolio, "_finnhub_symbol_search", lambda q: [{"symbol": q}])


def test_portfolio_add_buys_at_market_price(client, auth_headers, db_session, market, symbol_search_ok):
    market.set("AAPL", "150")

    response = client.post(
        "/api/portfolio",
        headers=auth_headers,
        json={"ticker": "AAPL", "quantity": 2, "price": 0.01},
    )

    assert response.status_code == 201, response.text
    assert response.json()[0]["average_price"] == pytest.approx(150.0)
    assert _cash(db_session) == STARTING_CASH - Decimal("300.00")


def test_portfolio_delete_sells_only_requested_quantity(client, auth_headers, db_session, market):
    market.set("AAPL", "100")
    _trade(client, auth_headers, "BUY", 10)

    response = client.request(
        "DELETE", "/api/portfolio/AAPL", headers=auth_headers, json={"quantity": 1}
    )

    assert response.status_code == 200, response.text
    assert _position(db_session).quantity == Decimal("9")


def test_portfolio_delete_without_quantity_closes_position(client, auth_headers, db_session, market):
    market.set("AAPL", "100")
    _trade(client, auth_headers, "BUY", 10)

    response = client.delete("/api/portfolio/AAPL", headers=auth_headers)

    assert response.status_code == 200, response.text
    assert response.json() == []
    assert _position(db_session) is None
    assert _cash(db_session) == STARTING_CASH


def test_portfolio_delete_of_unknown_ticker_is_a_no_op(client, auth_headers):
    response = client.delete("/api/portfolio/ZZZZ", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# precision
# ---------------------------------------------------------------------------

def test_decimal_math_leaves_no_float_residue(client, auth_headers, db_session, market):
    market.set("AAPL", "10.10")
    _trade(client, auth_headers, "BUY", 0.1)
    _trade(client, auth_headers, "BUY", 0.2)

    position = _position(db_session)
    assert isinstance(position.quantity, Decimal)
    assert position.quantity == Decimal("0.3")
    assert _cash(db_session) == STARTING_CASH - Decimal("1.01") - Decimal("2.02")

    _trade(client, auth_headers, "SELL", 0.3)

    assert _position(db_session) is None
    cash = _cash(db_session)
    assert isinstance(cash, Decimal)
    # 1.01 + 2.02 paid, 0.3 x 10.10 = 3.03 received
    assert cash == STARTING_CASH


def test_money_is_rounded_to_cents(client, auth_headers, db_session, market):
    market.set("AAPL", "33.333333")

    _trade(client, auth_headers, "BUY", 3)  # 99.999999 -> 100.00

    assert _cash(db_session) == STARTING_CASH - Decimal("100.00")


# ---------------------------------------------------------------------------
# atomicity and concurrency
# ---------------------------------------------------------------------------

def test_failure_mid_trade_rolls_everything_back(db_session, registered_user, market, monkeypatch):
    market.set("AAPL", "100")

    def _boom(*args, **kwargs):
        raise RuntimeError("simulated crash after cash and lot were written")

    monkeypatch.setattr(trading_service, "_sync_position", _boom)

    with pytest.raises(RuntimeError):
        trading_service.execute_trade(
            db_session,
            registered_user["id"],
            TradeRequest(symbol="AAPL", quantity=5, trade_type="BUY"),
        )

    assert _cash(db_session, registered_user["id"]) == STARTING_CASH
    assert db_session.query(Trade).count() == 0
    assert _position(db_session) is None


def _run_concurrently(session_factory, user_id, requests):
    barrier = threading.Barrier(len(requests))
    results = []
    lock = threading.Lock()

    def worker(request):
        session = session_factory()
        try:
            barrier.wait()
            trading_service.execute_trade(session, user_id, request)
            outcome = "ok"
        except (InsufficientFundsError, InsufficientSharesError) as exc:
            outcome = type(exc).__name__
        finally:
            session.close()
        with lock:
            results.append(outcome)

    threads = [threading.Thread(target=worker, args=(r,)) for r in requests]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return results


@requires_postgres
def test_concurrent_sells_cannot_oversell(session_factory, db_session, registered_user, market):
    market.set("AAPL", "100")
    trading_service.execute_trade(
        db_session, registered_user["id"], TradeRequest("AAPL", 5, "BUY")
    )

    results = _run_concurrently(
        session_factory, registered_user["id"], [TradeRequest("AAPL", 1, "SELL")] * 10
    )

    assert results.count("ok") == 5
    assert results.count("InsufficientSharesError") == 5
    assert _position(db_session) is None
    assert _cash(db_session, registered_user["id"]) == STARTING_CASH


@requires_postgres
def test_concurrent_buys_cannot_overspend(session_factory, db_session, registered_user, market):
    market.set("AAPL", "4000")  # cash covers two buys of 1 share, not three

    results = _run_concurrently(
        session_factory, registered_user["id"], [TradeRequest("AAPL", 1, "BUY")] * 6
    )

    assert results.count("ok") == 2
    assert results.count("InsufficientFundsError") == 4
    assert _position(db_session).quantity == Decimal("2")
    assert _cash(db_session, registered_user["id"]) == Decimal("2000.00")
