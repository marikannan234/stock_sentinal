import streamlit as st
import plotly.express as px
from data_fetcher import fetch_stock_data, fetch_news_data
from sentiment_model import analyze_sentiment
import os

st.set_page_config(page_title="StockSentinel", layout="wide")
st.title("📈 StockSentinel: AI-Powered Market Sentiment Analyzer")

# --- Secure API Key Setup ---
# OPTION 1: If deploying on Streamlit Cloud — use secrets management.
# Add this key under "Secrets" in app settings as: NEWS_API_KEY = "your_key_here"
# api_key = st.secrets["NEWS_API_KEY"]

# OPTION 2: For local development — hardcode (not recommended for public repos).
api_key = "151eb78228084f2fb633e9aacb91ba96"  # replace with your actual key

# --- Initialize Variables ---
stock_data = None
news_data = None
sentiment_summary = {}
analyzed_data = None

# --- Input field for stock ticker ---
tickers = st.multiselect(
    "Select Companies to Analyze:",
    ["AAPL", "TSLA", "MSFT", "AMZN", "GOOGL", "NVDA", "META", "NFLX"],
    default=["AAPL", "TSLA"]
)


# --- Main Logic ---
for ticker in tickers:
    st.subheader(f"Results for {ticker}")
    try:
        stock_data = fetch_stock_data(ticker)
        news_data = fetch_news_data(ticker, api_key)

        if stock_data is not None and not stock_data.empty and news_data is not None and not news_data.empty:
            analyzed_data, sentiment_summary = analyze_sentiment(news_data)

            # Chart Section
            if "Date" in stock_data.columns and "Close" in stock_data.columns:
                chart = px.line(
                    stock_data, x="Date", y="Close",
                    title=f"{ticker} - Stock Performance"
                )
                st.plotly_chart(chart, use_container_width=True)

            # Sentiment Pie Chart
            if sentiment_summary:
                sentiment_fig = px.pie(
                    names=list(sentiment_summary.keys()),
                    values=list(sentiment_summary.values()),
                    title=f"{ticker} - News Sentiment"
                )
                st.plotly_chart(sentiment_fig, use_container_width=True)

            # Display News Data
            st.dataframe(analyzed_data[["title", "source", "publishedAt", "sentiment"]])
        else:
            st.warning(f"No data found for {ticker}.")

    except Exception as e:
        st.error(f"Error for {ticker}: {e}")

# --- Stock Chart Visualization ---
if stock_data is not None and not stock_data.empty:
    st.subheader("Stock Price Over Time")
    if "Date" in stock_data.columns and "Close" in stock_data.columns:
        try:
            price_chart = px.line(
                stock_data, x="Date", y="Close",
                title=f"{ticker.upper()} Closing Prices (Last 30 Days)"
            )
            st.plotly_chart(price_chart, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not render stock chart: {e}")
    else:
        st.warning("Stock data missing 'Date' or 'Close' columns.")

# --- Sentiment Distribution Visualization ---
if sentiment_summary:
    st.subheader("Sentiment Distribution")
    try:
        fig = px.pie(
            names=list(sentiment_summary.keys()),
            values=list(sentiment_summary.values()),
            title="Market News Sentiment Share"
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Error rendering sentiment chart: {e}")

# --- News Data Table ---
if analyzed_data is not None and not analyzed_data.empty:
    st.subheader("Latest Analyzed News")
    st.dataframe(
        analyzed_data[["title", "source", "publishedAt", "sentiment"]],
        use_container_width=True
    )
