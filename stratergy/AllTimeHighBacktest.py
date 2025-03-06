from functools import lru_cache

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

from Index import fetch_nifty500_list
from stratergy.Index import fetch_nifty50_list

@lru_cache(maxsize=64)
def get_data(ticker):
    try:
        data = yf.download(ticker,interval='1wk', start="2000-01-01", end="2025-01-01", auto_adjust=False)

        data.columns = [col[0].replace(r'/.+$', '') if isinstance(col, tuple) else col for col in data.columns]

        if data.empty:
            raise ValueError(f"No data found for ticker {ticker}.")

        data['Week'] = data.index.to_period('W')
        weekly_data = data.resample('W').last()
        weekly_data['30W_MA'] = weekly_data['Close'].rolling(window=30, min_periods=30).mean()  # 30-week MA

        return weekly_data

    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

def find_trades(data):
    entries = []
    exits = []
    entry_price = None
    next_entry_date = pd.Timestamp("2010-01-01")
    in_trade = False  # Added flag to track if we are currently in a trade

    try:
        # Calculate cumulative max high up to each month's end
        daily_data = data.resample('D').ffill()  # Fill forward to ensure daily continuity
        daily_data['Cumulative_High'] = daily_data['High'].cummax()

        monthly_resampled = daily_data.resample('ME').apply(lambda x: x.iloc[-1])
        monthly_highs = monthly_resampled['Cumulative_High']
        monthly_closes = monthly_resampled['Close']

        for i in range(8, len(monthly_closes)):
            if monthly_closes.index[i] < next_entry_date:
                continue

            if monthly_closes[i] > monthly_highs[i-1]:
                entry_date = monthly_closes.index[i]
                entry_price = monthly_closes[i]
                entries.append((entry_date, entry_price))
                print(f"Entry on {entry_date}: {entry_price}")

                weekly_closes_below_ma = data[(data.index > entry_date) & (data['Close'] < data['30W_MA'])]

                if not weekly_closes_below_ma.empty:
                    exit_date = weekly_closes_below_ma.index[0]
                    next_entry_date = exit_date
                    exit_price = weekly_closes_below_ma['Close'][0]
                    exits.append((exit_date, exit_price))
                    print(f"Exit on {exit_date}: {exit_price}")

                    profit_loss = exit_price - entry_price
                    print(f"Profit/Loss for trade: {profit_loss}\n")

                    entry_price = None
                    in_trade = False  # Exiting a trade

    except Exception as e:
        print(f"Error processing trades: {e}")

    total_profit_loss = sum(exit[1] - entry[1] for entry, exit in zip(entries, exits))
    return entries, exits, total_profit_loss


def main():
    # Get a list of Nifty 500 tickers (these are just examples; you'll need to get the full list)
    nifty500_tickers = fetch_nifty50_list()

    # Store stocks that have broken their all-time high
    new_highs = []

    # Check each stock in the list
    for ticker in nifty500_tickers:
        print(f"********************! {ticker}  !********************")

        data = get_data(ticker)
        if data is not None:
            entries, exits, overall_profit_loss = find_trades(data)
            if entries and exits:
                print(f"Overall Profit/Loss: {overall_profit_loss}")
            else:
                print("No trades occurred.")
        else:
            print("Data retrieval failed. Exiting.")


if __name__ == "__main__":
    main()

