import re
from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.alert import ALERT_PARAMETERS_CHECK, Alert, AlertCondition, AlertType


def _create(client, headers, **payload):
    payload.setdefault("stock_symbol", "AAPL")
    return client.post("/api/alerts", headers=headers, json=payload)


VALID_ALERTS = [
    {"alert_type": "price", "condition": ">", "target_value": 150},
    {"alert_type": "custom", "condition": "<=", "target_value": 90},
    {"alert_type": "percentage_change", "target_value": 5},
    {"alert_type": "volume_spike", "target_value": 2},
    {"alert_type": "crash", "target_value": 10},
    {"alert_type": "sma_above", "sma_period": 50},
    {"alert_type": "sma_below", "sma_period": 200},
    {"alert_type": "sma_crossover", "sma_period": 20},
    {"alert_type": "ema_above", "ema_period": 12},
    {"alert_type": "ema_below", "ema_period": 26},
    {"alert_type": "ema_crossover", "ema_period": 50},
    {"alert_type": "rsi_overbought", "rsi_period": 14},
    {"alert_type": "rsi_oversold", "rsi_period": 14},
    {"alert_type": "rsi_crossover", "rsi_period": 7},
    {"alert_type": "strong_buy_signal", "sma_period": 50, "ema_period": 20, "rsi_period": 14},
    {"alert_type": "strong_sell_signal", "sma_period": 50, "ema_period": 20, "rsi_period": 14},
]


def test_every_alert_type_has_a_creation_case():
    assert {case["alert_type"] for case in VALID_ALERTS} == {t.value for t in AlertType}


@pytest.mark.parametrize("payload", VALID_ALERTS, ids=lambda p: p["alert_type"])
def test_create_each_alert_type(client, auth_headers, db_session, payload):
    response = _create(client, auth_headers, **payload)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["alert_type"] == payload["alert_type"]
    assert body["is_active"] is True
    assert body["is_triggered"] is False
    for field in ("condition", "target_value", "sma_period", "ema_period", "rsi_period"):
        assert body[field] == payload.get(field), field

    stored = db_session.get(Alert, body["id"])
    assert stored.sma_period == payload.get("sma_period")
    assert stored.ema_period == payload.get("ema_period")
    assert stored.rsi_period == payload.get("rsi_period")


def test_indicator_alert_does_not_require_or_keep_price_fields(client, auth_headers):
    response = _create(
        client, auth_headers,
        alert_type="sma_crossover", sma_period=50, condition=">", target_value=123, ema_period=9,
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert (body["condition"], body["target_value"], body["ema_period"]) == (None, None, None)


def test_threshold_alert_does_not_require_condition(client, auth_headers):
    response = _create(client, auth_headers, alert_type="percentage_change", target_value=5, condition=">")

    assert response.status_code == 201, response.text
    assert response.json()["condition"] is None


def test_alert_type_is_case_insensitive(client, auth_headers):
    response = _create(client, auth_headers, alert_type="SMA_Above", sma_period=50)

    assert response.status_code == 201, response.text
    assert response.json()["alert_type"] == "sma_above"


@pytest.mark.parametrize(
    "payload, message",
    [
        ({"alert_type": "price", "target_value": 150}, "condition"),
        ({"alert_type": "price", "condition": ">"}, "target_value"),
        ({"alert_type": "custom", "target_value": 150}, "condition"),
        ({"alert_type": "percentage_change"}, "target_value"),
        ({"alert_type": "volume_spike"}, "target_value"),
        ({"alert_type": "crash"}, "target_value"),
        ({"alert_type": "sma_above"}, "sma_period"),
        ({"alert_type": "ema_crossover"}, "ema_period"),
        ({"alert_type": "rsi_oversold"}, "rsi_period"),
        ({"alert_type": "strong_buy_signal", "sma_period": 50, "ema_period": 20}, "rsi_period"),
    ],
)
def test_missing_required_fields_are_rejected(client, auth_headers, payload, message):
    response = _create(client, auth_headers, **payload)

    assert response.status_code == 422
    assert message in response.text


@pytest.mark.parametrize(
    "payload",
    [
        {"alert_type": "sma_amazing", "sma_period": 5},
        {"alert_type": "price", "condition": "~", "target_value": 5},
        {"alert_type": "price", "condition": "percentage_change", "target_value": 5},
        {"alert_type": "price", "condition": ">", "target_value": -1},
        {"alert_type": "price", "condition": ">", "target_value": 0},
        {"alert_type": "price", "condition": ">", "target_value": "abc"},
        {"alert_type": "crash", "target_value": 100},
        {"alert_type": "percentage_change", "target_value": 5000},
        {"alert_type": "volume_spike", "target_value": 0.5},
        {"alert_type": "sma_above", "sma_period": 1},
        {"alert_type": "sma_above", "sma_period": 501},
        {"alert_type": "rsi_overbought", "rsi_period": 101},
        {"alert_type": "price", "condition": ">", "target_value": 5, "stock_symbol": ""},
    ],
)
def test_invalid_values_are_rejected(client, auth_headers, payload):
    assert _create(client, auth_headers, **payload).status_code == 422


def test_duplicate_alert_is_rejected_but_other_period_is_not(client, auth_headers):
    assert _create(client, auth_headers, alert_type="sma_above", sma_period=50).status_code == 201

    assert _create(client, auth_headers, alert_type="sma_above", sma_period=50).status_code == 409
    assert _create(client, auth_headers, alert_type="sma_above", sma_period=200).status_code == 201


def test_alerts_require_authentication(client):
    assert client.get("/api/alerts").status_code == 401
    assert _create(client, {}, alert_type="price", condition=">", target_value=1).status_code == 401


def test_list_and_delete(client, auth_headers):
    alert_id = _create(client, auth_headers, alert_type="rsi_oversold", rsi_period=14).json()["id"]

    listed = client.get("/api/alerts", headers=auth_headers).json()
    assert [a["id"] for a in listed] == [alert_id]

    assert client.delete(f"/api/alerts/{alert_id}", headers=auth_headers).status_code == 204
    assert client.get("/api/alerts", headers=auth_headers).json() == []


def test_reenabling_a_fired_alert_rearms_it(client, auth_headers, db_session):
    alert_id = _create(client, auth_headers, alert_type="percentage_change", target_value=5).json()["id"]
    alert = db_session.get(Alert, alert_id)
    alert.is_active, alert.is_triggered, alert.last_price = False, True, 123.0
    db_session.commit()

    response = client.patch(f"/api/alerts/{alert_id}", headers=auth_headers, json={"is_active": True})

    assert response.status_code == 200, response.text
    body = response.json()
    assert (body["is_active"], body["is_triggered"], body["last_price"]) == (True, False, None)


def test_pausing_keeps_trigger_state(client, auth_headers, db_session):
    alert_id = _create(client, auth_headers, alert_type="sma_crossover", sma_period=20).json()["id"]
    alert = db_session.get(Alert, alert_id)
    alert.last_price = 99.0
    db_session.commit()

    body = client.patch(f"/api/alerts/{alert_id}", headers=auth_headers, json={"is_active": False}).json()

    assert (body["is_active"], body["last_price"]) == (False, 99.0)


def test_database_rejects_alert_without_required_parameters(db_session, registered_user):
    db_session.add(Alert(
        user_id=registered_user["id"], stock_symbol="AAPL", alert_type=AlertType.PRICE,
        condition=AlertCondition.GREATER_THAN, target_value=None,
    ))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    db_session.add(Alert(user_id=registered_user["id"], stock_symbol="AAPL", alert_type=AlertType.SMA_ABOVE))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_migration_check_matches_model_rules():
    migration = (Path(__file__).parents[1] / "alembic" / "versions" / "0007_alert_type_parameters.py").read_text()
    frozen = "".join(re.findall(r'"([^"]*)"', migration.split("ALERT_PARAMETERS_CHECK = (")[1].split(")\n\n")[0]))

    assert frozen == ALERT_PARAMETERS_CHECK
