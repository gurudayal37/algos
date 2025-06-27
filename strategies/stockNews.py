import yfinance as yf
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Example Nifty 50 tickers (you can expand this list or import from your data module)
nifty50_tickers = ['INDHOTEL.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'TORNTPHARM.NS','JIOFIN.NS','ASIANPAINT.NS']

analyzer = SentimentIntensityAnalyzer()

for ticker in nifty50_tickers:
    print(f"\nNews for {ticker}:")
    try:
        stock = yf.Ticker(ticker)
        news_items = getattr(stock, 'news', None)
        if not news_items:
            print("  No news found for this ticker.")
            continue
        for item in news_items[:2]:
            content = item.get('content', {})
            headline = content.get('title', 'No title')
            url = (
                content.get('clickThroughUrl', {}).get('url') or
                content.get('canonicalUrl', {}).get('url') or
                'No link'
            )
            sentiment = analyzer.polarity_scores(content)
            if sentiment['compound'] >= 0.05:
                sentiment_label = 'Positive'
            elif sentiment['compound'] <= -0.05:
                sentiment_label = 'Negative'
            else:
                sentiment_label = 'Neutral'
            print(f"  [{sentiment_label}] {headline}")
            print(f"      {url}")
    except Exception as e:
        print(f"  Error fetching news for {ticker}: {e}")
