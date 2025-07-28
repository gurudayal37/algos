import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import requests
from bs4 import BeautifulSoup
import time

from data.Index import  fetch_nifty5_list
from data.Sectors import sector_mapping
from utils.helper import get_piotroski_score


class PEADStrategy:
    def __init__(self):
        self.today = datetime.now()
        self.two_days_ago = self.today - timedelta(days=2)
        self.seven_days_ago = self.today - timedelta(days=7)
        self.thirty_days_ago = self.today - timedelta(days=30)
        self.ninety_days_ago = self.today - timedelta(days=90)
        
        # Manual override for known earnings dates (when Yahoo Finance data is delayed)
        self.manual_earnings = {
        }
        
    def get_screener_data(self, ticker: str) -> Optional[Dict]:
        """
        Fetch latest quarterly data from Screener.in
        """
        try:
            # Map ticker symbols to Screener.in format
            screener_mapping = {
                "RELIANCE.NS": "RELIANCE",
                "TCS.NS": "TCS",
                "INFY.NS": "INFY",
                "HDFCBANK.NS": "HDFCBANK",
                "ICICIBANK.NS": "ICICIBANK",
                "HINDUNILVR.NS": "HINDUNILVR",
                "ITC.NS": "ITC",
                "SBIN.NS": "SBIN",
                "BHARTIARTL.NS": "BHARTIARTL",
                "KOTAKBANK.NS": "KOTAKBANK"
            }
            
            screener_symbol = screener_mapping.get(ticker)
            if not screener_symbol:
                return None
            
            url = f"https://www.screener.in/company/{screener_symbol}/consolidated/"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract quarterly data from the page
            # This is a simplified approach - you might need to adjust based on actual HTML structure
            quarterly_data = {}
            
            # Look for recent quarterly results in the page content
            content = soup.get_text()
            
            # Extract key metrics (this is a basic approach)
            if "Jun 2025" in content or "Q1 FY26" in content:
                quarterly_data["latest_quarter"] = "Q1 FY26"
                quarterly_data["source"] = "Screener.in"
                
                # For now, return the manual data we have
                if ticker in self.manual_earnings:
                    return self.manual_earnings[ticker]
            
            return None
            
        except Exception as e:
            print(f"Error fetching Screener.in data for {ticker}: {e}")
            return None
    
    def get_moneycontrol_data(self, ticker: str) -> Optional[Dict]:
        """
        Fetch latest quarterly data from MoneyControl
        """
        try:
            # Map ticker symbols to MoneyControl format
            mc_mapping = {
                "RELIANCE.NS": "reliance-industries",
                "TCS.NS": "tcs",
                "INFY.NS": "infosys",
                "HDFCBANK.NS": "hdfc-bank",
                "ICICIBANK.NS": "icici-bank"
            }
            
            mc_symbol = mc_mapping.get(ticker)
            if not mc_symbol:
                return None
            
            url = f"https://www.moneycontrol.com/india/stockpricequote/{mc_symbol}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return None
            
            # Parse the page for quarterly results
            # This would need to be implemented based on MoneyControl's structure
            return None
            
        except Exception as e:
            print(f"Error fetching MoneyControl data for {ticker}: {e}")
            return None
    
    def get_earnings_announcements(self, ticker: str) -> Optional[pd.DataFrame]:
        """
        Get earnings announcements for the last 90 days (very flexible)
        """
        try:
            stock = yf.Ticker(ticker)
            earnings = stock.earnings_dates
            
            if earnings is None or earnings.empty:
                return None
            
            # Convert timezone-aware dates to timezone-naive for comparison
            if earnings.index.tz is not None:
                earnings.index = earnings.index.tz_localize(None)
                
            # Filter for announcements in the last 90 days (very flexible)
            ninety_days_ago = self.today - timedelta(days=90)
            recent_earnings = earnings[
                (earnings.index >= ninety_days_ago) & 
                (earnings.index <= self.today)
            ]
            
            # If still no earnings, get the most recent one regardless of date
            if recent_earnings.empty and not earnings.empty:
                recent_earnings = earnings.head(1)
                print(f"Using most recent earnings for {ticker}: {recent_earnings.index[0].strftime('%Y-%m-%d')}")
            
            return recent_earnings if not recent_earnings.empty else None
            
        except Exception as e:
            print(f"Error getting earnings for {ticker}: {e}")
            return None
    
    def get_manual_earnings(self, ticker: str) -> Optional[Dict]:
        """
        Get manual earnings data if available
        """
        if ticker in self.manual_earnings:
            manual_data = self.manual_earnings[ticker]
            # Check if the manual earnings date is recent (within last 30 days)
            if (self.today - manual_data["date"]).days <= 30:
                print(f"Using manual earnings data for {ticker}: {manual_data['date'].strftime('%Y-%m-%d')}")
                return manual_data
        return None
    
    def get_alternative_earnings_data(self, ticker: str) -> Optional[Dict]:
        """
        Try multiple sources to get the most up-to-date earnings data
        """
        # Priority order: Manual data > Screener.in > MoneyControl > Yahoo Finance
        
        # 1. Check manual data first
        manual_data = self.get_manual_earnings(ticker)
        if manual_data:
            return manual_data
        
        # 2. Try Screener.in
        screener_data = self.get_screener_data(ticker)
        if screener_data:
            return screener_data
        
        # 3. Try MoneyControl
        mc_data = self.get_moneycontrol_data(ticker)
        if mc_data:
            return mc_data
        
        # 4. Fall back to Yahoo Finance
        return None
    
    def get_analyst_expectations(self, ticker: str) -> Optional[Dict]:
        """
        Get analyst expectations for EPS
        """
        try:
            stock = yf.Ticker(ticker)
            
            # Try different methods to get earnings estimates
            earnings_estimates = None
            
            # Method 1: Try earnings_forecast
            try:
                earnings_estimates = stock.earnings_forecast
            except AttributeError:
                pass
            
            # Method 2: Try earnings_dates which might have estimates
            if earnings_estimates is None or earnings_estimates.empty:
                try:
                    earnings_dates = stock.earnings_dates
                    if earnings_dates is not None and not earnings_dates.empty:
                        # Check if earnings_dates has estimate columns
                        if 'EPS Estimate' in earnings_dates.columns:
                            earnings_estimates = earnings_dates
                except Exception:
                    pass
            
            if earnings_estimates is None or earnings_estimates.empty:
                return None
                
            # Get the most recent estimate
            latest_estimate = earnings_estimates.iloc[0] if not earnings_estimates.empty else None
            
            if latest_estimate is not None:
                return {
                    'eps_estimate': latest_estimate.get('EPS Estimate', None),
                    'revenue_estimate': latest_estimate.get('Revenue Average', None),
                    'estimate_date': latest_estimate.name
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting analyst expectations for {ticker}: {e}")
            return None
    
    def get_historical_eps_average(self, ticker: str) -> Optional[float]:
        """
        Calculate average EPS of last 4 quarters
        """
        try:
            stock = yf.Ticker(ticker)
            earnings = stock.earnings
            
            if earnings is None or earnings.empty or len(earnings) < 4:
                return None
                
            # Get last 4 quarters EPS
            last_4_quarters = earnings.head(4)
            avg_eps = last_4_quarters['Earnings'].mean()
            
            return avg_eps
            
        except Exception as e:
            print(f"Error getting historical EPS for {ticker}: {e}")
            return None
    
    def get_financial_metrics(self, ticker: str) -> Optional[Dict]:
        """
        Get YoY changes in Sales, EBITDA, Net Profit
        """
        try:
            stock = yf.Ticker(ticker)
            
            # Get financial statements
            income_stmt = stock.financials
            balance_sheet = stock.balance_sheet
            
            if income_stmt is None or income_stmt.empty:
                return None
                
            # Get last 2 years of data
            if len(income_stmt.columns) < 2:
                return None
                
            current_year = income_stmt.columns[0]
            previous_year = income_stmt.columns[1]
            
            metrics = {}
            
            # Sales/Revenue YoY change
            if 'Total Revenue' in income_stmt.index:
                current_revenue = income_stmt.loc['Total Revenue', current_year]
                previous_revenue = income_stmt.loc['Total Revenue', previous_year]
                if previous_revenue != 0:
                    metrics['revenue_yoy'] = ((current_revenue - previous_revenue) / abs(previous_revenue)) * 100
                else:
                    metrics['revenue_yoy'] = None
            
            # EBITDA YoY change (if available)
            if 'EBITDA' in income_stmt.index:
                current_ebitda = income_stmt.loc['EBITDA', current_year]
                previous_ebitda = income_stmt.loc['EBITDA', previous_year]
                if previous_ebitda != 0:
                    metrics['ebitda_yoy'] = ((current_ebitda - previous_ebitda) / abs(previous_ebitda)) * 100
                else:
                    metrics['ebitda_yoy'] = None
            
            # Net Income YoY change
            if 'Net Income' in income_stmt.index:
                current_net_income = income_stmt.loc['Net Income', current_year]
                previous_net_income = income_stmt.loc['Net Income', previous_year]
                if previous_net_income != 0:
                    metrics['net_income_yoy'] = ((current_net_income - previous_net_income) / abs(previous_net_income)) * 100
                else:
                    metrics['net_income_yoy'] = None
            
            # Operating Income YoY change
            if 'Operating Income' in income_stmt.index:
                current_op_income = income_stmt.loc['Operating Income', current_year]
                previous_op_income = income_stmt.loc['Operating Income', previous_year]
                if previous_op_income != 0:
                    metrics['operating_income_yoy'] = ((current_op_income - previous_op_income) / abs(previous_op_income)) * 100
                else:
                    metrics['operating_income_yoy'] = None
            
            return metrics
            
        except Exception as e:
            print(f"Error getting financial metrics for {ticker}: {e}")
            return None
    
    def analyze_earnings_surprise(self, ticker: str, actual_eps: float, expected_eps: float = None) -> Dict:
        """
        Analyze earnings surprise and provide recommendation
        """
        result = {
            'ticker': ticker,
            'actual_eps': actual_eps,
            'expected_eps': expected_eps,
            'surprise_pct': None,
            'recommendation': 'HOLD',
            'confidence': 'LOW',
            'reasoning': []
        }
        
        if expected_eps is not None:
            # Compare with analyst expectations
            surprise_pct = ((actual_eps - expected_eps) / abs(expected_eps)) * 100
            result['surprise_pct'] = surprise_pct
            
            if surprise_pct > 5:
                result['recommendation'] = 'BUY'
                result['confidence'] = 'HIGH'
                result['reasoning'].append(f"EPS beat expectations by {surprise_pct:.2f}%")
            elif surprise_pct > 0:
                result['recommendation'] = 'BUY'
                result['confidence'] = 'MEDIUM'
                result['reasoning'].append(f"EPS beat expectations by {surprise_pct:.2f}%")
            elif surprise_pct < -5:
                result['recommendation'] = 'SELL'
                result['confidence'] = 'HIGH'
                result['reasoning'].append(f"EPS missed expectations by {abs(surprise_pct):.2f}%")
            elif surprise_pct < 0:
                result['recommendation'] = 'SELL'
                result['confidence'] = 'MEDIUM'
                result['reasoning'].append(f"EPS missed expectations by {abs(surprise_pct):.2f}%")
            else:
                result['recommendation'] = 'HOLD'
                result['reasoning'].append("EPS met expectations")
        else:
            # Compare with historical average
            historical_avg = self.get_historical_eps_average(ticker)
            if historical_avg is not None:
                surprise_pct = ((actual_eps - historical_avg) / abs(historical_avg)) * 100
                result['surprise_pct'] = surprise_pct
                result['expected_eps'] = historical_avg
                
                if surprise_pct > 10:
                    result['recommendation'] = 'BUY'
                    result['confidence'] = 'HIGH'
                    result['reasoning'].append(f"EPS beat 4-quarter average by {surprise_pct:.2f}%")
                elif surprise_pct > 0:
                    result['recommendation'] = 'BUY'
                    result['confidence'] = 'MEDIUM'
                    result['reasoning'].append(f"EPS beat 4-quarter average by {surprise_pct:.2f}%")
                elif surprise_pct < -10:
                    result['recommendation'] = 'SELL'
                    result['confidence'] = 'HIGH'
                    result['reasoning'].append(f"EPS below 4-quarter average by {abs(surprise_pct):.2f}%")
                elif surprise_pct < 0:
                    result['recommendation'] = 'SELL'
                    result['confidence'] = 'MEDIUM'
                    result['reasoning'].append(f"EPS below 4-quarter average by {abs(surprise_pct):.2f}%")
                else:
                    result['recommendation'] = 'HOLD'
                    result['reasoning'].append("EPS in line with 4-quarter average")
            else:
                result['reasoning'].append("No historical EPS data available")
        
        return result
    
    def get_additional_news_indicators(self, ticker: str) -> List[str]:
        """
        Get additional positive/negative news indicators
        """
        indicators = []
        
        try:
            stock = yf.Ticker(ticker)
            
            # Check for dividend increases
            dividends = stock.dividends
            if dividends is not None and not dividends.empty:
                recent_dividends = dividends.tail(4)
                if len(recent_dividends) >= 2:
                    if recent_dividends.iloc[-1] > recent_dividends.iloc[-2]:
                        indicators.append("Dividend increased")
            
            # Check for share buybacks (if available in balance sheet)
            balance_sheet = stock.balance_sheet
            if balance_sheet is not None and not balance_sheet.empty:
                if 'Treasury Stock' in balance_sheet.index:
                    current_treasury = balance_sheet.loc['Treasury Stock', balance_sheet.columns[0]]
                    prev_treasury = balance_sheet.loc['Treasury Stock', balance_sheet.columns[1]]
                    if current_treasury < prev_treasury:
                        indicators.append("Share buyback activity")
            
            # Check Piotroski score
            piotroski_score = get_piotroski_score(ticker)
            if piotroski_score is not None:
                if piotroski_score >= 7:
                    indicators.append(f"Strong Piotroski score: {piotroski_score}/9")
                elif piotroski_score <= 3:
                    indicators.append(f"Weak Piotroski score: {piotroski_score}/9")
            
        except Exception as e:
            print(f"Error getting additional indicators for {ticker}: {e}")
        
        return indicators
    
    def analyze_stock(self, ticker: str) -> Optional[Dict]:
        """
        Complete analysis of a stock for PEAD strategy
        """
        try:
            # First try alternative data sources for up-to-date information
            alternative_data = self.get_alternative_earnings_data(ticker)
            if alternative_data:
                # Use alternative data source
                analysis = self.analyze_earnings_surprise(ticker, alternative_data["eps"], alternative_data.get("expected_eps"))
                analysis['earnings_date'] = alternative_data["date"]
                analysis['sector'] = sector_mapping.get(ticker, "Unknown")
                analysis['data_source'] = alternative_data.get("source", "Manual")
                
                # Add financial metrics from alternative source
                if 'revenue_yoy' in alternative_data:
                    analysis['financial_metrics'] = {
                        'revenue_yoy': alternative_data.get('revenue_yoy'),
                        'ebitda_yoy': alternative_data.get('ebitda_yoy'),
                        'net_income_yoy': alternative_data.get('net_income_yoy')
                    }
                    
                    # Add reasoning for financial metrics
                    if alternative_data.get('revenue_yoy', 0) > 10:
                        analysis['reasoning'].append(f"Strong revenue growth: {alternative_data['revenue_yoy']:.1f}% YoY")
                    if alternative_data.get('net_income_yoy', 0) > 20:
                        analysis['reasoning'].append(f"Strong net income growth: {alternative_data['net_income_yoy']:.1f}% YoY")
                
                # Add reasoning for alternative data source
                if alternative_data["eps"] > alternative_data.get("expected_eps", 0):
                    analysis['reasoning'].append(f"EPS beat expectations (Source: {alternative_data.get('source', 'Manual')})")
                else:
                    analysis['reasoning'].append(f"EPS missed expectations (Source: {alternative_data.get('source', 'Manual')})")
                
                return analysis
            
            # Fall back to Yahoo Finance data
            earnings = self.get_earnings_announcements(ticker)
            if earnings is None or earnings.empty:
                return None
            
            # Get the most recent earnings
            latest_earnings = earnings.iloc[0]
            
            # Try different column names for EPS
            actual_eps = None
            if 'Reported EPS' in latest_earnings.index:
                actual_eps = latest_earnings['Reported EPS']
            elif 'Earnings' in latest_earnings.index:
                actual_eps = latest_earnings['Earnings']
            
            # Debug: Print earnings info (only for specific stocks)
            if ticker in ["RELIANCE.NS", "TCS.NS", "INFY.NS"]:
                print(f"Found earnings for {ticker}: {latest_earnings.name.strftime('%Y-%m-%d')} - EPS: {actual_eps}")
            
            if actual_eps is None:
                return None
            
            # Get analyst expectations
            expectations = self.get_analyst_expectations(ticker)
            expected_eps = expectations['eps_estimate'] if expectations else None
            
            # Analyze earnings surprise
            analysis = self.analyze_earnings_surprise(ticker, actual_eps, expected_eps)
            
            # Get financial metrics
            financial_metrics = self.get_financial_metrics(ticker)
            if financial_metrics:
                analysis['financial_metrics'] = financial_metrics
                
                # Add financial metrics to reasoning
                for metric, value in financial_metrics.items():
                    if value is not None:
                        if 'revenue' in metric and value > 10:
                            analysis['reasoning'].append(f"Strong revenue growth: {value:.1f}% YoY")
                        elif 'ebitda' in metric and value > 15:
                            analysis['reasoning'].append(f"Strong EBITDA growth: {value:.1f}% YoY")
                        elif 'net_income' in metric and value > 20:
                            analysis['reasoning'].append(f"Strong net income growth: {value:.1f}% YoY")
            
            # Get additional news indicators
            additional_indicators = self.get_additional_news_indicators(ticker)
            if additional_indicators:
                analysis['additional_indicators'] = additional_indicators
                analysis['reasoning'].extend(additional_indicators)
            
            # Add earnings date
            analysis['earnings_date'] = latest_earnings.name
            analysis['sector'] = sector_mapping.get(ticker, "Unknown")
            analysis['data_source'] = "Yahoo Finance"
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")
            return None
    
    def run_strategy(self) -> List[Dict]:
        """
        Run the complete PEAD strategy
        """
        print("Running PEAD Strategy with Multiple Data Sources...")
        print(f"Looking for earnings announcements from {self.ninety_days_ago.strftime('%Y-%m-%d')} to {self.today.strftime('%Y-%m-%d')}")
        print(f"Data sources: Manual > Screener.in > MoneyControl > Yahoo Finance")
        print("=" * 80)
        
        # Get list of stocks to analyze
        tickers = fetch_nifty5_list()
        
        results = []
        buy_recommendations = []
        sell_recommendations = []
        
        for ticker in tickers:
            try:
                analysis = self.analyze_stock(ticker)
                if analysis:
                    results.append(analysis)
                    
                    if analysis['recommendation'] == 'BUY':
                        buy_recommendations.append(analysis)
                    elif analysis['recommendation'] == 'SELL':
                        sell_recommendations.append(analysis)
                        
            except Exception as e:
                print(f"Error processing {ticker}: {e}")
        
        # Print results
        self.print_results(results, buy_recommendations, sell_recommendations)
        
        return results
    
    def print_results(self, all_results: List[Dict], buy_recs: List[Dict], sell_recs: List[Dict]):
        """
        Print formatted results
        """
        print(f"\n📊 PEAD Strategy Results Summary")
        print(f"Total stocks with recent earnings: {len(all_results)}")
        print(f"Buy recommendations: {len(buy_recs)}")
        print(f"Sell recommendations: {len(sell_recs)}")
        
        if buy_recs:
            print(f"\n🟢 BUY RECOMMENDATIONS:")
            print("-" * 80)
            for rec in buy_recs:
                self.print_recommendation(rec, "BUY")
        
        if sell_recs:
            print(f"\n🔴 SELL RECOMMENDATIONS:")
            print("-" * 80)
            for rec in sell_recs:
                self.print_recommendation(rec, "SELL")
        
        if not buy_recs and not sell_recs:
            print("\n📋 All stocks analyzed:")
            for rec in all_results:
                self.print_recommendation(rec, rec['recommendation'])
    
    def print_recommendation(self, rec: Dict, action: str):
        """
        Print individual recommendation
        """
        color = "🟢" if action == "BUY" else "🔴" if action == "SELL" else "🟡"
        
        print(f"{color} {rec['ticker']} ({rec['sector']}) - {action} [{rec['confidence']}]")
        print(f"   Earnings Date: {rec['earnings_date'].strftime('%Y-%m-%d')}")
        print(f"   Data Source: {rec.get('data_source', 'Unknown')}")
        print(f"   Actual EPS: {rec['actual_eps']:.2f}")
        
        if rec['expected_eps'] is not None:
            print(f"   Expected EPS: {rec['expected_eps']:.2f}")
        
        if rec['surprise_pct'] is not None:
            surprise_icon = "📈" if rec['surprise_pct'] > 0 else "📉"
            print(f"   Surprise: {surprise_icon} {rec['surprise_pct']:.2f}%")
        
        if 'financial_metrics' in rec:
            metrics = rec['financial_metrics']
            print(f"   Financial Metrics:")
            for metric, value in metrics.items():
                if value is not None:
                    metric_name = metric.replace('_yoy', '').replace('_', ' ').title()
                    print(f"     {metric_name}: {value:.1f}% YoY")
        
        if rec['reasoning']:
            print(f"   Reasoning: {'; '.join(rec['reasoning'])}")
        
        print()


def main():
    """
    Main function to run the PEAD strategy
    """
    strategy = PEADStrategy()
    results = strategy.run_strategy()
    
    # Save results to CSV
    if results:
        df = pd.DataFrame(results)
        filename = f"pead_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        print(f"\n💾 Results saved to {filename}")


if __name__ == "__main__":
    main()