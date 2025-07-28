#!/usr/bin/env python3
"""
Working Screener.in Quarterly Results Scraper
This scraper properly parses the actual page structure and extracts company data
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import re
from typing import List, Dict, Tuple, Optional
import logging
import json
from urllib.parse import urljoin, urlparse
import random
import sys
import os

# Try to import local config
try:
    from config_local import *
    print("✅ Loaded local configuration with credentials")
except ImportError:
    print("❌ No configuration file found. Please create config_local.py with your credentials")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WorkingScreenerScraper:
    """
    Working web scraper for Screener.in quarterly results
    """
    
    def __init__(self):
        self.base_url = "https://www.screener.in"
        self.login_url = "https://www.screener.in/login/"
        self.results_url = "https://www.screener.in/results/latest/"
        self.session = requests.Session()
        self.is_authenticated = False
        
        # Create output directory if it doesn't exist
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
        
        # Set up headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def login(self) -> bool:
        """Login to Screener.in"""
        try:
            logger.info("Attempting to login to Screener.in...")
            
            # Get login page
            response = self.session.get(self.login_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract CSRF token
            csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
            if not csrf_input:
                logger.error("Could not find CSRF token")
                return False
            
            csrf_token = csrf_input.get('value')
            
            # Prepare login data
            login_data = {
                'csrfmiddlewaretoken': csrf_token,
                'username': SCREENER_EMAIL,  # Use 'username' field
                'password': SCREENER_PASSWORD,
                'next': '/results/latest/'
            }
            
            # Add headers
            self.session.headers.update({
                'Referer': self.login_url,
                'Content-Type': 'application/x-www-form-urlencoded',
            })
            
            # Perform login
            login_response = self.session.post(self.login_url, data=login_data, timeout=15, allow_redirects=True)
            
            # Check if login was successful
            if 'login' not in login_response.url.lower():
                logger.info("Login successful!")
                self.is_authenticated = True
                return True
            else:
                logger.error("Login failed - still on login page")
                return False
                
        except Exception as e:
            logger.error(f"Error during login: {e}")
            return False
    
    def scrape_page(self, url: str) -> List[Dict]:
        """Scrape a single page for company results"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            companies = []
            
            # Extract date from URL
            date_match = re.search(r'result_update_date__day=(\d+)&result_update_date__month=(\d+)&result_update_date__year=(\d+)', url)
            result_date = ""
            if date_match:
                result_date = f"{date_match.group(3)}-{date_match.group(2)}-{date_match.group(1)}"
            
            # Save HTML for debugging if enabled
            if DEBUG_MODE:
                debug_file = os.path.join(OUTPUT_DIR, f"debug_working_page_{result_date}.html")
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(str(soup))
            
            # Find all company sections
            # Look for all company sections directly
            company_sections = soup.find_all('div', class_='flex-row flex-space-between flex-align-center margin-top-32 margin-bottom-16 margin-left-4 margin-right-4')
            logger.info(f"Found {len(company_sections)} company sections")
            
            # Filter out sections that don't have company links
            valid_sections = []
            for section in company_sections:
                name_link = section.find('a', class_='font-weight-500')
                if name_link and name_link.get('href', '').startswith('/company/'):
                    valid_sections.append(section)
            
            company_sections = valid_sections
            logger.info(f"Found {len(company_sections)} valid company sections")
            
            for section in company_sections:
                company_data = self._extract_company_data(section, result_date)
                if company_data and company_data['name']:
                    companies.append(company_data)
            
            logger.info(f"Found {len(companies)} companies on {url}")
            return companies
            
        except Exception as e:
            logger.error(f"Error parsing {url}: {e}")
            return []
    
    def _extract_company_data(self, section, result_date: str) -> Dict:
        """Extract company data from a section"""
        company_data = self._get_empty_company_data()
        company_data['result_date'] = result_date
        
        try:
            # Extract company name and link
            name_link = section.find('a', class_='font-weight-500')
            if name_link:
                company_data['name'] = name_link.get_text(strip=True)
                company_data['url'] = self.base_url + name_link.get('href', '')
            
            # Extract price and market cap info
            price_info = section.find('div', class_='font-size-14')
            if price_info:
                self._extract_price_info(price_info, company_data)
            
            # Extract financial metrics from table
            # The table is in the next sibling div after the company section
            table_container = section.find_next_sibling('div', class_='bg-base border-radius-8 padding-small responsive-holder')
            if table_container:
                table = table_container.find('table', class_='data-table')
                if table:
                    self._extract_financial_metrics_from_table(table, company_data)
            
        except Exception as e:
            logger.warning(f"Error extracting company data: {e}")
        
        return company_data
    
    def _extract_price_info(self, price_element, company_data: Dict):
        """Extract price and market cap information"""
        try:
            text = price_element.get_text()
            
            # Extract price
            price_match = re.search(r'Price ₹\s*([\d,]+\.?\d*)', text)
            if price_match:
                company_data['price'] = self._parse_number(price_match.group(1))
            
            # Extract market cap
            mcap_match = re.search(r'M\.Cap ₹\s*([\d,]+\.?\d*)\s*Cr', text)
            if mcap_match:
                company_data['market_cap'] = self._parse_number(mcap_match.group(1)) * 10000000
            
            # Extract PE ratio
            pe_match = re.search(r'PE\s+([\d.]+)', text)
            if pe_match:
                company_data['pe_ratio'] = float(pe_match.group(1))
                
        except Exception as e:
            logger.warning(f"Error extracting price info: {e}")
    
    def _extract_financial_metrics_from_table(self, table, company_data: Dict):
        """Extract financial metrics from table"""
        try:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 4:
                    # Get metric name (first column)
                    metric_name = cells[0].get_text(strip=True).lower()
                    
                    # Get YOY growth (second column)
                    yoy_cell = cells[1]
                    yoy_growth = self._parse_percentage_from_cell(yoy_cell)
                    
                    # Get current quarter value (third column)
                    current_value = cells[2].get_text(strip=True)
                    current_num = self._parse_number(current_value)
                    
                    # Map metrics to company data
                    if 'sales' in metric_name:
                        company_data['sales'] = current_num
                        company_data['sales_growth'] = yoy_growth
                    elif 'ebidt' in metric_name:
                        company_data['ebidt'] = current_num
                        company_data['ebidt_growth'] = yoy_growth
                    elif 'net profit' in metric_name:
                        company_data['net_profit'] = current_num
                        company_data['net_profit_growth'] = yoy_growth
                    elif 'eps' in metric_name:
                        company_data['eps'] = current_num
                        company_data['eps_growth'] = yoy_growth
                        
        except Exception as e:
            logger.warning(f"Error extracting from table: {e}")
    
    def _parse_percentage_from_cell(self, cell) -> float:
        """Parse percentage from a table cell"""
        try:
            # Look for change spans
            change_span = cell.find('span', class_='change')
            if change_span:
                text = change_span.get_text(strip=True)
                return self._parse_percentage(text)
            
            # Fallback to cell text
            text = cell.get_text(strip=True)
            return self._parse_percentage(text)
            
        except Exception as e:
            logger.warning(f"Error parsing percentage from cell: {e}")
            return 0.0
    
    def _get_empty_company_data(self) -> Dict:
        """Get empty company data structure"""
        return {
            'name': '',
            'url': '',
            'price': 0,
            'market_cap': 0,
            'pe_ratio': 0,
            'sales': 0,
            'sales_growth': 0,
            'ebidt': 0,
            'ebidt_growth': 0,
            'net_profit': 0,
            'net_profit_growth': 0,
            'eps': 0,
            'eps_growth': 0,
            'result_date': '',
        }
    
    def _parse_number(self, text: str) -> float:
        """Parse number from text"""
        if not text or text.strip() == '':
            return 0.0
        
        text = text.strip().replace(',', '')
        
        # Handle negative numbers
        is_negative = text.startswith('-')
        if is_negative:
            text = text[1:]
        
        numeric_match = re.search(r'[\d.]+', text)
        if numeric_match:
            result = float(numeric_match.group())
            return -result if is_negative else result
        
        return 0.0
    
    def _parse_percentage(self, text: str) -> float:
        """Parse percentage from text"""
        if not text or text.strip() == '':
            return 0.0
        
        text = text.strip()
        
        # Handle arrow indicators
        if '↑' in text:
            sign = 1
            text = text.replace('↑', '')
        elif '↓' in text:
            sign = -1
            text = text.replace('↓', '')
        else:
            sign = 1
        
        # Remove % and extract number
        text = text.replace('%', '')
        
        # Handle negative signs
        if text.startswith('-'):
            sign = -1
            text = text[1:]
        
        numeric_match = re.search(r'[\d.]+', text)
        if numeric_match:
            return float(numeric_match.group()) * sign
        
        return 0.0
    
    def scrape_current_results(self) -> pd.DataFrame:
        """Scrape current quarterly results"""
        if not self.login():
            logger.error("Failed to login. Cannot proceed with scraping.")
            return pd.DataFrame()
        
        try:
            # Scrape the main results page
            companies = self.scrape_page(self.results_url)
            
            # Convert to DataFrame
            df = pd.DataFrame(companies)
            
            # Clean and filter data
            if not df.empty:
                # Remove rows with no company name
                df = df[df['name'].str.len() > 0]
                
                # Add scrape date
                df['scrape_date'] = datetime.now().strftime('%Y-%m-%d')
                
                # Remove duplicates
                df = df.drop_duplicates(subset=['name'])
            
            return df
            
        except Exception as e:
            logger.error(f"Error scraping current results: {e}")
            return pd.DataFrame()
    
    def analyze_results(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Analyze results and find top 5 best and worst performing companies"""
        if df.empty:
            logger.warning("No data to analyze")
            return pd.DataFrame(), pd.DataFrame()
        
        # Create composite score
        df['composite_score'] = (
            df['sales_growth'].fillna(0) * COMPOSITE_SCORE_WEIGHTS['sales_growth'] + 
            df['ebidt_growth'].fillna(0) * COMPOSITE_SCORE_WEIGHTS['ebidt_growth'] + 
            df['net_profit_growth'].fillna(0) * COMPOSITE_SCORE_WEIGHTS['net_profit_growth'] + 
            df['eps_growth'].fillna(0) * COMPOSITE_SCORE_WEIGHTS['eps_growth']
        )
        
        # Filter companies with meaningful data
        df_filtered = df[df['composite_score'] != 0].copy()
        
        if df_filtered.empty:
            logger.warning("No companies with growth data found")
            return pd.DataFrame(), pd.DataFrame()
        
        # Sort by composite score
        df_sorted = df_filtered.sort_values('composite_score', ascending=False)
        
        # Get top 5 best and worst
        top_5_best = df_sorted.head(5)
        top_5_worst = df_sorted.tail(5)
        
        return top_5_best, top_5_worst
    
    def print_analysis(self, top_5_best: pd.DataFrame, top_5_worst: pd.DataFrame):
        """Print analysis results"""
        print("\n" + "="*100)
        print("QUARTERLY RESULTS ANALYSIS")
        print("="*100)
        
        if not top_5_best.empty:
            print(f"\n🏆 TOP 5 COMPANIES WITH GREAT RESULTS ({len(top_5_best)} companies):")
            print("-" * 70)
            for idx, row in top_5_best.iterrows():
                print(f"{row['name']}")
                print(f"  Sales Growth: {row['sales_growth']:+.1f}% | "
                      f"EBIDT Growth: {row['ebidt_growth']:+.1f}% | "
                      f"Net Profit Growth: {row['net_profit_growth']:+.1f}% | "
                      f"EPS Growth: {row['eps_growth']:+.1f}%")
                print(f"  Composite Score: {row['composite_score']:.2f}")
                if row['price'] > 0:
                    print(f"  Price: ₹{row['price']:.2f} | Market Cap: ₹{row['market_cap']/10000000:.1f} Cr")
                print()
        
        if not top_5_worst.empty:
            print(f"\n📉 TOP 5 COMPANIES WITH POOR RESULTS ({len(top_5_worst)} companies):")
            print("-" * 70)
            for idx, row in top_5_worst.iterrows():
                print(f"{row['name']}")
                print(f"  Sales Growth: {row['sales_growth']:+.1f}% | "
                      f"EBIDT Growth: {row['ebidt_growth']:+.1f}% | "
                      f"Net Profit Growth: {row['net_profit_growth']:+.1f}% | "
                      f"EPS Growth: {row['eps_growth']:+.1f}%")
                print(f"  Composite Score: {row['composite_score']:.2f}")
                if row['price'] > 0:
                    print(f"  Price: ₹{row['price']:.2f} | Market Cap: ₹{row['market_cap']/10000000:.1f} Cr")
                print()
        
        print("="*100)


def main():
    """Main function to run the working scraper"""
    print("🔍 Working Screener.in Quarterly Results Scraper")
    print("=" * 60)
    print("This scraper extracts current quarterly financial results")
    print("and analyzes top 5 best/worst performing companies.")
    print("=" * 60)
    
    # Check if credentials are properly configured
    if SCREENER_EMAIL == "your_email@example.com":
        print("\n⚠️  Please configure your credentials in config_local.py")
        return
    
    # Initialize scraper
    scraper = WorkingScreenerScraper()
    
    print(f"\n👤 Using credentials for: {SCREENER_EMAIL}")
    
    try:
        # Scrape the current results
        print("\n⏳ Scraping current quarterly results...")
        df = scraper.scrape_current_results()
        
        if df.empty:
            print("\n❌ No data found. This might be due to:")
            print("   1. No quarterly results available")
            print("   2. Website structure has changed")
            print("   3. Authentication failed")
            return
        
        print(f"\n✅ Successfully scraped data for {len(df)} companies")
        
        # Show data summary
        print(f"\n📊 Data Summary:")
        print(f"   Total Companies: {len(df)}")
        print(f"   Companies with Sales Data: {len(df[df['sales'] > 0])}")
        print(f"   Companies with EBIDT Data: {len(df[df['ebidt'] != 0])}")
        print(f"   Companies with Net Profit Data: {len(df[df['net_profit'] != 0])}")
        print(f"   Companies with EPS Data: {len(df[df['eps'] != 0])}")
        print(f"   Companies with Growth Data: {len(df[df['sales_growth'] != 0])}")
        
        # Analyze results
        print("\n📈 Analyzing results...")
        top_5_best, top_5_worst = scraper.analyze_results(df)
        
        # Print analysis
        scraper.print_analysis(top_5_best, top_5_worst)
        
        # Save to CSV
        output_file = os.path.join(OUTPUT_DIR, f"working_screener_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        df.to_csv(output_file, index=False)
        print(f"\n💾 Data saved to: {output_file}")
        
        # Show sample of raw data
        if not df.empty:
            print(f"\n📋 Sample of scraped data:")
            print(df.head(3).to_string(index=False))
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Scraping interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        print("Please check your internet connection and try again.")


if __name__ == "__main__":
    main() 