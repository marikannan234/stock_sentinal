from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from app.ai.config import ai_settings


@dataclass
class SentimentResult:
    headline: str
    label: str
    score: float


class SentimentService:
    """
    High-level service for sentiment analysis of news headlines using FinBERT.

    Usage:
        service = SentimentService()
        results = service.analyze_headlines(["Stock X rallies on strong earnings"])
    """

    def __init__(self, model_name: str | None = None, device: str | None = None) -> None:
        self.model_name = model_name or ai_settings.FINBERT_MODEL_NAME
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        self._model.to(self.device)
        self._model.eval()

        # FinBERT labels: usually ["negative", "neutral", "positive"]
        self._id2label = self._model.config.id2label

    def analyze_headlines(self, headlines: Iterable[str]) -> List[SentimentResult]:
        """
        Analyze a batch of news headlines and return per-headline sentiment.

        Returns a list of SentimentResult with:
        - label: "positive" | "neutral" | "negative"
        - score: model confidence for the predicted label (0..1)
        """
        texts = [h for h in headlines if h and h.strip()]
        if not texts:
            return []

        encoded = self._tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=64,
            return_tensors="pt",
        )
        encoded = {k: v.to(self.device) for k, v in encoded.items()}

        with torch.no_grad():
            outputs = self._model(**encoded)
            probs = torch.softmax(outputs.logits, dim=-1)

        scores, indices = torch.max(probs, dim=-1)

        results: List[SentimentResult] = []
        for headline, idx, score in zip(texts, indices.tolist(), scores.tolist()):
            label = self._id2label.get(idx, str(idx))
            results.append(
                SentimentResult(
                    headline=headline,
                    label=label,
                    score=float(score),
                )
            )

        return results

