import pandas as pd
import numpy as np
import yfinance as yf
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
from sklearn.metrics import mean_squared_error, mean_absolute_error
import matplotlib.pyplot as plt
import warnings
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.Index import fetch_nifty5_list

warnings.filterwarnings('ignore')

class ARIMABacktester:
    """
    ARIMA Backtesting System for Nifty 50 Stocks
    Downloads 10 years of weekly data, splits 70:30 train/test
    Compares ARIMA(2,1,2) with buy-and-hold strategy
    """
    
    def __init__(self, symbol, start_date=None, end_date=None):
        self.symbol = symbol
        self.start_date = start_date or (datetime.now() - timedelta(days=365*10))
        self.end_date = end_date or datetime.now()
        self.data = None
        self.train_data = None
        self.test_data = None
        self.arima_model = None
        self.fitted_model = None
        self.predictions = None
        self.results = {}
        
    def download_data(self):
        """Download 10 years of weekly data for the stock"""
        try:
            print(f"Downloading weekly data for {self.symbol}...")
            data = yf.download(
                self.symbol, 
                start=self.start_date, 
                end=self.end_date, 
                interval='1wk',
                progress=False
            )
            
            # Clean column names
            data.columns = [col[0].replace(r'/.+$', '') if isinstance(col, tuple) else col 
                           for col in data.columns]
            
            # Use Close prices for analysis
            data = data[['Close']].copy()
            data.columns = ['price']
            data.dropna(inplace=True)
            
            if len(data) < 100:  # Need sufficient data
                print(f"Insufficient data for {self.symbol}: {len(data)} points")
                return False
                
            self.data = data
            print(f"Downloaded {len(data)} weekly data points for {self.symbol}")
            return True
            
        except Exception as e:
            print(f"Error downloading data for {self.symbol}: {str(e)}")
            return False
    
    def split_data(self, train_ratio=0.7):
        """Split data into train and test sets (70:30)"""
        if self.data is None:
            print("No data available. Run download_data() first.")
            return False
            
        split_idx = int(len(self.data) * train_ratio)
        self.train_data = self.data.iloc[:split_idx]
        self.test_data = self.data.iloc[split_idx:]
        
        print(f"Train data: {len(self.train_data)} points ({train_ratio*100}%)")
        print(f"Test data: {len(self.test_data)} points ({(1-train_ratio)*100}%)")
        return True
    
    def check_stationarity(self, data):
        """Check if time series is stationary using Augmented Dickey-Fuller test"""
        result = adfuller(data)
        return result[1] < 0.05  # p-value < 0.05 indicates stationarity
    
    def fit_arima_model(self, order=(2, 1, 2), train_window=100):
        """Fit ARIMA model using rolling window approach"""
        try:
            print(f"Fitting rolling ARIMA{order} model for {self.symbol} with train_window={train_window}...")
            
            # Use rolling window approach instead of single model fit
            self.train_window = train_window
            self.order = order
            
            # We'll fit models dynamically during prediction phase
            print(f"Rolling window ARIMA model configured successfully")
            return True
            
        except Exception as e:
            print(f"Error configuring rolling ARIMA model for {self.symbol}: {str(e)}")
            return None
    
    def make_predictions(self):
        """Make predictions using rolling window ARIMA approach"""
        if not hasattr(self, 'train_window'):
            print("No ARIMA model configured. Run fit_arima_model() first.")
            return False
            
        try:
            print(f"Generating predictions using rolling window approach...")
            
            # Combine train and test data for rolling window
            full_data = pd.concat([self.train_data, self.test_data])
            results = []
            
            # Start predictions from the beginning of test data
            test_start_idx = len(self.train_data)
            
            for i in range(test_start_idx, len(full_data)):
                if i % 50 == 0:
                    print(f"Processing observation {i}/{len(full_data)}")
                
                try:
                    # Use rolling window of data up to current point
                    train_series = full_data.iloc[i - self.train_window:i]
                    
                    # Fit ARIMA model on this window
                    model = ARIMA(train_series['price'], order=self.order)
                    fitted_model = model.fit()
                    
                    # Make one-step ahead forecast
                    forecast = fitted_model.forecast(steps=1)[0]
                    actual_price = full_data.iloc[i]['price']
                    
                    # Generate trading signal
                    current_price = train_series.iloc[-1]['price']
                    signal = 1 if forecast > current_price else -1
                    
                    results.append({
                        'date': full_data.index[i],
                        'actual_price': actual_price,
                        'predicted_price': forecast,
                        'signal': signal,
                        'current_price': current_price
                    })
                    
                except Exception as e:
                    print(f"Skipping index {i} due to error: {e}")
                    continue
            
            # Convert to DataFrame
            self.predictions_df = pd.DataFrame(results).set_index('date')
            self.predictions = self.predictions_df['predicted_price']
            
            print(f"Generated {len(self.predictions_df)} predictions using rolling window")
            return True
            
        except Exception as e:
            print(f"Error making predictions for {self.symbol}: {str(e)}")
            return False
    
    def create_rolling_arima_strategy(self, price_data, train_window=100, order=(2, 1, 2)):
        """
        Build trading strategy using rolling ARIMA forecasts on price data.
        Returns a DataFrame with predictions and trading signals.
        """
        results = []

        print(f"Training window: {train_window} observations")
        
        for i in range(train_window, len(price_data)):
            if i % 100 == 0:
                print(f"Processing observation {i}/{len(price_data)}")
            
            try:
                train_series = price_data.iloc[i - train_window:i]
                model = ARIMA(train_series, order=order)
                fitted_model = model.fit()
                forecast = fitted_model.forecast(steps=1)[0]
                actual_price = price_data.iloc[i]
                signal = 1 if forecast > train_series.iloc[-1] else -1

                results.append({
                    'date': price_data.index[i],
                    'actual_price': actual_price,
                    'predicted_price': forecast,
                    'signal': signal
                })
            except Exception as e:
                print(f"Skipping index {i} due to error: {e}")
                continue

        strategy_df = pd.DataFrame(results).set_index('date')
        return strategy_df
    
    def calculate_metrics(self):
        """Calculate performance metrics for rolling window ARIMA strategy"""
        if self.predictions_df is None:
            print("No predictions available. Run make_predictions() first.")
            return False
            
        try:
            # Get actual and predicted prices
            actual = self.predictions_df['actual_price'].values
            predicted = self.predictions_df['predicted_price'].values
            signals = self.predictions_df['signal'].values
            
            # Calculate prediction accuracy metrics
            mse = mean_squared_error(actual, predicted)
            rmse = np.sqrt(mse)
            mae = mean_absolute_error(actual, predicted)
            mape = np.mean(np.abs((actual - predicted) / actual)) * 100
            
            # Calculate returns
            actual_returns = np.diff(actual) / actual[:-1]
            
            # Buy and hold strategy returns
            buy_hold_return = (actual[-1] - actual[0]) / actual[0] * 100
            
            # ARIMA strategy returns based on signals
            # Apply signals to actual returns (shifted by 1 since we can't trade on current price)
            strategy_returns = signals[:-1] * actual_returns
            arima_total_return = np.sum(strategy_returns) * 100
            
            # Calculate additional metrics
            win_rate = np.sum(strategy_returns > 0) / len(strategy_returns) * 100
            avg_win = np.mean(strategy_returns[strategy_returns > 0]) if np.sum(strategy_returns > 0) > 0 else 0
            avg_loss = np.mean(strategy_returns[strategy_returns < 0]) if np.sum(strategy_returns < 0) > 0 else 0
            
            # Store results
            self.results = {
                'symbol': self.symbol,
                'mse': mse,
                'rmse': rmse,
                'mae': mae,
                'mape': mape,
                'buy_hold_return': buy_hold_return,
                'arima_return': arima_total_return,
                'outperformance': arima_total_return - buy_hold_return,
                'win_rate': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'test_period_start': self.predictions_df.index[0],
                'test_period_end': self.predictions_df.index[-1],
                'test_points': len(self.predictions_df),
                'train_window': self.train_window,
                'order': str(self.order)
            }
            
            print(f"\nResults for {self.symbol}:")
            print(f"RMSE: {rmse:.2f}")
            print(f"MAE: {mae:.2f}")
            print(f"MAPE: {mape:.2f}%")
            print(f"Buy & Hold Return: {buy_hold_return:.2f}%")
            print(f"ARIMA Strategy Return: {arima_total_return:.2f}%")
            print(f"Outperformance: {self.results['outperformance']:.2f}%")
            print(f"Win Rate: {win_rate:.1f}%")
            print(f"Avg Win: {avg_win:.4f}")
            print(f"Avg Loss: {avg_loss:.4f}")
            
            return True
            
        except Exception as e:
            print(f"Error calculating metrics for {self.symbol}: {str(e)}")
            return False
    
    def plot_results(self):
        """Plot actual vs predicted prices with trading signals"""
        if self.predictions_df is None:
            print("No predictions available for plotting.")
            return
            
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
        
        # Plot 1: Price predictions
        ax1.plot(self.train_data.index, self.train_data['price'], 
                label='Training Data', color='blue', alpha=0.7)
        ax1.plot(self.predictions_df.index, self.predictions_df['actual_price'], 
                label='Actual Price', color='green', linewidth=2)
        ax1.plot(self.predictions_df.index, self.predictions_df['predicted_price'], 
                label='ARIMA Predictions', color='red', linestyle='--', linewidth=2)
        
        ax1.set_title(f'Rolling ARIMA({self.order}) Backtest Results for {self.symbol}')
        ax1.set_ylabel('Price')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Trading signals
        buy_signals = self.predictions_df[self.predictions_df['signal'] == 1]
        sell_signals = self.predictions_df[self.predictions_df['signal'] == -1]
        
        ax2.plot(self.predictions_df.index, self.predictions_df['actual_price'], 
                color='black', alpha=0.7, label='Actual Price')
        ax2.scatter(buy_signals.index, buy_signals['actual_price'], 
                   color='green', marker='^', s=50, label='Buy Signal', alpha=0.8)
        ax2.scatter(sell_signals.index, sell_signals['actual_price'], 
                   color='red', marker='v', s=50, label='Sell Signal', alpha=0.8)
        
        ax2.set_title('Trading Signals')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Price')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    
    def run_backtest(self, train_window=100, order=(2, 1, 2)):
        """Run complete backtest pipeline with rolling window ARIMA"""
        print(f"\n{'='*60}")
        print(f"Starting Rolling ARIMA Backtest for {self.symbol}")
        print(f"Train window: {train_window}, Order: {order}")
        print(f"{'='*60}")
        
        # Step 1: Download data
        if not self.download_data():
            return None
        
        # Step 2: Split data
        if not self.split_data():
            return None
        
        # Step 3: Configure rolling ARIMA model
        if not self.fit_arima_model(order=order, train_window=train_window):
            return None
        
        # Step 4: Make predictions using rolling window
        if not self.make_predictions():
            return None
        
        # Step 5: Calculate metrics
        if not self.calculate_metrics():
            return None
        
        # Step 6: Plot results
        # self.plot_results()
        
        return self.results


def run_nifty50_arima_backtest(train_window=100, order=(2, 1, 2)):
    """Run rolling ARIMA backtest on all Nifty 50 stocks"""
    print("Rolling ARIMA Backtesting System for Nifty 50 Stocks")
    print(f"Train window: {train_window}, Order: {order}")
    print("=" * 60)
    
    # Get Nifty 5 symbols
    nifty50_symbols = fetch_nifty5_list()
    print(f"Found {len(nifty50_symbols)} Nifty 5 symbols")
    
    # Store all results
    all_results = []
    successful_backtests = 0
    
    for i, symbol in enumerate(nifty50_symbols, 1):
        print(f"\nProgress: {i}/{len(nifty50_symbols)}")
        
        try:
            # Create backtester instance
            backtester = ARIMABacktester(symbol)
            
            # Run backtest with rolling window
            results = backtester.run_backtest(train_window=train_window, order=order)
            
            if results is not None:
                all_results.append(results)
                successful_backtests += 1
                
        except Exception as e:
            print(f"Error in backtest for {symbol}: {str(e)}")
            continue
    
    # Create summary DataFrame
    if all_results:
        results_df = pd.DataFrame(all_results)
        
        print(f"\n{'='*60}")
        print(f"ROLLING ARIMA BACKTEST SUMMARY")
        print(f"{'='*60}")
        print(f"Train window: {train_window}, Order: {order}")
        print(f"Successful backtests: {successful_backtests}/{len(nifty50_symbols)}")
        print(f"Success rate: {successful_backtests/len(nifty50_symbols)*100:.1f}%")
        
        # Summary statistics
        print(f"\nPerformance Summary:")
        print(f"Average Buy & Hold Return: {results_df['buy_hold_return'].mean():.2f}%")
        print(f"Average ARIMA Strategy Return: {results_df['arima_return'].mean():.2f}%")
        print(f"Average Outperformance: {results_df['outperformance'].mean():.2f}%")
        print(f"Average Win Rate: {results_df['win_rate'].mean():.1f}%")
        print(f"Average RMSE: {results_df['rmse'].mean():.2f}")
        print(f"Average MAPE: {results_df['mape'].mean():.2f}%")
        
        # Top performers
        print(f"\nTop 5 ARIMA Performers:")
        top_performers = results_df.nlargest(5, 'arima_return')
        for _, row in top_performers.iterrows():
            print(f"{row['symbol']}: {row['arima_return']:.2f}% (Win Rate: {row['win_rate']:.1f}%)")
        
        # Worst performers
        print(f"\nBottom 5 ARIMA Performers:")
        bottom_performers = results_df.nsmallest(5, 'arima_return')
        for _, row in bottom_performers.iterrows():
            print(f"{row['symbol']}: {row['arima_return']:.2f}% (Win Rate: {row['win_rate']:.1f}%)")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"rolling_arima_backtest_results_{timestamp}.csv"
        results_df.to_csv(filename, index=False)
        print(f"\nResults saved to: {filename}")
        
        return results_df
    
    else:
        print("No successful backtests completed.")
        return None


if __name__ == "__main__":
    # Run the complete backtest
    results = run_nifty50_arima_backtest() 