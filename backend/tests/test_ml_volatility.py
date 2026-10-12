import numpy as np
import pandas as pd
import pytest

from app.services.ml_volatility import (
    FEATURE_COLUMNS,
    InsufficientHistoryError,
    build_training_frame,
    forecast_realized_volatility,
)


def _history(rows: int = 500) -> pd.DataFrame:
    rng = np.random.default_rng(23)
    returns = rng.normal(0.0003, 0.015, rows)
    close = 100 * np.exp(np.cumsum(returns))
    return pd.DataFrame({
        "Close": close,
        "Volume": rng.integers(100_000, 2_000_000, rows),
    }, index=pd.date_range("2023-01-01", periods=rows, freq="B"))


def test_training_frame_has_expected_features_and_finite_targets():
    frame = build_training_frame(_history())
    assert set(FEATURE_COLUMNS).issubset(frame.columns)
    assert frame["target_volatility"].notna().all()
    assert np.isfinite(frame[list(FEATURE_COLUMNS)].to_numpy()).all()


def test_forecast_uses_chronological_holdout_and_returns_baseline_metrics():
    result = forecast_realized_volatility(_history(), "aapl")
    assert result.symbol == "AAPL"
    assert result.horizon_days == 5
    assert result.holdout_observations >= 30
    assert result.predicted_volatility_percent >= 0
    assert result.model_mae_percent >= 0
    assert result.baseline_mae_percent >= 0
    assert isinstance(result.model_beats_baseline, bool)


def test_forecast_rejects_short_history_instead_of_inventing_prediction():
    with pytest.raises(InsufficientHistoryError):
        forecast_realized_volatility(_history(90), "AAPL")
