import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf

# Parameters
nifty_50_symbols = [
    "ABB.NS", "ACC.NS", "ADANIGREEN.NS", "ADANIPORTS.NS", "AMBUJACEM.NS",
    "ASIANPAINT.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJAJFINSV.NS", "BAJFINANCE.NS",
    "BANDHANBNK.NS", "BANKBARODA.NS", "BERGEPAINT.NS", "BHARTIARTL.NS", "BIOCON.NS",
    "BPCL.NS", "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "COLPAL.NS",
    "CONCOR.NS", "DABUR.NS", "DIVISLAB.NS", "DLF.NS", "DRREDDY.NS",
    "EICHERMOT.NS", "GAIL.NS", "GLAND.NS", "GLENMARK.NS", "GMRINFRA.NS",
    "GODREJCP.NS", "GRASIM.NS", "HAVELLS.NS", "HEROMOTOCO.NS", "HINDALCO.NS",
    "HINDPETRO.NS", "HINDUNILVR.NS", "HDFCBANK.NS", "HDFCLIFE.NS",
    "ICICIBANK.NS", "ICICIPRULI.NS", "INDHOTEL.NS", "INDIGO.NS", "INDUSINDBK.NS",
    "INFY.NS", "IOC.NS", "ITC.NS", "JSWSTEEL.NS", "JUBLFOOD.NS",
    "KOTAKBANK.NS", "LT.NS", "LUPIN.NS", "M&M.NS", "MARICO.NS",
    "MARUTI.NS", "MCDOWELL-N.NS", "MFSL.NS", "NAUKRI.NS", "NAVINFLUOR.NS",
    "NESTLEIND.NS", "NMDC.NS", "ONGC.NS", "PIIND.NS", "PIDILITIND.NS",
    "PNB.NS", "POWERGRID.NS", "RELIANCE.NS", "SBICARD.NS", "SBILIFE.NS",
    "SBIN.NS", "SHREECEM.NS", "SIEMENS.NS", "SRF.NS", "SUNPHARMA.NS",
    "TATACONSUM.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "TCS.NS", "TECHM.NS",
    "TITAN.NS", "TORNTPHARM.NS", "ULTRACEMCO.NS", "UPL.NS", "VEDL.NS",
    "WIPRO.NS", "ZEEL.NS"
]
capital = 100000  # Trading capital
risk_to_reward = 2  # Risk-to-reward ratio
risk_percentage = 0.01  # Risk per trade as a fraction of capital


# Function to calculate moving averages
def calculate_sma(data, window):
    return data['Close'].rolling(window=window).mean()


# Fetch historical data
def fetch_historical_data(symbol):
    print(f"Fetching historical data for {symbol}...")
    df = yf.download(symbol, start="2022-01-01", end="2025-01-01", progress=False)
    print(f"Data fetched for {symbol}, total records: {len(df)}")
    df.columns = [col[0].replace(r'/.+$', '') if isinstance(col, tuple) else col for col in df.columns]
    print(df.columns)
    return df

def plot_trade(df, symbol, entry_date, exit_date):
    # Extract the data within the trade period for plotting
    plot_data = df.loc[entry_date:exit_date]

    # Create a new DataFrame for plotting with mplfinance
    plot_data = plot_data[['Open', 'High', 'Low', 'Close', 'Volume']]

    # Moving averages to highlight
    ma15 = df['SMA_15']
    ma30 = df['SMA_30']
    ma150 = df['SMA_150']

    # Additional moving averages can be passed in as a dictionary
    moving_avgs = {'MA15': ma15, 'MA30': ma30, 'MA150': ma150}

    # Plot using mplfinance
    mpf.plot(
        plot_data,
        type='candle',
        volume=True,
        title=f'{symbol} - Trade from {entry_date} to {exit_date}',
        addplot=[
            mpf.make_addplot(ma15.loc[entry_date:exit_date], color='blue', width=1.0),
            mpf.make_addplot(ma30.loc[entry_date:exit_date], color='orange', width=1.0),
            mpf.make_addplot(ma150.loc[entry_date:exit_date], color='green', width=1.0)
        ]
    )

# Main function to test strategy
def test_strategy():
    trades = []
    for symbol in nifty_50_symbols[:3]:
        print(f"\nTesting strategy for {symbol}...")
        try:
            df = fetch_historical_data(symbol)

            df['SMA_150'] = calculate_sma(df, 150)
            df['SMA_30'] = calculate_sma(df, 30)
            df['SMA_15'] = calculate_sma(df, 15)

            df.dropna(inplace=True)

            for i in range(3, len(df)):
                # Check if conditions were met for a potential entry
                condition_150 = df['SMA_150'].iloc[i] > df['SMA_150'].iloc[i - 1]
                condition_30 = df['SMA_30'].iloc[i] > df['SMA_30'].iloc[i - 1]
                condition_15 = df['SMA_15'].iloc[i] > df['SMA_15'].iloc[i - 1]

                if condition_150 and condition_30 and condition_15:

                    # Execute a detailed comparison
                    low_below_sma15 = (df['Low'].iloc[i] <= df['SMA_15'].iloc[i])
                    green_candle = (df['Close'].iloc[i] > df['Open'].iloc[i])

                    if low_below_sma15 and green_candle:
                        print(f"Entry criteria met on {df.index[i]} for {symbol}")
                        entry_price = df['High'].iloc[i]
                        stop_loss = min(df['Low'].iloc[i - 1], df['Low'].iloc[i - 2])
                        risk = entry_price - stop_loss
                        if risk <= 0:
                            print("Invalid risk calculation, possible issue in price data.")
                            continue
                        position_size = (capital * risk_percentage) / risk

                        target_price = entry_price + (entry_price - stop_loss) * risk_to_reward

                        entry_date = df.index[i]
                        exit_date = None
                        profit = None

                        # Look ahead to find exit based on target or stop loss
                        for j in range(i + 1, len(df)):
                            current_price = df['Close'].iloc[j]
                            if current_price >= target_price:
                                profit = (target_price - entry_price) * position_size
                                exit_date = df.index[j]
                                trades.append((symbol, entry_date, exit_date, "Profit", profit))
                                print(f"Target hit for {symbol} on {exit_date}, Profit: {profit}")
                                plot_trade(df, symbol, entry_date, exit_date)

                                break
                            elif current_price <= stop_loss:
                                loss = (entry_price - stop_loss) * position_size
                                exit_date = df.index[j]
                                trades.append((symbol, entry_date, exit_date, "Loss", loss))
                                print(f"Stop loss hit for {symbol} on {exit_date}, Loss: {loss}")
                                plot_trade(df, symbol, entry_date, exit_date)
                                break

        except Exception as e:
            print(f"Error processing {symbol}: {e}")

    # Print each trade and overall results
    total_profit = 0
    total_loss = 0
    for trade in trades:
        symbol, entry_date, exit_date, result, amount = trade
        print(f"Symbol: {symbol}, Entry Date: {entry_date}, Exit Date: {exit_date}, Result: {result}, Amount: {amount}")
        if result == "Profit":
            total_profit += amount
        else:
            total_loss += amount

    overall_result = total_profit + total_loss
    print("\nSummary:")
    print(f"Total Profit: {total_profit}")
    print(f"Total Loss: {total_loss}")
    print(f"Overall Profit/Loss: {overall_result}")


# Run the strategy
def main():
    test_strategy()


if __name__ == "__main__":
    main()