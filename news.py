from newsapi import NewsApiClient
import yfinance as yf
api_key = "5720ee2c29bb4e02871b73e7d105ed02"
import main

def extract_common_name(company_name):
    stopwords = {"inc", "inc.", "corporation", "corp", "corp.", "co", "co.", "ltd", "ltd.", "plc", "class", "a", "b"}
    words = company_name.lower().split()
    filtered = [word.capitalize() for word in words if word not in stopwords]
    return ' '.join(filtered[:2])  # Use 1 or 2 top words

def get_stock_news(ticker):
    newsapi = NewsApiClient(api_key=api_key)
    newsData = []

    ticker = extract_common_name(ticker)

    query = f"{ticker} stock OR {ticker} shares OR {ticker} earnings OR {ticker} price"
    
    # Domains focused on business/finance
    business_domains = "cnbc.com,bloomberg.com,marketwatch.com,finance.yahoo.com,reuters.com"

    news_ = newsapi.get_everything(
        q=query,
        language="en",
        sort_by="relevancy",
        domains=business_domains
    )['articles']

    for i, article in enumerate(news_[:6]):
        newsData.append((
            article['title'],
            article['description'],
            article['urlToImage'],
            article['url']
        ))
    
    return newsData


def get_stock_news_data(ticker):
    newsapi = NewsApiClient(api_key=api_key)
    newsData = []

    ticker = extract_common_name(ticker)

    query = f"{ticker} stock OR {ticker} shares OR {ticker} earnings OR {ticker} price"
    
    # Domains focused on business/finance
    business_domains = "cnbc.com,bloomberg.com,marketwatch.com,finance.yahoo.com,reuters.com"

    news_ = newsapi.get_everything(
        q=query,
        language="en",
        sort_by="relevancy",
        domains=business_domains
    )['articles']

    for i, article in enumerate(news_[:100]):
        newsData.append((
            article['title'],
            article['description'],
            article['urlToImage'],
            article['url']
        ))
    
    return newsData
