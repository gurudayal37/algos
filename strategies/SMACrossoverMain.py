from backtests.SMABacktester import SMABacktester
from data.Index import fetch_nifty50_list

def main():
    # Get a list of Nifty 500 tickers (these are just examples; you'll need to get the full list)
    nifty50_tickers = fetch_nifty50_list()

    # Check each stock in the list
    for ticker in nifty50_tickers[0:1]:
        try:
            print(f" Testing 50/200 sma crossover strategy {ticker}")
            tester = SMABacktester(ticker , 50, 100, "2021-01-01", "2025-01-01")
            buy_hold_returns, statergy_returns = tester.test_strategy()
            print(f" Buy and hold returns {buy_hold_returns}")
            print(f" Statergy returns {statergy_returns}")
            tester.plot_results()


        except Exception as e:
            print(f"Error processing {ticker}: {str(e)}")


if __name__ == "__main__":

    main()