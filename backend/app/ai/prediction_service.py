from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, List, Literal, Optional

import numpy as np
import pandas as pd
from prophet import Prophet

from app.ai.config import ai_settings


PredictionBackend = Literal["prophet", "lstm"]


@dataclass
class PricePoint:
    date: datetime
    price: float


@dataclass
class PredictionPoint:
    date: datetime
    predicted_price: float


class PredictionService:
    """
    High-level stock prediction service.

    For simplicity and robustness, the default backend is Prophet, which
    handles daily time series with minimal configuration. An LSTM backend
    can be added later behind the same interface.
    """

    def __init__(
        self,
        backend: PredictionBackend | None = None,
        horizon_days: Optional[int] = None,
    ) -> None:
        self.backend: PredictionBackend = backend or ai_settings.PREDICTION_BACKEND
        self.horizon_days: int = (
            horizon_days or ai_settings.PREDICTION_DEFAULT_HORIZON_DAYS
        )

        if self.backend not in {"prophet", "lstm"}:
            raise ValueError(f"Unsupported prediction backend: {self.backend}")

    # Public API ---------------------------------------------------------------

    def predict_next_days(
        self,
        history: Iterable[PricePoint],
        horizon_days: Optional[int] = None,
    ) -> List[PredictionPoint]:
        """
        Predict the next N days of prices given historical daily closing prices.

        `history` should be in chronological order, but will be sorted just in case.
        """
        horizon = horizon_days or self.horizon_days

        if self.backend == "prophet":
            return self._predict_with_prophet(history, horizon)
        else:
            # Placeholder for an LSTM-based implementation (not wired here to
            # keep dependencies and complexity reasonable).
            return self._predict_with_naive(history, horizon)

    # Internal implementations -------------------------------------------------

    def _predict_with_prophet(
        self,
        history: Iterable[PricePoint],
        horizon_days: int,
    ) -> List[PredictionPoint]:
        points = sorted(history, key=lambda p: p.date)
        if len(points) < 5:
            # Not enough data for Prophet; fall back to naive forecast.
            return self._predict_with_naive(points, horizon_days)

        df = pd.DataFrame(
            {
                "ds": [p.date for p in points],
                "y": [p.price for p in points],
            }
        )

        model = Prophet()
        model.fit(df)

        future = model.make_future_dataframe(periods=horizon_days, freq="D", include_history=False)
        forecast = model.predict(future)

        results: List[PredictionPoint] = []
        for _, row in forecast.iterrows():
            results.append(
                PredictionPoint(
                    date=row["ds"].to_pydatetime(),
                    predicted_price=float(row["yhat"]),
                )
            )
        return results

    def _predict_with_naive(
        self,
        history: Iterable[PricePoint],
        horizon_days: int,
    ) -> List[PredictionPoint]:
        """
        Simple fallback: extend the last observed price or linear trend.

        This keeps the service usable even when there is not enough data
        for more sophisticated models.
        """
        points = sorted(history, key=lambda p: p.date)
        if not points:
            return []

        if len(points) == 1:
            last_price = points[-1].price
            start_date = points[-1].date
            return [
                PredictionPoint(
                    date=start_date + timedelta(days=i),
                    predicted_price=float(last_price),
                )
                for i in range(1, horizon_days + 1)
            ]

        # Simple linear trend on last N points
        dates = np.array(
            [(p.date - points[0].date).days for p in points], dtype=float
        )
        prices = np.array([p.price for p in points], dtype=float)

        # Fit y = a * t + b
        a, b = np.polyfit(dates, prices, 1)

        last_day = dates[-1]
        last_date = points[-1].date

        results: List[PredictionPoint] = []
        for i in range(1, horizon_days + 1):
            t = last_day + i
            price = a * t + b
            results.append(
                PredictionPoint(
                    date=last_date + timedelta(days=i),
                    predicted_price=float(price),
                )
            )

        return results

