import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

from Index import fetch_nifty500_list
from stratergy.Index import fetch_nifty50_list


# Define a function to get historical data and check for new all-time highs
def check_new_all_time_high(ticker, period='7y'):
    # Fetch historical market data
    data = yf.download(ticker, period=period, interval='1mo' , progress=False)


    data.columns = [col[0].replace(r'/.+$', '') if isinstance(col, tuple) else col for col in data.columns]

    if data.empty or len(data) < 1:
        return False, None

    # Calculate the all-time high by considering all historical data
    all_time_high = data['High'].iloc[:-1].max()
    previous_all_time_high_date = data['High'].iloc[:-1].idxmax()
    print(f"{ticker} has hit a previous all-time high  of {all_time_high} on {previous_all_time_high_date}!")

    # Get the most recent closing price
    last_close = data['High'].iloc[-1:].max()

    if last_close > all_time_high:
        # Find the date where the all-time high was recorded
        all_time_high_date = data['High'].iloc[-1:].idxmax()
        return True, all_time_high_date
    return False, None


def main():
    # Get a list of Nifty 500 tickers (these are just examples; you'll need to get the full list)
    nifty500_tickers = fetch_nifty500_list()

    # Store stocks that have broken their all-time high
    new_highs = []

    # Check each stock in the list
    for ticker in nifty500_tickers:
        try:
            is_new_high, high_date = check_new_all_time_high(ticker)
            if is_new_high:
                print(f"********************! {ticker} has hit a new all-time high on {high_date} !********************")
                new_highs.append((ticker, high_date))
        except Exception as e:
            print(f"Error processing {ticker}: {str(e)}")

    # Output all stocks that have hit new highs
    print("Stocks hitting new all-time highs:")
    for ticker, high_date in new_highs:
        print(f"{ticker}: {high_date}")


if __name__ == "__main__":
    main()