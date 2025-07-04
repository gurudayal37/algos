# ## 5. $ARIMA$ models: The institutional approach

# $AR$ models are good, but investment professionals often use **$ARIMA$ models** because they handle three key problems:

# 1. **AutoRegressive ($AR$)**: Uses past returns (what we just did)
# 2. **Integrated ($I$)**: Handles non-stationary data automatically  
# 3. **Moving Average ($MA$)**: Uses past forecast errors to improve predictions

# **Why this matters for trading:**
# - **$AR$ part**: Captures momentum and mean reversion
# - **$I$ part**: Adapts when market trends change
# - **$MA$ part**: Learns from prediction mistakes

# Let's upgrade our strategy to $ARIMA$ and see if it performs better.

import sys
import os
import warnings
from statsmodels.tools.sm_exceptions import ConvergenceWarning

# Suppress warnings to clean up output
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=ConvergenceWarning)
warnings.filterwarnings('ignore', message='No frequency information was provided')
warnings.filterwarnings('ignore', message='Series.__getitem__ treating keys as positions is deprecated')
warnings.filterwarnings('ignore', message='Maximum Likelihood optimization failed to converge')
warnings.filterwarnings('ignore', message='Non-stationary starting autoregressive parameters found')
warnings.filterwarnings('ignore', message='Non-invertible starting MA parameters found')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from statsmodels.tsa.stattools import adfuller
import yfinance as yf
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.tsa.arima.model import ARIMA
import pandas as pd
import numpy as np
import time
from utils.helper import download_data

# Create rolling forecasts
def create_ar_strategy(data, train_window=100):
    """
    Build a trading strategy using rolling AR(1) forecasts
    """
    results = []
    
    for i in range(train_window, len(data)):
        # Use past 'train_window' observations to fit model
        if i % 100 == 0:
            print(f"Processed {i}/{len(data)}")
        train_series = data.iloc[i-train_window:i]
        
        # Fit AR(1) model (ARIMA with order=(1, 0, 0))
        init_model = ARIMA(train_series, order=(1, 0, 0))
        fitted_model = init_model.fit()
        
        # Make one-step-ahead forecast
        forecast = fitted_model.forecast(steps=1)[0]
        
        # Store result
        results.append({
            'date': data.index[i],
            'actual_returns': data.iloc[i],
            'predicted_returns': forecast,
            'signal': 1 if forecast > 0 else -1
        })
    
    return pd.DataFrame(results).set_index('date')


def create_arima_strategy(price_data, train_window=100, order=(2, 1, 2)):
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


order = (2, 1, 2)
firm_name = 'PYPL'

df_weekly = download_data(firm_name, interval='1wk', period='7y')
print(f"Building ARIMA{order} strategy on {firm_name} stock weekly prices...")
print("This will take a while. We're fitting 400+ models...\n")

# Start timing
start_time = time.time()

# Run the rolling ARIMA strategy on crude oil adjusted close prices
arima_strategy = create_arima_strategy(df_weekly['Close'], order=order)

# Calculate elapsed time
elapsed_time = time.time() - start_time
minutes = int(elapsed_time / 60)
seconds = elapsed_time % 60

print(f"\n✅ Strategy built! Generated {len(arima_strategy)} trading signals")
print(f"⏱️ Time taken: {minutes}m {seconds:.1f}s")
print(f"Period: {arima_strategy.index[0].date()} to {arima_strategy.index[-1].date()}")

# Show a sample of predictions
print("\nSample predictions:")
print("=" * 60)
print(arima_strategy[['actual_price', 'predicted_price', 'signal']].head(10).round(2))

print(f"\n✅ ARIMA strategy complete!")


# Compute ARIMA strategy returns
arima_strategy['predicted_change'] = arima_strategy['predicted_price'] - arima_strategy['predicted_price'].shift(1)
arima_strategy['actual_change'] = arima_strategy['actual_price'] - arima_strategy['actual_price'].shift(1)

# Generate signals based on predicted change
arima_strategy['signal'] = arima_strategy['predicted_change'].apply(lambda x: 1 if x > 0 else -1)

# Compute actual return (price change as % of previous price)
arima_strategy['actual_returns'] = arima_strategy['actual_price'].pct_change()

# Strategy return = signal × actual return
arima_strategy['strategy_returns'] = arima_strategy['signal'].shift(1) * arima_strategy['actual_returns']

def compare_strategies(arima_results):
    """
    Compare multiple strategies on weekly data
    """
    arima_results = arima_results.dropna(subset=['strategy_returns', 'actual_returns'])
    # ARIMA strategy
    arima_total = (1 + arima_results['strategy_returns']).cumprod().iloc[-1] - 1
    arima_sharpe = arima_results['strategy_returns'].mean() / arima_results['strategy_returns'].std() * np.sqrt(52)
    
    # Buy and hold
    buyhold_total = (1 + arima_results['actual_returns']).cumprod().iloc[-1] - 1
    buyhold_sharpe = arima_results['actual_returns'].mean() / arima_results['actual_returns'].std() * np.sqrt(52)
    
    # Simple momentum: long if last return > 0
    momentum_signals = (arima_results['actual_returns'].shift(1) > 0).astype(int) * 2 - 1
    momentum_returns = momentum_signals * arima_results['actual_returns']
    momentum_total = (1 + momentum_returns).cumprod().iloc[-1] - 1
    momentum_sharpe = momentum_returns.mean() / momentum_returns.std() * np.sqrt(52)
    
    print(f"Strategy comparison - {firm_name} weekly")
    print("=" * 60)
    print(f"ARIMA(2,1,2):     {arima_total:7.2%} returns, {arima_sharpe:5.2f} Sharpe")
    print(f"Simple momentum:  {momentum_total:7.2%} returns, {momentum_sharpe:5.2f} Sharpe") 
    print(f"Buy & hold:       {buyhold_total:7.2%} returns, {buyhold_sharpe:5.2f} Sharpe")
    
    print(f"\nARIMA vs buy & hold: {arima_total - buyhold_total:+.2%} excess returns")
    print(f"ARIMA vs momentum: {arima_total - momentum_total:+.2%} excess returns")
    
    return {
        'arima': {'returns': arima_total, 'sharpe': arima_sharpe},
        'momentum': {'returns': momentum_total, 'sharpe': momentum_sharpe},
        'buyhold': {'returns': buyhold_total, 'sharpe': buyhold_sharpe}
    }

# Compare strategies
comparison = compare_strategies(arima_strategy)