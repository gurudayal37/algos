import yfinance as yf
import logging
from datetime import datetime
import time

# Configure logging
logging.basicConfig(filename="nifty50_earnings_sue.log", level=logging.INFO, format="%(asctime)s - %(message)s")

# NIFTY 50 stocks with Yahoo Finance symbols
# nifty50_tickers = [
#     "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "HINDUNILVR.NS",
#     "SBIN.NS", "BAJFINANCE.NS", "BHARTIARTL.NS", "KOTAKBANK.NS", "ITC.NS", "LT.NS",
#     "HCLTECH.NS", "AXISBANK.NS", "MARUTI.NS", "ASIANPAINT.NS", "SUNPHARMA.NS", "TITAN.NS",
#     "ULTRACEMCO.NS", "TECHM.NS", "NESTLEIND.NS", "INDUSINDBK.NS", "WIPRO.NS", "POWERGRID.NS",
#     "BAJAJFINSV.NS", "TATAMOTORS.NS", "TATACONSUM.NS", "HDFCLIFE.NS", "DRREDDY.NS", "ONGC.NS",
#     "HINDALCO.NS", "JSWSTEEL.NS", "DIVISLAB.NS", "ADANIPORTS.NS", "CIPLA.NS", "GRASIM.NS",
#     "NTPC.NS", "BRITANNIA.NS", "APOLLOHOSP.NS", "COALINDIA.NS", "SBILIFE.NS", "EICHERMOT.NS",
#     "BAJAJ-AUTO.NS", "TATASTEEL.NS", "HEROMOTOCO.NS", "BPCL.NS", "M&M.NS", "IOC.NS",
# ]

nifty50_tickers = ["ABB.NS"]


def calculate_sue(earnings_data):
    """
    Calculate Standardized Unexpected Earnings (SUE)

    Parameters:
    earnings_data (pd.DataFrame): DataFrame containing earnings information

    Returns:
    float: SUE value
    """
    try:
        # Extract EPS estimates and reported EPS
        eps_estimates = earnings_data['EPS Estimate']
        reported_eps = earnings_data['Reported EPS']

        # Calculate mean expected EPS
        mean_expected_eps = eps_estimates.mean()

        # Calculate standard deviation of expected EPS
        std_eps = eps_estimates.std()

        # Handle case where standard deviation is zero or very small
        if std_eps < 1e-8:
            logging.warning("Standard deviation too small for meaningful SUE calculation")
            return None

        # Calculate SUE
        sue = (reported_eps - mean_expected_eps) / std_eps

        return sue
    except Exception as e:
        logging.error(f"Error calculating SUE: {e}")
        return None


def analyze_earnings(ticker):
    """
    Analyze earnings for a specific stock

    Parameters:
    ticker (str): Stock ticker symbol

    Returns:
    None
    """
    try:
        # Fetch stock data
        stock = yf.Ticker(ticker)

        # Get earnings dates
        earnings = stock.earnings_dates

        earnings_estimates = stock.earnings_estimate


        # Check if earnings data exists
        if earnings is None or earnings.empty:
            logging.warning(f"No earnings data available for {ticker}")
            return

        # Calculate SUE
        sue = calculate_sue(earnings)

        # Check if SUE calculation was successful
        if sue is None:
            logging.warning(f"Could not calculate SUE for {ticker}")
            return

        # Prepare log message with detailed earnings information
        log_msg = (
            f"Stock: {ticker}\n"
            f"SUE: {sue:.2f}\n"
            f"Earnings Date: {earnings.index[0].strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Expected EPS: {earnings['EPS Estimate'].mean():.2f}\n"
            f"Reported EPS: {earnings['Reported EPS'].values[0]:.2f}"
        )

        # Generate trading signal based on SUE
        if sue > 2:
            signal = "STRONG BUY SIGNAL"
            log_msg = f"{signal}\n{log_msg}"
            logging.info(log_msg)
            print(log_msg)
        elif sue < -2:
            signal = "STRONG SELL SIGNAL"
            log_msg = f"{signal}\n{log_msg}"
            logging.info(log_msg)
            print(log_msg)
        else:
            signal = "HOLD SIGNAL"
            log_msg = f"{signal}\n{log_msg}"
            logging.info(log_msg)
            print(log_msg)

    except Exception as e:
        logging.error(f"Error analyzing earnings for {ticker}: {e}")


# def main():
#     for ticker in nifty50_tickers:
#         try:
#             stock = yf.Ticker(ticker)
#             earnings = stock.earnings_dates  # Fetch earnings data
#
#             if earnings is None or earnings.empty:
#                 logging.warning(f"No earnings data available for {ticker}")
#                 continue
#
#             for index, row in earnings.iterrows():
#                 eps_estimate = row["EPS Estimate"]
#                 reported_eps = row["Reported EPS"]
#                 surprise = row["Surprise(%)"]
#                 earnings_date = index.strftime("%Y-%m-%d %H:%M:%S")
#
#                 if surprise > 0:  # Buy signal if earnings surprise is positive
#                     log_msg = (
#                         f"BUY SIGNAL: {ticker} - Earnings Date: {earnings_date}, "
#                         f"EPS Estimate: {eps_estimate}, Reported EPS: {reported_eps}, "
#                         f"Surprise: {surprise:.2f}%"
#                     )
#                     print(log_msg)
#                     logging.info(log_msg)
#                 elif surprise < 0:
#                     log_msg = (
#                         f"SELL SIGNAL: {ticker} - Earnings Date: {earnings_date}, "
#                         f"EPS Estimate: {eps_estimate}, Reported EPS: {reported_eps}, "
#                         f"Surprise: {surprise:.2f}%"
#                     )
#                     print(log_msg)
#                     logging.info(log_msg)
#                 else :
#                     log_msg = (
#                         f"No data Earnings Date: {earnings_date} "
#                     )
#                     print(log_msg)
#
#         except Exception as e:
#             logging.error(f"Error fetching earnings data for {ticker}: {e}")
def main():
    """
    Main function to analyze earnings for Nifty 50 stocks
    """
    print("Starting Earnings Analysis...")

    # Track analysis progress
    total_stocks = len(nifty50_tickers)
    processed_stocks = 0

    # Analyze earnings for each ticker
    for ticker in nifty50_tickers:
        try:
            analyze_earnings(ticker)
            processed_stocks += 1

            # Progress update
            progress = (processed_stocks / total_stocks) * 100
            print(f"Progress: {progress:.2f}% ({processed_stocks}/{total_stocks})")

        except Exception as e:
            logging.error(f"Error processing {ticker}: {e}")

    print("Earnings analysis completed. Check logs for details.")


if __name__ == "__main__":
    main()
