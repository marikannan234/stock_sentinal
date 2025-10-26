import streamlit as st
import plotly.express as px
from data_fetcher import fetch_stock_data, fetch_news_data
from sentiment_model import analyze_sentiment

st.set_page_config(page_title="StockSentinel", layout="wide")
st.title("📈 StockSentinel: AI-Powered Market Sentiment Analyzer")

# --- Initialize Session State Safely ---
if "stock_data" not in st.session_state:
    st.session_state.stock_data = None
if "news_data" not in st.session_state:
    st.session_state.news_data = None
if "analyzed_data" not in st.session_state:
    st.session_state.analyzed_data = None
if "sentiment_summary" not in st.session_state:
    st.session_state.sentiment_summary = {}

# --- Input Fields ---
st.sidebar.header("Configuration")
user_api_key = 151eb78228084f2fb633e9aacb91ba96
tickers = st.multiselect(
    "Select Companies to Analyze:",
    ["AAPL", "TSLA", "MSFT", "AMZN", "GOOGL", "NVDA", "META", "NFLX"],
    default=["AAPL", "TSLA"]
)


# --- Data Fetching Section ---
if ticker and user_api_key:
    with st.spinner("Fetching latest news and stock data..."):
        try:
            stock_data = fetch_stock_data(ticker)
            news_data = fetch_news_data(ticker, user_api_key)

            if stock_data is not None and not stock_data.empty:
                st.session_state.stock_data = stock_data

            if news_data is not None and not news_data.empty:
                analyzed_df, summary = analyze_sentiment(news_data)
                st.session_state.analyzed_data = analyzed_df
                st.session_state.sentiment_summary = summary
            else:
                st.warning("No news data found — please verify the ticker symbol or API key.")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

# --- Stock Chart Section ---
st.header("📊 Stock Trend Visualization")
if st.session_state.stock_data is not None and not st.session_state.stock_data.empty:
    data = st.session_state.stock_data
    if "Date" in data.columns and "Close" in data.columns:
        try:
            fig = px.line(
                data, x="Date", y="Close",
                title=f"{ticker.upper()} Stock Closing Prices (Last 30 Days)"
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Unable to render stock chart: {e}")
    else:
        st.warning("Fetched stock data does not contain 'Date' or 'Close' columns.")
else:
    st.info("Enter a valid stock ticker and API key to start analysis.")

# --- Sentiment Visualization Section ---
if st.session_state.sentiment_summary:
    st.header("🧠 Market Sentiment Overview")
    summary = st.session_state.sentiment_summary
    try:
        sentiment_fig = px.pie(
            names=list(summary.keys()),
            values=list(summary.values()),
            title="News Sentiment Distribution"
        )
        st.plotly_chart(sentiment_fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not render sentiment chart: {e}")
else:
    st.info("No sentiment data to display yet. Fetch news first.")

# --- Analyzed News Table Section ---
if st.session_state.analyzed_data is not None and not st.session_state.analyzed_data.empty:
    st.header("📰 Latest News Sentiment Analysis")
    st.dataframe(
        st.session_state.analyzed_data[["title", "source", "publishedAt", "sentiment"]],
        use_container_width=True
    )
