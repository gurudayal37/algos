import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.helper import download_data
from data.Index import nifty_next_500_symbols
import pandas as pd

def test_symbols():
    """Test all symbols in update to see which ones can be downloaded"""
    working_symbols = []
    failed_symbols = []
    
    print(f"Testing {len(nifty_next_500_symbols)} symbols...")
    
    for i, symbol in enumerate(nifty_next_500_symbols, 1):
        try:
            print(f"Testing {i}/{len(nifty_next_500_symbols)}: {symbol}")
            data = download_data(symbol, interval='1mo', period='1y')
            
            # Check if we got meaningful data
            if data is not None and len(data) > 0 and not data.empty:
                working_symbols.append(symbol)
                print(f"✓ {symbol} - SUCCESS")
            else:
                failed_symbols.append(symbol)
                print(f"✗ {symbol} - NO DATA")
                
        except Exception as e:
            failed_symbols.append(symbol)
            print(f"✗ {symbol} - ERROR: {str(e)}")
    
    print(f"\n=== RESULTS ===")
    print(f"Working symbols: {len(working_symbols)}")
    print(f"Failed symbols: {len(failed_symbols)}")
    
    if failed_symbols:
        print(f"\nFailed symbols:")
        for symbol in failed_symbols:
            print(f"  '{symbol}',")
    
    return working_symbols, failed_symbols

if __name__ == "__main__":
    working, failed = test_symbols() 