import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

from data.Index import fetch_nifty500_list, fetch_nifty_list_all
from data.Sectors import sector_mapping
from utils.helper import get_piotroski_score


# Define a function to get historical data and check for new all-time highs
def check_new_all_time_high(ticker, period='10y'):
    # Fetch historical market data
    data = yf.download(ticker, period=period, interval='1mo' , progress=False)


    data.columns = [col[0].replace(r'/.+$', '') if isinstance(col, tuple) else col for col in data.columns]

    if data.empty or len(data) < 1:
        return False, None

    # Calculate the all-time high by considering all historical data
    all_time_high = data['High'].iloc[:-1].max()
    previous_all_time_high_date = data['High'].iloc[:-1].idxmax()
    print(f"{ticker} has hit a previous all-time high  of {all_time_high} on {previous_all_time_high_date}!")

    # Check if previous all-time high was more than 3 months ago
    if isinstance(previous_all_time_high_date, pd.Timestamp):
        previous_ath_date = previous_all_time_high_date.to_pydatetime()
    else:
        previous_ath_date = pd.to_datetime(previous_all_time_high_date)
    three_months_ago = datetime.now() - pd.DateOffset(months=2)
    if previous_ath_date > three_months_ago:
        return False, None

    # Get the most recent closing price
    last_close = data['Close'].iloc[-1:].max()

    if last_close > all_time_high:
        # Find the date where the all-time high was recorded
        all_time_high_date = data['High'].iloc[-1:].idxmax()
        return True, all_time_high_date
    return False, None


def main():
    # Get a list of Nifty 500 tickers (these are just examples; you'll need to get the full list)
    nifty500_tickers = fetch_nifty_list_all()

    # Store stocks that have broken their all-time high
    new_highs = []
    groupByTickers = {}

    # Check each stock in the list
    for ticker in nifty500_tickers:
        try:
            is_new_high, high_date = check_new_all_time_high(ticker)
            
            if is_new_high:
                sector = sector_mapping.get(ticker, "Unknown")
                if sector not in groupByTickers:
                    groupByTickers[sector] = []
                groupByTickers[sector].append((ticker, high_date))
                print(f"********************! {ticker} has hit a new all-time high on {high_date} | sector {sector} !********************")
                new_highs.append((ticker, high_date))
        except Exception as e:
            print(f"Error processing {ticker}: {str(e)}")

    # Output all stocks that have hit new highs, grouped by sector
    print("Stocks hitting new all-time highs grouped by sector:")
    for sector, tickers in groupByTickers.items():
        print(f"Sector: {sector}")
        for ticker, high_date in tickers:
            print(f"  {ticker}: {high_date}")
            piotroski_score = get_piotroski_score(ticker)
            if piotroski_score is not None:
                print(f"{ticker}: Piotroski Score = {piotroski_score}/9")
            else:
                print(f"{ticker}: Piotroski Score = Not available")


if __name__ == "__main__":
    main()