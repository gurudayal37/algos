import yfinance as yf
import pandas as pd
from datetime import timedelta

def download_data(ticker, interval='1mo', period='7y'):
    data = yf.download(ticker, period=period, interval=interval , progress=False)
    data.columns = [col[0].replace(r'/.+$', '') if isinstance(col, tuple) else col for col in data.columns]
    return data

def get_piotroski_score(ticker):
    try:
        stock = yf.Ticker(ticker)

        # Get fundamental financials
        bs = stock.balance_sheet
        is_ = stock.financials
        cf = stock.cashflow

        if bs.empty or is_.empty or cf.empty:
            print(f"{ticker}: Missing financial data")
            return None

        # Convert columns to datetime for easy year comparison
        years = list(is_.columns)
        if len(years) < 2:
            print(f"{ticker}: Not enough historical data for Piotroski score")
            return None

        # Use most recent and previous years
        current_year, prev_year = years[0], years[1]

        score = 0

        # Profitability
        net_income = is_.loc["Net Income", current_year]
        operating_cf = cf.loc["Operating Cash Flow", current_year]
        total_assets = bs.loc["Total Assets", current_year]
        prev_total_assets = bs.loc["Total Assets", prev_year]
        prev_net_income = is_.loc["Net Income", prev_year]
        prev_operating_cf = cf.loc["Operating Cash Flow", prev_year]

        if net_income > 0: score += 1
        if operating_cf > 0: score += 1
        if total_assets > 0 and net_income / total_assets > 0: score += 1
        if operating_cf > net_income: score += 1

        # Leverage, Liquidity, Source of Funds
        lt_debt = bs.loc["Long Term Debt", current_year] if "Long Term Debt" in bs.index else 0
        prev_lt_debt = bs.loc["Long Term Debt", prev_year] if "Long Term Debt" in bs.index else 0
        if prev_lt_debt > 0 and lt_debt < prev_lt_debt: score += 1

        curr_assets = bs.loc["Total Current Assets", current_year] if "Total Current Assets" in bs.index else 0
        curr_liab = bs.loc["Total Current Liabilities", current_year] if "Total Current Liabilities" in bs.index else 1  # avoid div by 0
        prev_assets = bs.loc["Total Current Assets", prev_year] if "Total Current Assets" in bs.index else 0
        prev_liab = bs.loc["Total Current Liabilities", prev_year] if "Total Current Liabilities" in bs.index else 1
        curr_ratio = curr_assets / curr_liab
        prev_ratio = prev_assets / prev_liab
        if curr_ratio > prev_ratio: score += 1

        shares_outstanding = bs.loc["Ordinary Shares Number", current_year] if "Ordinary Shares Number" in bs.index else 0
        prev_shares_outstanding = bs.loc["Ordinary Shares Number", prev_year] if "Ordinary Shares Number" in bs.index else 0
        if shares_outstanding <= prev_shares_outstanding: score += 1

        # Efficiency
        gross_margin = (is_.loc["Gross Profit", current_year] / is_.loc["Total Revenue", current_year])
        prev_gross_margin = (is_.loc["Gross Profit", prev_year] / is_.loc["Total Revenue", prev_year])
        if gross_margin > prev_gross_margin: score += 1

        asset_turnover = is_.loc["Total Revenue", current_year] / total_assets
        prev_asset_turnover = is_.loc["Total Revenue", prev_year] / prev_total_assets
        if asset_turnover > prev_asset_turnover: score += 1

        return score

    except Exception as e:
        print(f"Error calculating Piotroski Score for {ticker}: {e}")
        return None


def get_pead_score(ticker):
    try:
        stock = yf.Ticker(ticker)
        earnings = stock.earnings_dates

        if earnings is None or earnings.empty:
            print(f"{ticker} has no recent earnings data.")
            return None

        recent_earnings = earnings.iloc[0]
        surprise = recent_earnings.get("Surprise (%)")

        if surprise is None:
            return None

        # Get stock performance 5 days post earnings
        earnings_date = recent_earnings.name
        end_date = earnings_date + timedelta(days=5)
        price_data = yf.download(ticker, start=earnings_date.strftime('%Y-%m-%d'),
                                 end=end_date.strftime('%Y-%m-%d'), progress=False)

        if price_data.empty or 'Close' not in price_data:
            return None

        start_price = price_data['Close'].iloc[0]
        end_price = price_data['Close'].iloc[-1]
        return_pct = (end_price - start_price) / start_price * 100

        # Simple PEAD score: surprise % + 5-day return %
        pead_score = surprise + return_pct
        return round(pead_score, 2)

    except Exception as e:
        print(f"Error getting PEAD for {ticker}: {e}")
        return None
