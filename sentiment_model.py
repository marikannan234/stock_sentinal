import torch
from transformers import pipeline
import streamlit as st

@st.cache_resource
def load_sentiment_pipeline():
    """
    Load and cache the FinBERT pipeline strictly on the CPU.
    Prevents 'meta tensor' and memory offloading issues in Streamlit Cloud.
    """
    # Force all tensors to CPU; disable meta device initialization
    torch.set_default_device("cpu")

    # Explicitly ensure CPU-only model loading
    model_pipeline = pipeline(
        "sentiment-analysis",
        model="ProsusAI/finbert",
        revision="main",
        device=-1   # -1 = use CPU
    )
    return model_pipeline


def analyze_sentiment(news_df):
    """
    Perform sentiment analysis on a column of news titles.
    Returns the augmented DataFrame and sentiment summary.
    """
    sentiment_pipeline = load_sentiment_pipeline()
    sentiments = []

    for text in news_df["title"]:
        if isinstance(text, str):
            try:
                result = sentiment_pipeline(text[:512])[0]
                label = result["label"]
            except Exception:
                label = "NEUTRAL"
        else:
            label = "NEUTRAL"
        sentiments.append(label)

    news_df["sentiment"] = sentiments
    summary = news_df["sentiment"].value_counts().to_dict()
    return news_df, summary
