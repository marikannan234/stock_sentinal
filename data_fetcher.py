import yfinance as yf
from newsapi import NewsApiClient
import pandas as pd

def fetch_stock_data(ticker):
    data = yf.download(ticker, period="30d", interval="1d")
    data.reset_index(inplace=True)
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
