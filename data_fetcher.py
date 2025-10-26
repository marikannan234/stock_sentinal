import yfinance as yf
from newsapi import NewsApiClient
import pandas as pd
import streamlit as st


@st.cache_data(ttl=1800)
def fetch_stock_data(tickers):
    """
    Fetch stock price data for one or multiple tickers from Yahoo Finance.
    Handles yfinance's new MultiIndex column format introduced in 0.2.51+.
    Always returns a DataFrame with a 'Date' column and flattened names.
    """
    import yfinance as yf
    import pandas as pd

    # Accept both string and list input
    if isinstance(tickers, str):
        tickers = [tickers]

    # ---- NEW FIX ----
    # Add multi_level_index=False (available in yfinance >=0.2.51)
    # This ensures single-level column names like 'Open', 'High', 'Close', etc.
    data = yf.download(
        tickers,
        period="30d",
        interval="1d",
        group_by="ticker",
        auto_adjust=True,
        multi_level_index=False  # <--- critical fix for 2025 versions
    )

    # Ensure Date is a visible column
    data.reset_index(inplace=True)

    # ---- Fallback: flatten MultiIndex (just in case older yfinance) ----
    if isinstance(data.columns, pd.MultiIndex):
        # If single ticker, drop the extra index level
        if len(tickers) == 1:
            data.columns = data.columns.get_level_values(0)
        else:
            data.columns = [f"{a}_{b}" if b else a for a, b in data.columns]

    return data



def fetch_news_data(query, api_key):
    newsapi = NewsApiClient(api_key=api_key)
    articles = newsapi.get_everything(q=query, language='en', sort_by='publishedAt', page_size=20)
    
    news_df = pd.DataFrame([{
        "title": a["title"],
        "description": a["description"],
        "publishedAt": a["publishedAt"],
        "source": a["source"]["name"]
    } for a in articles["articles"]])
    
    return news_df
