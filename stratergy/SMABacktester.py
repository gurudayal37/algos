import pandas as pd
import numpy as np
import yfinance as yf
from itertools import product
import matplotlib.pyplot as plt

class SMABacktester():

    def __init__(self, symbol, SMA_S, SMA_L, start, end):
        self.symbol = symbol
        self.SMA_S = SMA_S
        self.SMA_L = SMA_L
        self.start = start
        self.end = end
        self.results = None
        self.entry_exit_signals = []
        self.get_data()
        self.prepare_data()

    def __repr__(self):
        return "SMABacktester(symbol = {}, SMA_S = {}, SMA_L = {}, start = {}, end = {})".format(self.symbol,
                                                                                                 self.SMA_S, self.SMA_L,
                                                                                                 self.start, self.end)

    def get_data(self):

        raw = yf.download(self.symbol, start =self.start, end= self.end, interval='1d', progress=False)
        raw.columns = [col[0].replace(r'/.+$', '') if isinstance(col, tuple) else col for col in raw.columns]

        # raw = pd.read_csv("forex_pairs.csv", parse_dates=["Date"], index_col="Date")
        # raw = raw[self.symbol].to_frame().dropna()
        # raw = raw.loc[self.start:self.end].copy()
        # raw.rename(columns={self.symbol: "price"}, inplace=True)

        raw.rename(columns={"Close": "price"}, inplace=True)
        raw["returns"] = np.log(raw["price"] / raw["price"].shift(1))
        self.data = raw

    def prepare_data(self):
        '''Prepares the data for strategy backtesting (strategy-specific).
        '''
        data = self.data.copy()
        data["SMA_S"] = data["price"].rolling(self.SMA_S).mean()
        data["SMA_L"] = data["price"].rolling(self.SMA_L).mean()
        self.data = data

    def set_parameters(self, SMA_S=None, SMA_L=None):
        ''' Updates SMA parameters and the prepared dataset.
        '''
        if SMA_S is not None:
            self.SMA_S = SMA_S
            self.data["SMA_S"] = self.data["price"].rolling(self.SMA_S).mean()
        if SMA_L is not None:
            self.SMA_L = SMA_L
            self.data["SMA_L"] = self.data["price"].rolling(self.SMA_L).mean()

    def test_strategy(self):
        ''' Backtests the SMA-based trading strategy.
        Prints the entry/exit dates and the respective profit/loss in percentage.
        '''
        data = self.data.copy().dropna()
        data["position"] = np.where((data["SMA_S"].shift(1) < data["SMA_L"].shift(1)) &
                                    (data["SMA_S"] > data["SMA_L"]), 1,
                                    np.where((data["SMA_S"].shift(1) > data["SMA_L"].shift(1)) &
                                             (data["SMA_S"] < data["SMA_L"]), -1, 0))

        data["strategy"] = data["position"].shift(1) * data["returns"]
        data.dropna(inplace=True)

        # Track trades and calculate profit/loss
        in_position = False
        entry_date = None
        entry_price = None

        for i in range(1, len(data)):
            if data["position"].iloc[i] == 1:  # Enter a new position (buy)
                if not in_position:  # Only enter if not in a position
                    entry_date = data.index[i]
                    entry_price = data["price"].iloc[i]
                    in_position = True

            elif data["position"].iloc[i] == -1:  # Exit position (sell)
                if in_position:  # Only exit if in a position
                    exit_date = data.index[i]
                    exit_price = data["price"].iloc[i]
                    pl_pct = (exit_price - entry_price) / entry_price * 100 if entry_price != 0 else 0
                    self.entry_exit_signals.append((entry_date, exit_date, pl_pct))
                    print(f"Entry: {entry_date}, Exit: {exit_date}, P&L: {pl_pct:.2f}%")
                    in_position = False

        data["creturns"] = data["returns"].cumsum().apply(np.exp)
        data["cstrategy"] = data["strategy"].cumsum().apply(np.exp)
        self.results = data

        perf = data["cstrategy"].iloc[-1]  # absolute performance of the strategy
        outperf = perf - data["creturns"].iloc[-1]  # out-/underperformance of strategy
        return round(perf, 6), round(outperf, 6)

    def plot_results(self):
        ''' Plots the performance of the trading strategy and compares to "buy and hold".
        '''
        if self.results is None:
            print("Run test_strategy() first.")
        else:
            title = "{} | SMA_S = {} | SMA_L = {}".format(self.symbol, self.SMA_S, self.SMA_L)
            self.results[["creturns", "cstrategy"]].plot(title=title, figsize=(12, 8))
            plt.show()

    def optimize_parameters(self, SMA_S_range, SMA_L_range):
        ''' Finds the optimal strategy (global maximum) given the SMA parameter ranges.

        Parameters
        ----------
        SMA_S_range, SMA_L_range: tuple
            tuples of the form (start, end, step size)
        '''
        combinations = list(product(range(*SMA_S_range), range(*SMA_L_range)))

        # test all combinations
        results = []
        for comb in combinations:
            self.set_parameters(comb[0], comb[1])
            results.append(self.test_strategy()[0])

        best_perf = np.max(results)  # best performance
        opt = combinations[np.argmax(results)]  # optimal parameters

        # run/set the optimal strategy
        self.set_parameters(opt[0], opt[1])
        self.test_strategy()

        # create a df with many results
        many_results = pd.DataFrame(data=combinations, columns=["SMA_S", "SMA_L"])
        many_results["performance"] = results
        self.results_overview = many_results

        return opt, best_perf