# Rolling ARIMA Backtesting System for Nifty Stocks

## Overview

This system performs comprehensive rolling window ARIMA backtesting on Nifty stocks, comparing the performance against a buy-and-hold strategy. The system downloads 10 years of weekly data, uses a rolling window approach for realistic trading simulation, and provides detailed performance analysis with trading signals.

## Features

- **Data Management**: Downloads 10 years of weekly data for Nifty stocks
- **Rolling Window Approach**: Realistic walk-forward analysis with no data leakage
- **ARIMA Modeling**: Configurable ARIMA orders with rolling window retraining
- **Trading Signals**: Clear buy/sell signals based on price predictions
- **Performance Metrics**: RMSE, MAE, MAPE, win rate, and return calculations
- **Strategy Comparison**: Compares ARIMA strategy returns with buy-and-hold
- **Enhanced Visualization**: Dual plots showing predictions and trading signals
- **Batch Processing**: Processes multiple stocks automatically
- **Results Export**: Saves comprehensive results to CSV

## Key Improvements

### Rolling Window Approach
- **No Data Leakage**: Each prediction uses only past data available at that time
- **Realistic Simulation**: Models retrain with new data, simulating live trading
- **Walk-Forward Analysis**: More accurate representation of actual trading conditions

### Enhanced Metrics
- **Win Rate**: Percentage of profitable trades
- **Average Win/Loss**: Average returns for winning and losing trades
- **Trading Signals**: Explicit buy/sell signals for strategy evaluation

### Better Visualization
- **Dual Plot System**: Shows both price predictions and trading signals
- **Signal Visualization**: Green triangles for buy signals, red triangles for sell signals

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Required packages:
- `yfinance`: For downloading stock data
- `pandas`: For data manipulation
- `numpy`: For numerical computations
- `matplotlib`: For plotting results
- `statsmodels`: For ARIMA modeling
- `scikit-learn`: For performance metrics

## Usage

### 1. Test Single Stock

To test the system on a single stock first:

```python
from backtests.ARIMABacktester import ARIMABacktester

# Create backtester for a specific stock
backtester = ARIMABacktester("RELIANCE.NS")

# Run complete backtest with rolling window
results = backtester.run_backtest(train_window=100, order=(2, 1, 2))
```

### 2. Run Full Nifty Backtest

To run the complete backtest on Nifty stocks:

```bash
python backtests/ARIMABacktester.py
```

This will:
- Process all stocks sequentially
- Show progress for each stock
- Generate summary statistics
- Save results to CSV file

### 3. Custom Parameters

You can customize the rolling window and ARIMA parameters:

```python
# Run with custom parameters
results = run_nifty50_arima_backtest(train_window=150, order=(1, 1, 1))
```

## System Architecture

### ARIMABacktester Class

The main class with the following methods:

1. **`download_data()`**: Downloads 10 years of weekly data
2. **`split_data()`**: Splits data into 70:30 train/test ratio
3. **`fit_arima_model()`**: Configures rolling window ARIMA parameters
4. **`make_predictions()`**: Generates predictions using rolling window approach
5. **`calculate_metrics()`**: Computes comprehensive performance metrics
6. **`plot_results()`**: Creates dual visualization plots
7. **`run_backtest()`**: Executes complete backtest pipeline
8. **`create_rolling_arima_strategy()`**: Standalone rolling ARIMA strategy function

### Performance Metrics

The system calculates:

- **RMSE**: Root Mean Square Error
- **MAE**: Mean Absolute Error  
- **MAPE**: Mean Absolute Percentage Error
- **Buy & Hold Return**: Simple buy-and-hold strategy return
- **ARIMA Strategy Return**: Returns from ARIMA-based trading signals
- **Outperformance**: Difference between ARIMA and buy-and-hold returns
- **Win Rate**: Percentage of profitable trades
- **Average Win/Loss**: Average returns for winning and losing trades

### Trading Strategy

The rolling ARIMA strategy works as follows:
1. Use a rolling window of historical data (default: 100 observations)
2. Fit ARIMA model on the current window
3. Make one-step ahead prediction
4. Generate buy signal if predicted price > current price, sell signal otherwise
5. Move window forward and repeat
6. Calculate returns based on these signals
7. Compare with buy-and-hold strategy

## Current Results

Based on recent testing with Nifty stocks:

### Performance Summary
- **Average Buy & Hold Return**: 61.43%
- **Average ARIMA Strategy Return**: -1.94%
- **Average Outperformance**: -63.37%
- **Average Win Rate**: 49.1%
- **Average RMSE**: 70.86
- **Average MAPE**: 2.76%

### Top Performers
1. **EICHERMOT.NS**: 63.04% (Win Rate: 53.2%)
2. **HDFCBANK.NS**: 49.81% (Win Rate: 55.8%)
3. **INDIGO.NS**: 49.31% (Win Rate: 53.6%)
4. **BRITANNIA.NS**: 27.20% (Win Rate: 50.0%)
5. **TITAN.NS**: 23.09% (Win Rate: 48.1%)

### Key Insights
- ARIMA struggles in strongly trending markets
- Win rates around 50% suggest the model captures some price movements
- Mean reversion bias limits performance in bullish markets
- Transaction costs and risk management not included in current calculations

## Output Files

### CSV Results File

The system generates a timestamped CSV file with columns:
- `symbol`: Stock symbol
- `mse`, `rmse`, `mae`, `mape`: Error metrics
- `buy_hold_return`: Buy-and-hold strategy return
- `arima_return`: ARIMA strategy return
- `outperformance`: Performance difference
- `win_rate`: Percentage of profitable trades
- `avg_win`, `avg_loss`: Average returns for wins and losses
- `test_period_start/end`: Test period dates
- `test_points`: Number of test data points
- `train_window`: Rolling window size used
- `order`: ARIMA order parameters

### Console Output

The system provides:
- Progress updates for each stock
- Individual stock results with enhanced metrics
- Summary statistics including win rates
- Top and bottom performers with win rates
- Success rate information

## Example Output

```
Rolling ARIMA Backtesting System for Nifty Stocks
============================================================
Train window: 100, Order: (2, 1, 2)
Found 12 Nifty symbols

Progress: 1/12
============================================================
Starting Rolling ARIMA Backtest for ASIANPAINT.NS
Train window: 100, Order: (2, 1, 2)
============================================================
Downloading weekly data for ASIANPAINT.NS...
Downloaded 522 weekly data points for ASIANPAINT.NS
Train data: 365 points (70.0%)
Test data: 157 points (30.0%)
Fitting rolling ARIMA(2, 1, 2) model for ASIANPAINT.NS with train_window=100...
Rolling window ARIMA model configured successfully
Generating predictions using rolling window approach...
Generated 157 predictions using rolling window

Results for ASIANPAINT.NS:
RMSE: 85.70
MAE: 66.04
MAPE: 2.31%
Buy & Hold Return: -19.38%
ARIMA Strategy Return: -19.06%
Outperformance: 0.32%
Win Rate: 49.4%
Avg Win: 0.0209
Avg Loss: -0.0228

============================================================
ROLLING ARIMA BACKTEST SUMMARY
============================================================
Train window: 100, Order: (2, 1, 2)
Successful backtests: 12/12
Success rate: 100.0%

Performance Summary:
Average Buy & Hold Return: 61.43%
Average ARIMA Strategy Return: -1.94%
Average Outperformance: -63.37%
Average Win Rate: 49.1%
Average RMSE: 70.86
Average MAPE: 2.76%
```

## Limitations and Considerations

1. **Market Conditions**: ARIMA performs poorly in strongly trending markets
2. **Model Assumptions**: Linear relationships may not capture market complexity
3. **Transaction Costs**: Real trading includes fees and slippage (not included)
4. **Risk Management**: No position sizing or stop-loss mechanisms
5. **Parameter Sensitivity**: Fixed ARIMA parameters may not be optimal for all stocks
6. **Data Frequency**: Weekly data may be too coarse for effective signals

## Future Enhancements

Potential improvements to address current limitations:

### Model Improvements
- **Parameter Optimization**: Auto-optimize ARIMA orders for each stock
- **Multiple Models**: Combine ARIMA with other time series models
- **Ensemble Methods**: Use multiple ARIMA configurations
- **Daily Data**: Use higher frequency data for better signals

### Strategy Enhancements
- **Transaction Costs**: Include realistic trading costs
- **Position Sizing**: Implement confidence-based position sizing
- **Risk Management**: Add stop-loss and take-profit mechanisms
- **Trend Filters**: Avoid trading against strong market trends

### Performance Analysis
- **Risk-Adjusted Metrics**: Sharpe ratio, Sortino ratio, maximum drawdown
- **Portfolio Analysis**: Multi-stock portfolio optimization
- **Regime Detection**: Identify market conditions for strategy adaptation
- **Machine Learning**: Compare with ML-based approaches

## Troubleshooting

### Common Issues

1. **Insufficient Data**: Some stocks may have limited historical data
2. **Model Convergence**: ARIMA may fail to converge for some stocks
3. **Memory Issues**: Processing multiple stocks requires significant memory
4. **Network Issues**: Data download depends on internet connectivity

### Solutions

- Check internet connection for data downloads
- Ensure sufficient disk space for results
- Monitor system memory during batch processing
- Use single stock testing for debugging
- Adjust train window size for problematic stocks

## License

This project is for educational and research purposes. Please ensure compliance with data usage terms and trading regulations. 