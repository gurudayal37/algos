import yfinance as yf
import pandas as pd
from data.Index import fetch_nifty50_list

# List of Nifty 50 stock symbols


# Function to fetch data from Yahoo Finance
def fetch_data(symbol, start_date, end_date):
    data = yf.download(symbol, start=start_date, end=end_date, interval='5m')
    data.columns = [col[0].replace(r'/.+$', '') if isinstance(col, tuple) else col for col in data.columns]

    if not data.empty:
        data['Symbol'] = symbol
        return data
    else:
        return pd.DataFrame()  # Return empty DataFrame if no data


def determine_gaps(data):

    # Get the first opening price of each day for each stock
    first_open = data.groupby(['Symbol', 'Date'])['Open'].first()

    # Get the last closing price of the previous day for each stock
    last_close_prev_day = data.groupby(['Symbol', 'Date']).last()['Close'].groupby(level=0).shift(1)

    # Create a DataFrame for stock-symbol-wise first open and last close
    gap_data = pd.DataFrame({'First Open': first_open, 'Prev Close': last_close_prev_day}).dropna()

    # Calculate the percentage gap for the first candle of each day
    gap_data['Gap'] = (gap_data['First Open'] - gap_data['Prev Close']) / gap_data['Prev Close'] * 100

    # Separate into positive and negative gaps
    positive_gaps = gap_data[gap_data['Gap'] > 0]
    negative_gaps = gap_data[gap_data['Gap'] < 0]

    # Get top 3 positive gaps (gap ups) and top 3 negative gaps (gap downs) globally
    gap_ups = positive_gaps.nlargest(3, 'Gap')
    gap_downs = negative_gaps.nsmallest(3, 'Gap')

    return gap_ups, gap_downs

# Backtest strategy
def backtest_strategy(data, capital):
    results = []
    for date, group in data.groupby('Date'):
        gap_ups, gap_downs = determine_gaps(group)
        long_stocks = gap_ups['Symbol'].unique()
        short_stocks = gap_downs['Symbol'].unique()

        # Conduct trades for gap ups
        for stock in long_stocks:
            stock_data = group[group['Symbol'] == stock]
            entry_price = stock_data.iloc[0]['Open']
            stop_loss = entry_price * 0.98
            target = entry_price * 1.04
            for _, row in stock_data.iterrows():
                if row['Low'] <= stop_loss:
                    results.append((date, stock, 'Long', entry_price, stop_loss, 'Stopped out'))
                    break
                elif row['High'] >= target:
                    results.append((date, stock, 'Long', entry_price, target, 'Target reached'))
                    break
                elif row.name == stock_data.index[-1]:
                    results.append((date, stock, 'Long', entry_price, row['Close'], 'End of day'))

        # Conduct trades for gap downs
        for stock in short_stocks:
            stock_data = group[group['Symbol'] == stock]
            entry_price = stock_data.iloc[0]['Open']
            stop_loss = entry_price * 1.01
            target = entry_price * 0.98
            for _, row in stock_data.iterrows():
                if row['High'] >= stop_loss:
                    results.append((date, stock, 'Short', entry_price, stop_loss, 'Stopped out'))
                    break
                elif row['Low'] <= target:
                    results.append((date, stock, 'Short', entry_price, target, 'Target reached'))
                    break
                elif row.name == stock_data.index[-1]:
                    results.append((date, stock, 'Short', entry_price, row['Close'], 'End of day'))

    return results

def main():
    # Fetch data for each symbol
    all_data = []
    nifty50_tickers = fetch_nifty50_list()[:2]

    for symbol in nifty50_tickers:
        print(f"Fetching data for {symbol}...")
        stock_data = fetch_data(symbol, '2025-02-01', '2025-02-28')
        if not stock_data.empty:
            stock_data['Date'] = stock_data.index.date
            all_data.append(stock_data)

    # Combine all data into a single DataFrame
    if all_data:
        data = pd.concat(all_data, ignore_index=True)

        # Run backtest
        capital = 1000000  # 10 lakh INR
        trades = backtest_strategy(data, capital)

        # Print out trades
        for trade in trades:
            date, stock, position, entry_price, exit_price, result = trade
            pnl = (exit_price - entry_price) * (-1 if position == 'Short' else 1)  # Calculate P&L based on trade direction
            invested_cap = capital / 6  # Divide capital in 6 equal parts for 6 trades
            pl_ratio = pnl / entry_price * invested_cap
            print(
                f"Date: {date}, Stock: {stock}, Position: {position}, Entry: {entry_price:.2f}, Exit: {exit_price:.2f}, {result}, P&L: {pl_ratio:.2f}")
    else:
        print("No data available to backtest.")

if __name__ == "__main__":
    main()