"""Walk-forward evaluated ML baseline for short-horizon realized volatility.

This module forecasts volatility, not price direction. Features at row t use only
information available through t; the target is realized volatility over the next
five observations. The final chronological holdout is never used for fitting.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

FEATURE_COLUMNS = (
    "return_1d",
    "return_5d",
    "return_20d",
    "volatility_5d",
    "volatility_20d",
    "volatility_60d",
    "volume_change_1d",
    "distance_sma20",
    "distance_sma50",
)
HORIZON_DAYS = 5
MODEL_VERSION = "rf-realized-volatility-v1"


class InsufficientHistoryError(ValueError):
    """Raised when history is too short or too incomplete for honest evaluation."""


@dataclass(frozen=True)
class VolatilityForecast:
    symbol: str
    horizon_days: int
    predicted_volatility_percent: float
    baseline_volatility_percent: float
    model_mae_percent: float
    baseline_mae_percent: float
    holdout_observations: int
    model_beats_baseline: bool
    model_version: str
    methodology: str = "Random Forest regression; chronological holdout; next-five-observation realized volatility"
    caveat: str = "Research estimate only. Historical model performance does not guarantee future accuracy."


def build_training_frame(history: pd.DataFrame) -> pd.DataFrame:
    """Build leakage-aware features and a forward 5-observation volatility target."""
    if not {"Close", "Volume"}.issubset(history.columns):
        raise InsufficientHistoryError("Historical data must include Close and Volume columns.")

    frame = history[["Close", "Volume"]].copy()
    frame["Close"] = pd.to_numeric(frame["Close"], errors="coerce")
    frame["Volume"] = pd.to_numeric(frame["Volume"], errors="coerce")
    frame = frame.replace([np.inf, -np.inf], np.nan)
    frame = frame.loc[frame["Close"] > 0].copy()
    returns = np.log(frame["Close"] / frame["Close"].shift(1))
    frame["return_1d"] = returns
    frame["return_5d"] = frame["Close"].pct_change(5)
    frame["return_20d"] = frame["Close"].pct_change(20)
    frame["volatility_5d"] = returns.rolling(5).std() * np.sqrt(252)
    frame["volatility_20d"] = returns.rolling(20).std() * np.sqrt(252)
    frame["volatility_60d"] = returns.rolling(60).std() * np.sqrt(252)
    frame["volume_change_1d"] = frame["Volume"].pct_change().replace([np.inf, -np.inf], np.nan).clip(-5, 5)
    frame["distance_sma20"] = frame["Close"] / frame["Close"].rolling(20).mean() - 1
    frame["distance_sma50"] = frame["Close"] / frame["Close"].rolling(50).mean() - 1

    # Shift forward returns back to the feature timestamp: no future return enters features.
    future_returns = pd.concat(
        [returns.shift(-offset) for offset in range(1, HORIZON_DAYS + 1)],
        axis=1,
    )
    frame["target_volatility"] = future_returns.std(axis=1, ddof=1).where(future_returns.notna().all(axis=1)) * np.sqrt(252)
    frame = frame.replace([np.inf, -np.inf], np.nan)
    return frame.dropna(subset=[*FEATURE_COLUMNS, "target_volatility"])


def forecast_realized_volatility(history: pd.DataFrame, symbol: str) -> VolatilityForecast:
    """Fit a Random Forest on earlier rows and evaluate on a later untouched holdout."""
    frame = build_training_frame(history)
    if len(frame) < 180:
        raise InsufficientHistoryError(
            f"At least 180 usable daily observations are required; found {len(frame)}."
        )

    split = int(len(frame) * 0.8)
    train, test = frame.iloc[:split], frame.iloc[split:]
    if len(train) < 120 or len(test) < 30:
        raise InsufficientHistoryError("Not enough chronological training/holdout rows.")

    X_train, y_train = train[list(FEATURE_COLUMNS)], train["target_volatility"]
    X_test, y_test = test[list(FEATURE_COLUMNS)], test["target_volatility"]
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=6,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=1,
    )
    model.fit(X_train, y_train)
    model_predictions = np.maximum(model.predict(X_test), 0)
    baseline = float(y_train.median())
    baseline_predictions = np.full(len(y_test), baseline, dtype=float)
    model_mae = float(mean_absolute_error(y_test, model_predictions))
    baseline_mae = float(mean_absolute_error(y_test, baseline_predictions))
    latest_prediction = float(max(0.0, model.predict(frame.iloc[[-1]][list(FEATURE_COLUMNS)])[0]))

    return VolatilityForecast(
        symbol=symbol.upper(),
        horizon_days=HORIZON_DAYS,
        predicted_volatility_percent=round(latest_prediction * 100, 2),
        baseline_volatility_percent=round(baseline * 100, 2),
        model_mae_percent=round(model_mae * 100, 3),
        baseline_mae_percent=round(baseline_mae * 100, 3),
        holdout_observations=len(test),
        model_beats_baseline=model_mae < baseline_mae,
        model_version=MODEL_VERSION,
    )


def forecast_to_dict(forecast: VolatilityForecast) -> dict[str, Any]:
    """Convert dataclass output to a JSON-safe dictionary."""
    return {
        "symbol": forecast.symbol,
        "horizon_days": forecast.horizon_days,
        "predicted_volatility_percent": forecast.predicted_volatility_percent,
        "baseline_volatility_percent": forecast.baseline_volatility_percent,
        "model_mae_percent": forecast.model_mae_percent,
        "baseline_mae_percent": forecast.baseline_mae_percent,
        "holdout_observations": forecast.holdout_observations,
        "model_beats_baseline": forecast.model_beats_baseline,
        "model_version": forecast.model_version,
        "methodology": forecast.methodology,
        "caveat": forecast.caveat,
    }
