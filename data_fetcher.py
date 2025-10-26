from newsapi import NewsApiClient
import pandas as pd

# Initialize NewsAPI client
API_KEY = '151eb78228084f2fb633e9aacb91ba96'
newsapi = NewsApiClient(api_key=API_KEY)

def fetch_latest_news(query, language='en', max_articles=20):
    """
    Fetches the latest news articles using NewsAPI.
    Params:
        query: search term (like 'AAPL', 'Tesla','INTC','IBM','META','NVDA','AMZN','GOOGL','MSFT', etc.)
        language: language of news (default = English)
        max_articles: number of articles to fetch (default = 20)
    Returns:
        Pandas DataFrame with title, description, source, and publication date
    """
    all_articles = newsapi.get_everything(
        q=query,
        language=language,
        sort_by='publishedAt',
        page_size=max_articles
    )

    # Convert results to DataFrame
    if 'articles' not in all_articles:
        return pd.DataFrame()

    articles = all_articles['articles']
    
    news_df = pd.DataFrame([{
        'title': article['title'],
        'description': article['description'],
        'publishedAt': article['publishedAt'],
        'source': article['source']['name'],
        'url': article['url']
    } for article in articles])

    return news_df

# Example usage
if __name__ == "__main__":
    df = fetch_latest_news("Tesla stock")
    print(df.head())
