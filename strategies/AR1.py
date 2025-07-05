# The simplest autoregressive model looks like this:

# returns_today = 
#  + 
#  × returns_yesterday + noise

# Where:

# α (alpha) = the average return when there's no momentum
# β (beta) = how much yesterday's return affects today's return
# noise = the unpredictable part
# Different values of 

#  > 0: Momentum (positive returns tend to follow positive returns)
#  < 0: Mean reversion (positive returns tend to be followed by negative returns)
#  = 0: Random walk (yesterday tells us nothing about today)
from statsmodels.tsa.stattools import adfuller
import yfinance as yf
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.tsa.arima.model import ARIMA
import pandas as pd
import time
from utils.helper import download_data


def check_stationarity_quick(the_series, name):
    
    result = adfuller(the_series.dropna())
    
    print(f"Stationarity test performed on {name}:")
    print("=" * 50)
    print(f"ADF statistic: {result[0]:.4f}")
    print(f"p-value: {result[1]:.5f}")
    print(f"Critical values:")
    for key, value in result[4].items():
        print(f"\t{key}: {value:.3f}")
    
    if result[1] <= 0.05:
        print("✅ STATIONARY: Good for modeling!")
    else:
        print("❌ NON-STATIONARY: Need to transform the data.")
    print()

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


ticker = 'RELIANCE.NS'
data = download_data(ticker,interval='1wk',period='10y')
data['weekly_return'] = data['Close'].pct_change()  
check_stationarity_quick(data['Close'], ticker)
check_stationarity_quick(data['weekly_return'], ticker)

# fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
# sm.graphics.tsa.plot_acf(data['weekly_return'].dropna(), lags=15, ax=ax1)
# sm.graphics.tsa.plot_pacf(data['weekly_return'].dropna(), lags=15, ax=ax2)
# ax1.set_title(f"ACF of the {ticker} stock weekly returns")
# ax2.set_title(f"PACF of the {ticker} stock weekly returns")
# plt.tight_layout()
# plt.show()

train_end = '2023-12-31'
train_data = data[data.index <= train_end]['weekly_return']
test_data = data[data.index > train_end]['weekly_return']

print(f"Training: {len(train_data)} weeks; testing: {len(test_data)} weeks")


