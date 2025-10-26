import streamlit as st
import plotly.express as px
import pandas as pd
import yfinance as yf
from newsapi import NewsApiClient
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
import torch

# ------------------------------------------------------------
# PAGE SETUP
# ------------------------------------------------------------
st.set_page_config(page_title="StockSentinel", layout="wide")
st.title("📈 StockSentinel: AI-Powered Market Sentiment Analyzer")

# ------------------------------------------------------------
# YOUR NEWSAPI KEY
# ------------------------------------------------------------
API_KEY = "151eb78228084f2fb633e9aacb91ba96"  # Replace with your own key

# ------------------------------------------------------------
# CACHED FUNCTIONS
# ------------------------------------------------------------

@st.cache_resource
def load_finbert():
    """Load FinBERT pipeline safely on CPU (fixes meta tensor errors)."""
    torch.set_default_device("cpu")
    model_name = "ProsusAI/finbert"
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        torch_dtype=torch.float32,
        device_map=None,        # ensures CPU load only
        low_cpu_mem_usage=False
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    nlp = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer, device=-1)  # CPU only
    return nlp


@st.cache_data(ttl=3600)
def fetch_stock_data(tickers):
    """Download and flatten yfinance data."""
    if isinstance(tickers, str):
        tickers = [tickers]
    data = yf.download(tickers, period="30d", interval="1d", group_by='ticker', auto_adjust=True)
    data.reset_index(inplace=True)
    # Flatten MultiIndex columns (e.g. ('Close','TSLA') → 'Close_TSLA')
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [f"{a}_{b}" if b else a for a, b in data.columns]
    return data


@st.cache_data(ttl=3600)
def fetch_news(query, api_key):
    """Fetch news related to a stock/company."""
    newsapi = NewsApiClient(api_key=api_key)
    articles = newsapi.get_everything(q=query, language='en', sort_by='publishedAt', page_size=20)
    df = pd.DataFrame([{
        "title": article["title"],
        "description": article["description"],
        "publishedAt": article["publishedAt"],
        "source": article["source"]["name"]
    } for article in articles["articles"]])
    return df


def analyze_sentiment(df):
    """Run FinBERT sentiment analysis on titles."""
    classifier = load_finbert()
    sentiments = []
    for text in df["title"]:
        if isinstance(text, str):
            try:
                result = classifier(text[:512])[0]
                sentiments.append(result["label"])
            except Exception:
                sentiments.append("NEUTRAL")
        else:
            sentiments.append("NEUTRAL")
    df["sentiment"] = sentiments
    summary = df["sentiment"].value_counts().to_dict()
    return df, summary

# ------------------------------------------------------------
# MAIN INPUTS
# ------------------------------------------------------------
tickers = st.multiselect(
    "Select Companies to Analyze:",
    ["AAPL", "TSLA", "MSFT", "AMZN", "GOOGL", "NVDA", "META", "NFLX"],
    default=["AAPL", "TSLA"]
)

# ------------------------------------------------------------
# ANALYSIS PIPELINE
# ------------------------------------------------------------
if tickers:
    for ticker in tickers:
        st.header(f"Results for {ticker}")
        try:
            stock_data = fetch_stock_data(ticker)
            news_df = fetch_news(ticker, API_KEY)

            if stock_data is None or stock_data.empty:
                st.warning(f"No market data found for {ticker}.")
                continue

            if news_df is None or news_df.empty:
                st.warning(f"No news articles found for {ticker}.")
                continue

            analyzed_data, sentiment_summary = analyze_sentiment(news_df)

            # --- PRICE CHART ---
            if "Date" in stock_data.columns:
                close_col = f"Close_{ticker}" if f"Close_{ticker}" in stock_data.columns else "Close"
                if "Date" in stock_data.columns and close_col in stock_data.columns:
                    fig = px.line(stock_data, x="Date", y=close_col, title=f"{ticker} – Closing Prices (Last 30 Days)")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning(f"‘Close’ column not found for {ticker}.")

            else:
                st.warning("Stock data missing 'Date' column.")

            # --- SENTIMENT PIE CHART ---
            if sentiment_summary:
                fig_sent = px.pie(
                    names=list(sentiment_summary.keys()),
                    values=list(sentiment_summary.values()),
                    title=f"{ticker} - News Sentiment Share"
                )
                st.plotly_chart(fig_sent, use_container_width=True)
            else:
                st.info("No sentiment data available.")

            # --- SHOW NEWS DATA ---
            st.subheader(f"Recent News for {ticker}")
            st.dataframe(analyzed_data[["title", "source", "publishedAt", "sentiment"]])

        except Exception as e:
            st.error(f"Error for {ticker}: {e}")

else:
    st.info("Please select at least one company to start analysis.")
