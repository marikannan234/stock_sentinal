from transformers import pipeline
import pandas as pd

def analyze_sentiment(df):
    sentiment_pipeline = pipeline("sentiment-analysis", model="ProsusAI/finbert")
    sentiments = []
    
    for text in df['title']:
        if not isinstance(text, str):
            sentiments.append("NEUTRAL")
            continue
        result = sentiment_pipeline(text[:512])[0]
        sentiments.append(result['label'])
    
    df['sentiment'] = sentiments
    sentiment_summary = df['sentiment'].value_counts().to_dict()
    return df, sentiment_summary
