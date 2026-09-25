import pytest
from sqlalchemy import text

from app.api.routes.trading import _update_portfolio_from_trade
from app.models.portfolio import Portfolio
from app.models.trading import Trade, TradeType
from app.schemas.trading import TradeTypeStr


def _trade(client, headers, trade_type, quantity, price=100.0, symbol="AAPL"):
    return client.post(
        "/api/trade/",
        headers=headers,
        json={
            "symbol": symbol,
            "quantity": quantity,
            "entry_price": price,
            "trade_type": trade_type,
        },
    )


def _position(db_session, symbol="AAPL"):
    db_session.expire_all()
    return db_session.query(Portfolio).filter(Portfolio.ticker == symbol).first()


def test_buy_creates_position(client, auth_headers, db_session):
    response = _trade(client, auth_headers, "BUY", 10, price=150.0)

    assert response.status_code == 201, response.text
    position = _position(db_session)
    assert position is not None
    assert position.quantity == 10
    assert position.average_price == 150.0


def test_second_buy_updates_quantity_and_average_price(client, auth_headers, db_session):
    _trade(client, auth_headers, "BUY", 10, price=100.0)
    response = _trade(client, auth_headers, "BUY", 10, price=200.0)

    assert response.status_code == 201, response.text
    position = _position(db_session)
    assert position.quantity == 20
    assert position.average_price == pytest.approx(150.0)


def test_sell_owned_shares_reduces_position(client, auth_headers, db_session):
    _trade(client, auth_headers, "BUY", 10)
    response = _trade(client, auth_headers, "SELL", 4)

    assert response.status_code == 201, response.text
    assert _position(db_session).quantity == 6


def test_selling_entire_position_removes_it(client, auth_headers, db_session):
    _trade(client, auth_headers, "BUY", 10)
    response = _trade(client, auth_headers, "SELL", 10)

    assert response.status_code == 201, response.text
    assert _position(db_session) is None


def test_fractional_float_quantities_close_cleanly(client, auth_headers, db_session):
    _trade(client, auth_headers, "BUY", 0.1)
    _trade(client, auth_headers, "BUY", 0.2)
    response = _trade(client, auth_headers, "SELL", 0.3)

    assert response.status_code == 201, response.text
    assert _position(db_session) is None


def test_sell_more_than_owned_is_rejected(client, auth_headers, db_session):
    _trade(client, auth_headers, "BUY", 5)
    response = _trade(client, auth_headers, "SELL", 6)

    assert response.status_code == 400
    assert "Insufficient shares" in response.json()["detail"]
    assert _position(db_session).quantity == 5
    # The rejected SELL must not leave a trade row behind.
    assert db_session.query(Trade).count() == 1


def test_sell_without_position_is_rejected(client, auth_headers, db_session):
    response = _trade(client, auth_headers, "SELL", 1)

    assert response.status_code == 400
    assert _position(db_session) is None
    assert db_session.query(Trade).count() == 0


def test_trade_type_is_stored_as_canonical_value(client, auth_headers, db_session):
    _trade(client, auth_headers, "BUY", 2)
    response = _trade(client, auth_headers, "SELL", 1)

    assert response.json()["trade_type"] == "SELL"
    stored = db_session.execute(text("SELECT trade_type FROM trades ORDER BY id")).scalars().all()
    assert stored == ["BUY", "SELL"]


def test_invalid_trade_type_is_rejected(client, auth_headers):
    response = _trade(client, auth_headers, "TradeTypeStr.BUY", 1)

    assert response.status_code == 422


@pytest.mark.parametrize("trade_type", [TradeTypeStr.BUY, TradeType.BUY, "BUY"])
def test_portfolio_helper_accepts_every_trade_type_form(db_session, registered_user, trade_type):
    _update_portfolio_from_trade(
        user_id=registered_user["id"],
        symbol="msft",
        quantity=3,
        price=10.0,
        trade_type=trade_type,
        db=db_session,
    )
    db_session.flush()

    position = _position(db_session, "MSFT")
    assert position is not None
    assert position.quantity == 3


def _close(client, headers, trade_id, exit_price):
    return client.post(
        f"/api/trade/{trade_id}/close",
        headers=headers,
        params={"exit_price": exit_price},
    )


def test_closing_long_trade_records_profit(client, auth_headers):
    trade_id = _trade(client, auth_headers, "BUY", 10, price=100.0).json()["id"]

    history = _close(client, auth_headers, trade_id, 110.0).json()

    assert history["profit_loss"] == pytest.approx(100.0)
    assert history["profit_loss_percent"] == pytest.approx(10.0)


def test_closing_short_trade_profits_when_price_falls(client, auth_headers):
    trade_id = _trade(client, auth_headers, "SHORT", 10, price=100.0).json()["id"]

    history = _close(client, auth_headers, trade_id, 90.0).json()

    assert history["profit_loss"] == pytest.approx(100.0)
    assert history["profit_loss_percent"] == pytest.approx(10.0)


def test_closing_short_trade_loses_when_price_rises(client, auth_headers):
    trade_id = _trade(client, auth_headers, "SHORT", 10, price=100.0).json()["id"]

    history = _close(client, auth_headers, trade_id, 120.0).json()

    assert history["profit_loss"] == pytest.approx(-200.0)
    assert history["profit_loss_percent"] == pytest.approx(-20.0)


def test_closed_trade_cannot_be_reopened_and_closed_twice(client, auth_headers):
    trade_id = _trade(client, auth_headers, "BUY", 1).json()["id"]
    assert _close(client, auth_headers, trade_id, 101.0).status_code == 200

    reopen = client.put(f"/api/trade/{trade_id}", headers=auth_headers, json={"status": "open"})
    second_close = _close(client, auth_headers, trade_id, 500.0)

    assert reopen.status_code == 400
    assert second_close.status_code == 400
    history = client.get("/api/trade/history/list", headers=auth_headers).json()
    assert len(history) == 1


def test_trade_cannot_be_closed_through_update(client, auth_headers):
    trade_id = _trade(client, auth_headers, "BUY", 1).json()["id"]

    response = client.put(f"/api/trade/{trade_id}", headers=auth_headers, json={"status": "closed"})

    assert response.status_code == 400


def test_trade_endpoints_require_authentication(client):
    response = _trade(client, {}, "BUY", 1)

    assert response.status_code == 401
