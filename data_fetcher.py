import yfinance as yf
from newsapi import NewsApiClient
import pandas as pd
import streamlit as st


@st.cache_data(ttl=1800)
def fetch_stock_data(tickers):
    """
    Fetch stock price data for single or multiple companies and flatten columns
    to make sure 'Date' and 'Close' are always accessible.
    """
    # Allow single or list input
    if isinstance(tickers, str):
        tickers = [tickers]

    # Download with multi-level support
    data = yf.download(tickers, period="30d", interval="1d", group_by='ticker', auto_adjust=True)
    data.reset_index(inplace=True)

    # --- Fix for MultiIndex (latest yfinance update) ---
    if isinstance(data.columns, pd.MultiIndex):
        # If single ticker, extract its sub-data directly
        if len(tickers) == 1:
            data = data.xs(key=tickers[0], axis=1, level=1)
            data.reset_index(inplace=True)
        else:
            # Flatten multi-level columns (e.g. ('Close','TSLA') → 'Close_TSLA')
            data.columns = [f"{a}_{b}" if b else a for a, b in data.columns]

    # Clean indexing just in case
    data = data.loc[:, ~data.columns.duplicated()]
    data = data.rename(columns=lambda x: x.strip() if isinstance(x, str) else x)

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
