import yfinance as yf
from newsapi import NewsApiClient
import pandas as pd
import streamlit as st

@st.cache_data(ttl=1800)
def fetch_stock_data(tickers):
    # Allow single ticker or list
    if isinstance(tickers, str):
        tickers = [tickers]

    # Download data with group_by='ticker' for multi-company support
    data = yf.download(tickers, period="1mo", interval="1d", group_by="ticker", auto_adjust=True)

    # Reset index so Date becomes a column
    data.reset_index(inplace=True)

    # Flatten MultiIndex columns (e.g., ('Close','AAPL') → 'Close_AAPL')
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [
            f"{col[0]}_{col[1]}" if col[1] else col[0] for col in data.columns
        ]

    # Rename standalone Date column safely
    if "Date_" in data.columns:
        data.rename(columns={"Date_": "Date"}, inplace=True)

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
