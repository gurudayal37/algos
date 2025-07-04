import yfinance as yf

def download_data(ticker, interval='1mo', period='7y'):
    data = yf.download(ticker, period=period, interval=interval , progress=False)
    data.columns = [col[0].replace(r'/.+$', '') if isinstance(col, tuple) else col for col in data.columns]
    return data