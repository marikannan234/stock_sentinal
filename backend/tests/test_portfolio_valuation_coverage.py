from app.api.routes import portfolio as portfolio_routes


def _holding(ticker, invested, current_value, day_change=None):
    return portfolio_routes.HoldingItem(
        ticker=ticker,
        quantity=1,
        average_price=invested,
        invested_amount=invested,
        current_price=current_value,
        current_value=current_value,
        pl_amount=(current_value - invested) if current_value is not None else None,
        pl_percent=((current_value - invested) / invested * 100)
        if current_value is not None and invested
        else None,
        day_change=day_change,
        day_change_percent=None,
        name=ticker,
        asset_class="Technology",
    )


def test_portfolio_summary_excludes_unpriced_positions_from_pl(
    client, auth_headers, monkeypatch
):
    monkeypatch.setattr(
        portfolio_routes,
        "_enriched_holdings",
        lambda db, user_id: [
            _holding("AAPL", 100, 120, 2),
            _holding("MSFT", 200, None, None),
        ],
    )

    response = client.get("/api/portfolio/summary", headers=auth_headers)

    assert response.status_code == 200, response.text
    summary = response.json()
    assert summary["total_invested"] == 300
    assert summary["current_value"] == 120
    assert summary["total_pl"] == 20
    assert summary["percent_pl"] == 20
    assert summary["day_pl"] == 2
    assert summary["priced_invested"] == 100
    assert summary["priced_holdings"] == 1
    assert summary["total_holdings"] == 2
    assert summary["valuation_coverage_percent"] == 50


def test_portfolio_summary_with_no_holdings_has_full_coverage(
    client, auth_headers, monkeypatch
):
    monkeypatch.setattr(portfolio_routes, "_enriched_holdings", lambda db, user_id: [])

    response = client.get("/api/portfolio/summary", headers=auth_headers)

    assert response.status_code == 200, response.text
    summary = response.json()
    assert summary["total_invested"] == 0
    assert summary["current_value"] == 0
    assert summary["total_pl"] == 0
    assert summary["priced_holdings"] == 0
    assert summary["total_holdings"] == 0
    assert summary["valuation_coverage_percent"] == 100
