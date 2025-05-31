from dhanhq import dhanhq
import pandas as pd

# Replace these with your actual credentials
client_id = "your_client_id"
access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzQ4NzE5OTUzLCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwNTY4MTQ5MyJ9.fleP-yNa08YkT6Eh-1V6aDQv9cZNSEIpfDWieCZo4CDiup0r56-ycdq7JFabiKwaiM8j2YdZGM2yFOK8-04lcQ"

dhan = dhanhq(client_id, access_token)

# Sample list of stock symbols
stocks = ["RELIANCE", "HDFCBANK", "INFY", "TCS", "ICICIBANK"]

def get_instrument_token(symbol, segment):
    instruments = dhan.get_instruments_list(exchangeSegment=segment)
    for inst in instruments:
        if inst["tradingSymbol"] == symbol:
            return inst["instrumentId"]
    return None

def get_spot_and_future_gap(symbol):
    try:
        # Get instrument ID for cash
        cash_token = get_instrument_token(symbol, "EQUITY")

        # Get latest spot price
        spot = dhan.get_ltp(exchangeSegment="EQUITY", instrumentId=cash_token)
        spot_price = float(spot["ltp"])

        # Find FUT instrument token for the same symbol
        fut_symbol = symbol + "-EQ"  # adjust if needed
        futures = dhan.get_instruments_list("FUTURE")
        fut_instruments = [f for f in futures if f["tradingSymbol"].startswith(symbol)]

        if not fut_instruments:
            return None

        # Get nearest expiry future
        nearest_future = sorted(fut_instruments, key=lambda x: x["expiryDate"])[0]
        fut_price_data = dhan.get_ltp("FUTURE", nearest_future["instrumentId"])
        fut_price = float(fut_price_data["ltp"])

        gap = fut_price - spot_price

        return {
            "stock": symbol,
            "spot": spot_price,
            "future": fut_price,
            "gap": gap,
            "expiry": nearest_future["expiryDate"]
        }

    except Exception as e:
        print(f"Error for {symbol}: {e}")
        return None

# Run the strategy
results = []
for symbol in stocks:
    data = get_spot_and_future_gap(symbol)
    if data:
        results.append(data)

# Sort by price gap descending
sorted_results = sorted(results, key=lambda x: x["gap"], reverse=True)

# Print the output
print(f"{'Stock':<12}{'Spot':<10}{'Future':<10}{'Gap':<10}{'Expiry'}")
print("="*60)
for res in sorted_results:
    print(f"{res['stock']:<12}{res['spot']:<10.2f}{res['future']:<10.2f}{res['gap']:<10.2f}{res['expiry']}")
