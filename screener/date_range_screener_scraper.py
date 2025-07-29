#!/usr/bin/env python3
"""
Date Range Screener.in Quarterly Results Scraper
This scraper can scrape specific date ranges and analyze results
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
import ast

# Add utils folder to path for Piotroski score
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))
try:
    from helper import get_piotroski_score
    print("✅ Loaded Piotroski score function from utils/helper.py")
except ImportError:
    print("⚠️  Warning: Could not import Piotroski score function from utils/helper.py")
    get_piotroski_score = None

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

class DateRangeScreenerScraper:
    """
    Date range web scraper for Screener.in quarterly results
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
                debug_file = os.path.join(OUTPUT_DIR, f"debug_date_range_page_{result_date}.html")
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(str(soup))
            
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
                    logger.debug(f"Processing {company_data['name']} - Market Cap: ₹{company_data['market_cap']/10000000:.1f} Cr")
                    # Filter out companies with market cap less than 1000 Cr
                    if company_data['market_cap'] >= 100000000000:  # 1000 Cr = 100,000,000,000
                        # Try to get announcement time from NSE
                        if company_data['announcement_time'] == '':
                            nse_time = self.get_announcement_time_from_nse(company_data['name'])
                            if nse_time:
                                company_data['announcement_time'] = nse_time
                                logger.debug(f"📅 Found NSE announcement time for {company_data['name']}: {nse_time}")
                        
                        # Get Piotroski score
                        piotroski_score = self.get_piotroski_score_for_company(company_data['name'])
                        if piotroski_score is not None:
                            company_data['piotroski_score'] = piotroski_score
                            logger.debug(f"📊 Found Piotroski score for {company_data['name']}: {piotroski_score}/9")
                        
                        # Get shareholding pattern
                        company_symbol = self._get_company_symbol(company_data['name'])
                        if company_symbol:
                            shareholding_pattern = self.get_shareholding_pattern(company_symbol)
                            if shareholding_pattern:
                                company_data['shareholding_pattern'] = shareholding_pattern
                                logger.debug(f"📈 Found shareholding pattern for {company_data['name']}")
                        
                        companies.append(company_data)
                        logger.debug(f"✅ Included {company_data['name']} - Market Cap: ₹{company_data['market_cap']/10000000:.1f} Cr")
                    else:
                        logger.debug(f"❌ Filtered out {company_data['name']} - Market Cap: ₹{company_data['market_cap']/10000000:.1f} Cr")
            
            logger.info(f"Found {len(companies)} companies (after market cap filter) on {url}")
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
            
            # Extract PDF link if available
            pdf_link = section.find('a', class_='plausible-event-name=Latest+Results+PDF')
            if pdf_link:
                company_data['pdf_url'] = self.base_url + pdf_link.get('href', '')
            
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
            logger.debug(f"Price info text: {text}")
            
            # Extract price
            price_match = re.search(r'Price ₹\s*([\d,]+\.?\d*)', text)
            if price_match:
                company_data['price'] = self._parse_number(price_match.group(1))
                logger.debug(f"Extracted price: {company_data['price']}")
            
            # Extract market cap - handle multi-line format
            # Look for "M.Cap" followed by "₹" and numbers, then "Cr"
            mcap_match = re.search(r'M\.Cap\s*\n\s*₹\s*([\d,]+\.?\d*)\s*\n\s*Cr', text, re.MULTILINE | re.DOTALL)
            if mcap_match:
                mcap_value = self._parse_number(mcap_match.group(1))
                company_data['market_cap'] = mcap_value * 10000000  # Convert Cr to actual value
                logger.debug(f"Extracted market cap: {mcap_value} Cr = {company_data['market_cap']}")
            else:
                # Try alternative pattern for single-line format
                mcap_match = re.search(r'M\.Cap ₹\s*([\d,]+\.?\d*)\s*Cr', text)
                if mcap_match:
                    mcap_value = self._parse_number(mcap_match.group(1))
                    company_data['market_cap'] = mcap_value * 10000000  # Convert Cr to actual value
                    logger.debug(f"Extracted market cap: {mcap_value} Cr = {company_data['market_cap']}")
                else:
                    logger.debug(f"No market cap found in text: {text}")
            
            # Extract PE ratio
            pe_match = re.search(r'PE\s+([\d.]+)', text)
            if pe_match:
                company_data['pe_ratio'] = float(pe_match.group(1))
                logger.debug(f"Extracted PE: {company_data['pe_ratio']}")
                
        except Exception as e:
            logger.warning(f"Error extracting price info: {e}")
            logger.debug(f"Problematic text: {text}")
    
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
            'announcement_time': '',  # Will store IST announcement time if available
            'pdf_url': '',  # PDF link for detailed results
            'piotroski_score': None,  # Piotroski F-Score (0-9)
            'shareholding_pattern': {},  # Shareholding pattern for last 5 quarters
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
        if '↑' in text or '⇡' in text:
            sign = 1
            text = text.replace('↑', '').replace('⇡', '')
        elif '↓' in text or '⇣' in text:
            sign = -1
            text = text.replace('↓', '').replace('⇣', '')
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
    
    def get_total_pages(self, url: str) -> int:
        """Get total number of pages for a given date"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for pagination controls - try multiple selectors
            pagination_selectors = [
                'div.pagination',
                'div[class*="pagination"]',
                'div[class*="page"]',
                'nav[class*="pagination"]'
            ]
            
            pagination = None
            for selector in pagination_selectors:
                pagination = soup.select_one(selector)
                if pagination:
                    break
            
            if pagination:
                # Find all page numbers
                page_links = pagination.find_all('a')
                if page_links:
                    # Get the last page number
                    page_numbers = []
                    for link in page_links:
                        text = link.get_text(strip=True)
                        if text.isdigit():
                            page_numbers.append(int(text))
                    
                    if page_numbers:
                        max_page = max(page_numbers)
                        logger.info(f"Found pagination with {max_page} pages")
                        return max_page
            
            # Look for text indicating total results and pages
            page_text = soup.get_text()
            
            # Look for patterns like "101 results" or "page 5 of 5"
            results_match = re.search(r'(\d+)\s+results', page_text)
            if results_match:
                total_results = int(results_match.group(1))
                # Assuming 25 results per page (based on your observation)
                estimated_pages = (total_results + 24) // 25  # Ceiling division
                logger.info(f"Found {total_results} results, estimating {estimated_pages} pages")
                return estimated_pages
            
            # If no pagination found, assume single page
            logger.info("No pagination found, assuming single page")
            return 1
            
        except Exception as e:
            logger.warning(f"Error getting total pages for {url}: {e}")
            return 1
    
    def get_announcement_time_from_nse(self, company_name: str) -> str:
        """Get announcement time from NSE website for a company"""
        try:
            # NSE URL format
            nse_base_url = "https://www.nseindia.com/get-quotes/equity"
            
            # Try to find the company symbol from Screener.in URL
            company_symbol = self._get_company_symbol(company_name)
            
            if not company_symbol:
                return ""
            
            # Construct NSE URL
            nse_url = f"{nse_base_url}?symbol={company_symbol}"
            
            # Set comprehensive headers for NSE (mimicking real browser)
            nse_headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://www.nseindia.com/',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"macOS"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0',
            }
            
            # First, visit the main NSE page to get cookies
            main_response = self.session.get('https://www.nseindia.com/', headers=nse_headers, timeout=15)
            main_response.raise_for_status()
            
            # Add a small delay
            import time
            time.sleep(2)
            
            # Try to get financial results via API first
            api_url = f"https://www.nseindia.com/api/quote-equity?symbol={company_symbol}"
            try:
                api_response = self.session.get(api_url, headers=nse_headers, timeout=15)
                if api_response.status_code == 200:
                    api_data = api_response.json()
                    # Look for announcement time in API response
                    if 'announcements' in api_data:
                        for announcement in api_data['announcements']:
                            if 'date' in announcement:
                                return announcement['date']
            except Exception as e:
                logger.debug(f"API call failed for {company_name}: {e}")
            
            # Fallback to scraping the page
            response = self.session.get(nse_url, headers=nse_headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for the BROADCAST DATE/TIME column in financial results table
            # The format is typically "DD-Mon-YYYY HH:MM"
            broadcast_time_pattern = r'\d{2}-[A-Za-z]{3}-\d{4}\s+\d{2}:\d{2}'
            
            # First, try to find the "Integrated Filing-Financials" table specifically
            # This is where the most recent announcement times are shown
            financial_tables = soup.find_all('table')
            for table in financial_tables:
                # Look for table headers that might indicate financial results
                headers = table.find_all('th')
                header_text = ' '.join([h.get_text(strip=True) for h in headers])
                
                # Check if this is the Integrated Filing-Financials table
                if 'BROADCAST' in header_text.upper() and ('INTEGRATED' in header_text.upper() or 'FILING' in header_text.upper()):
                    # This is the Integrated Filing-Financials table - get the most recent announcement
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        # Look for the first data row (skip header row)
                        if len(cells) > 0 and cells[0].name == 'td':  # This is a data row, not header
                            for cell in cells:
                                cell_text = cell.get_text(strip=True)
                                if re.search(broadcast_time_pattern, cell_text):
                                    time_match = re.search(broadcast_time_pattern, cell_text)
                                    if time_match:
                                        time_str = time_match.group()
                                        # Check if this looks like an announcement time (not page timestamp)
                                        if '15:30' not in time_str and '02:05' not in time_str:  # Avoid page timestamps
                                            return time_str
                            # Only process the first data row (most recent quarter)
                            break
                
                # Also check regular Financial Results table
                elif 'BROADCAST' in header_text.upper() or ('DATE' in header_text.upper() and 'TIME' in header_text.upper()):
                    # This looks like a financial results table
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        for cell in cells:
                            cell_text = cell.get_text(strip=True)
                            if re.search(broadcast_time_pattern, cell_text):
                                time_match = re.search(broadcast_time_pattern, cell_text)
                                if time_match:
                                    time_str = time_match.group()
                                    # Check if this looks like an announcement time (not page timestamp)
                                    if '15:30' not in time_str and '02:05' not in time_str:  # Avoid page timestamps
                                        return time_str
            
            # If not found in financial tables, search in all table cells
            table_cells = soup.find_all(['td', 'th'])
            for cell in table_cells:
                cell_text = cell.get_text(strip=True)
                if re.search(broadcast_time_pattern, cell_text):
                    time_match = re.search(broadcast_time_pattern, cell_text)
                    if time_match:
                        time_str = time_match.group()
                        # Check if this looks like an announcement time (not page timestamp)
                        if '15:30' not in time_str:  # Avoid page timestamp
                            return time_str
            
            # If not found in table cells, search in the entire page
            page_text = soup.get_text()
            time_matches = re.findall(broadcast_time_pattern, page_text)
            if time_matches:
                # Filter out page timestamps and return the most recent announcement time
                announcement_times = [t for t in time_matches if '15:30' not in t]
                if announcement_times:
                    return announcement_times[0]
            
            return ""
            
        except Exception as e:
            logger.debug(f"Error getting announcement time from NSE for {company_name}: {e}")
            return ""
    
    def _get_company_symbol(self, company_name: str) -> str:
        """Map company name to NSE symbol"""
        # This is a simplified mapping - in practice, you'd need a comprehensive database
        # or API to map company names to their NSE symbols
        symbol_mapping = {
            'NTPC': 'NTPC',
            'GMR Airports': 'GMRAIRPORT',
            'Star Health Insu': 'STARHEALTH',
            'Asian Paints': 'ASIANPAINT',
            'V-Guard Industri': 'VGUARD',
            'Jubilant Pharmo': 'JUBLPHARMA',
            'Blue Dart Expres': 'BLUEDART',
            'Allied Blenders': 'ABDL',
            'GE Vernova T&D': 'GVT&D',
            'International Ge': 'IGL',
            'Craftsman Auto': 'CRAFTSMAN',
            'Amber Enterp.': 'AMBER',
            'Lloyds Engineeri': 'LLOYDS',
            'New India Assura': 'NIACL',
            'Dilip Buildcon': 'DLF',
            'IFB Industries': 'IFBIND',
            'John Cockerill': 'JCOCKERILL',
            'Timex Group': 'TIMEX',
            'Electrotherm(I)': 'ELECTROTHERM',
            'Odyssey Tech.': 'ODYSSEY',
            'National Perox.': 'NATPEROX',
            'Quadrant Future': 'QUADRANT',
            'D.P. Abhushan': 'DPABHUSHAN',
        }
        
        # Try exact match first
        if company_name in symbol_mapping:
            return symbol_mapping[company_name]
        
        # Try partial matches
        for key, symbol in symbol_mapping.items():
            if key.lower() in company_name.lower() or company_name.lower() in key.lower():
                return symbol
        
        return ""
    
    def get_shareholding_pattern(self, company_symbol: str) -> Dict:
        """Get shareholding pattern for the last 5 quarters from Screener.in"""
        try:
            # Construct URL for shareholding pattern
            shareholding_url = f"{self.base_url}/company/{company_symbol}/consolidated/"
            
            response = self.session.get(shareholding_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for shareholding pattern table
            shareholding_data = {}
            
            # Find the shareholding pattern section
            shareholding_section = soup.find('h2', string=lambda text: text and 'Shareholding Pattern' in text)
            if shareholding_section:
                # Look for the table in the same section
                table = shareholding_section.find_next('table')
                if table:
                    rows = table.find_all('tr')
                    
                    # Extract quarters from header
                    header_row = rows[0] if rows else None
                    if header_row:
                        quarters = []
                        header_cells = header_row.find_all(['th', 'td'])
                        for cell in header_cells[1:]:  # Skip first cell (category)
                            quarter_text = cell.get_text(strip=True)
                            if quarter_text and any(char.isdigit() for char in quarter_text):
                                quarters.append(quarter_text)
                        
                        # Extract data rows
                        for row in rows[1:]:  # Skip header row
                            cells = row.find_all(['td', 'th'])
                            if len(cells) > 1:
                                category = cells[0].get_text(strip=True)
                                if category and any(keyword in category.lower() for keyword in ['promoter', 'fii', 'dii', 'public']):
                                    shareholding_data[category] = {}
                                    for i, cell in enumerate(cells[1:], 1):
                                        if i <= len(quarters):
                                            value = cell.get_text(strip=True)
                                            shareholding_data[category][quarters[i-1]] = value
            
            return shareholding_data
            
        except Exception as e:
            logger.debug(f"Error getting shareholding pattern for {company_symbol}: {e}")
            return {}
    
    def get_piotroski_score_for_company(self, company_name: str) -> Optional[int]:
        """Get Piotroski score for a company"""
        if get_piotroski_score is None:
            return None
        
        try:
            # Map company name to ticker symbol
            ticker_mapping = {
                'Allied Blenders': 'ABDL.NS',
                'GE Vernova T&D': 'GVT&D.NS',
                'NTPC': 'NTPC.NS',
                'Asian Paints': 'ASIANPAINT.NS',
                'Star Health Insu': 'STARHEALTH.NS',
                'V-Guard Industri': 'VGUARD.NS',
                'Jubilant Pharmo': 'JUBLPHARMA.NS',
                'Blue Dart Expres': 'BLUEDART.NS',
                'International Ge': 'IGL.NS',
                'Craftsman Auto': 'CRAFTSMAN.NS',
                'Amber Enterp.': 'AMBER.NS',
                'Lloyds Engineeri': 'LLOYDS.NS',
                'New India Assura': 'NIACL.NS',
                'Dilip Buildcon': 'DLF.NS',
                'IFB Industries': 'IFBIND.NS',
                'John Cockerill': 'JCOCKERILL.NS',
                'Timex Group': 'TIMEX.NS',
                'Electrotherm(I)': 'ELECTROTHERM.NS',
                'Odyssey Tech.': 'ODYSSEY.NS',
                'National Perox.': 'NATPEROX.NS',
                'Quadrant Future': 'QUADRANT.NS',
                'D.P. Abhushan': 'DPABHUSHAN.NS',
            }
            
            ticker = ticker_mapping.get(company_name)
            if ticker:
                return get_piotroski_score(ticker)
            
            return None
            
        except Exception as e:
            logger.debug(f"Error getting Piotroski score for {company_name}: {e}")
            return None
    
    def get_announcement_time_from_company_page(self, company_url: str) -> str:
        """Try to get announcement time from individual company page"""
        try:
            # Add quarters section to URL if not present
            if '#quarters' not in company_url:
                company_url = company_url + '#quarters'
            
            response = self.session.get(company_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for announcement time in various possible locations
            # This is speculative as Screener.in may not show exact announcement times
            time_selectors = [
                'span[data-announcement-time]',
                '.announcement-time',
                '.result-time',
                '.publish-time',
                '[class*="time"]',
                '[class*="announcement"]'
            ]
            
            for selector in time_selectors:
                time_element = soup.select_one(selector)
                if time_element:
                    time_text = time_element.get_text(strip=True)
                    if time_text and any(char.isdigit() for char in time_text):
                        return time_text
            
            # If no specific time found, return empty string
            return ""
            
        except Exception as e:
            logger.debug(f"Error getting announcement time from {company_url}: {e}")
            return ""
    
    def scrape_date_range(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Scrape a range of dates with pagination support"""
        if not self.login():
            logger.error("Failed to login. Cannot proceed with scraping.")
            return pd.DataFrame()
        
        try:
            # Generate date range
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
            all_companies = []
            current = start
            
            while current <= end:
                date_str = current.strftime('%Y-%m-%d')
                day = current.day
                month = current.month
                year = current.year
                
                # Create base URL for this date
                base_url = f"{self.results_url}?all=&result_update_date__day={day}&result_update_date__month={month}&result_update_date__year={year}"
                
                print(f"Scraping {date_str}: {base_url}")
                
                # Get total pages for this date
                total_pages = self.get_total_pages(base_url)
                print(f"  Total pages for {date_str}: {total_pages}")
                
                # Fallback: If detection shows only 1 page but we know there should be more
                # (based on the user's observation of 101 results), try pages 2-5
                if total_pages == 1:
                    logger.info("Pagination detection shows 1 page, but checking for additional pages...")
                    # Try to access page 2 to see if it exists
                    test_page2_url = f"{base_url}&p=2"
                    try:
                        test_response = self.session.get(test_page2_url, timeout=10)
                        if test_response.status_code == 200:
                            test_soup = BeautifulSoup(test_response.content, 'html.parser')
                            # Check if page 2 has company data (not login page)
                            test_companies = test_soup.find_all('div', class_='flex-row flex-space-between flex-align-center margin-top-32 margin-bottom-16 margin-left-4 margin-right-4')
                            if len(test_companies) > 0:
                                logger.info("Page 2 exists with company data, updating total pages to 5")
                                total_pages = 5
                                print(f"  Updated total pages for {date_str}: {total_pages}")
                    except Exception as e:
                        logger.warning(f"Error testing page 2: {e}")
                
                date_companies = []
                
                # Scrape all pages for this date
                for page in range(1, total_pages + 1):
                    page_url = f"{base_url}&p={page}"
                    print(f"    Scraping page {page}/{total_pages}: {page_url}")
                    
                    companies = self.scrape_page(page_url)
                    
                    if companies:
                        date_companies.extend(companies)
                        print(f"      Found {len(companies)} companies on page {page}")
                    else:
                        print(f"      No companies found on page {page}")
                    
                    # Small delay between pages
                    time.sleep(1)
                
                if date_companies:
                    all_companies.extend(date_companies)
                    print(f"  Total companies for {date_str}: {len(date_companies)}")
                else:
                    print(f"  No companies found for {date_str}")
                
                # Move to next date
                current += timedelta(days=1)
                
                # Small delay to be respectful
                time.sleep(2)
            
            # Convert to DataFrame
            df = pd.DataFrame(all_companies)
            
            # Clean and filter data
            if not df.empty:
                # Remove rows with no company name
                df = df[df['name'].str.len() > 0]
                
                # Add scrape date
                df['scrape_date'] = datetime.now().strftime('%Y-%m-%d')
                
                # Remove duplicates
                df = df.drop_duplicates(subset=['name', 'result_date'])
                
                # Final market cap filter (in case some slipped through)
                df = df[df['market_cap'] >= 100000000000]  # 1000 Cr minimum
                
                print(f"\n📊 Final filtering results:")
                print(f"   Companies with market cap >= 1000 Cr: {len(df)}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error scraping date range: {e}")
            return pd.DataFrame()
    
    def analyze_results(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Analyze results and find top 5 best and worst performing companies"""
        if df.empty:
            logger.warning("No data to analyze")
            return pd.DataFrame(), pd.DataFrame()
        
        # Filter companies with market cap >= 1000 Cr
        df_filtered = df[df['market_cap'] >= 100000000000].copy()
        
        if df_filtered.empty:
            logger.warning("No companies with market cap >= 1000 Cr found")
            return pd.DataFrame(), pd.DataFrame()
        
        # Create composite score
        df_filtered['composite_score'] = (
            df_filtered['sales_growth'].fillna(0) * COMPOSITE_SCORE_WEIGHTS['sales_growth'] + 
            df_filtered['ebidt_growth'].fillna(0) * COMPOSITE_SCORE_WEIGHTS['ebidt_growth'] + 
            df_filtered['net_profit_growth'].fillna(0) * COMPOSITE_SCORE_WEIGHTS['net_profit_growth'] + 
            df_filtered['eps_growth'].fillna(0) * COMPOSITE_SCORE_WEIGHTS['eps_growth']
        )
        
        # Filter companies with meaningful data
        df_with_growth = df_filtered[df_filtered['composite_score'] != 0].copy()
        
        if df_with_growth.empty:
            logger.warning("No companies with growth data found")
            return pd.DataFrame(), pd.DataFrame()
        
        # Sort by composite score
        df_sorted = df_with_growth.sort_values('composite_score', ascending=False)
        
        # Get top 5 best and worst
        top_5_best = df_sorted.head(5)
        top_5_worst = df_sorted.tail(5)
        
        return top_5_best, top_5_worst
    
    def print_analysis(self, top_5_best: pd.DataFrame, top_5_worst: pd.DataFrame):
        """Print analysis results"""
        print("\n" + "="*100)
        print("QUARTERLY RESULTS ANALYSIS (Market Cap >= 1000 Cr)")
        print("="*100)
        print("📝 Note: Announcement times are fetched from NSE website (IST)")
        print("   Format: DD-Mon-YYYY HH:MM")
        print("   📄 PDF links contain detailed announcement information")
        print("="*100)
        
        if not top_5_best.empty:
            print(f"\n🏆 TOP 5 COMPANIES WITH GREAT RESULTS ({len(top_5_best)} companies):")
            print("-" * 70)
            for idx, row in top_5_best.iterrows():
                print(f"{row['name']} ({row['result_date']})")
                print(f"  Sales Growth: {row['sales_growth']:+.1f}% | "
                      f"EBIDT Growth: {row['ebidt_growth']:+.1f}% | "
                      f"Net Profit Growth: {row['net_profit_growth']:+.1f}% | "
                      f"EPS Growth: {row['eps_growth']:+.1f}%")
                print(f"  Composite Score: {row['composite_score']:.2f}")
                
                # Add Piotroski score if available
                if 'piotroski_score' in row and row['piotroski_score'] is not None:
                    piotroski = row['piotroski_score']
                    if piotroski >= 7:
                        print(f"  📊 Piotroski Score: {piotroski}/9 (Strong)")
                    elif piotroski <= 3:
                        print(f"  📊 Piotroski Score: {piotroski}/9 (Weak)")
                    else:
                        print(f"  📊 Piotroski Score: {piotroski}/9 (Moderate)")
                
                # Add announcement time if available
                if 'announcement_time' in row and row['announcement_time']:
                    print(f"  🕐 Announcement Time: {row['announcement_time']} (IST)")
                
                # Add shareholding pattern for last 5 quarters if available
                if 'shareholding_pattern' in row and row['shareholding_pattern']:
                    shareholding = row['shareholding_pattern']
                    if 'Promoters +' in shareholding:
                        print(f"  📈 Shareholding Pattern (Last 5 Quarters):")
                        quarters = list(shareholding['Promoters +'].keys())
                        last_5_quarters = quarters[-5:] if len(quarters) >= 5 else quarters
                        
                        for quarter in last_5_quarters:
                            promoters = shareholding['Promoters +'].get(quarter, 'N/A')
                            fiis = shareholding.get('FIIs +', {}).get(quarter, 'N/A')
                            diis = shareholding.get('DIIs +', {}).get(quarter, 'N/A')
                            public = shareholding.get('Public +', {}).get(quarter, 'N/A')
                            print(f"    {quarter}: Promoters {promoters} | FIIs {fiis} | DIIs {diis} | Public {public}")
                
                if row['price'] > 0:
                    print(f"  Price: ₹{row['price']:.2f} | Market Cap: ₹{row['market_cap']/10000000:.1f} Cr")
                print()
        
        if not top_5_worst.empty:
            print(f"\n📉 TOP 5 COMPANIES WITH POOR RESULTS ({len(top_5_worst)} companies):")
            print("-" * 70)
            for idx, row in top_5_worst.iterrows():
                print(f"{row['name']} ({row['result_date']})")
                print(f"  Sales Growth: {row['sales_growth']:+.1f}% | "
                      f"EBIDT Growth: {row['ebidt_growth']:+.1f}% | "
                      f"Net Profit Growth: {row['net_profit_growth']:+.1f}% | "
                      f"EPS Growth: {row['eps_growth']:+.1f}%")
                print(f"  Composite Score: {row['composite_score']:.2f}")
                
                # Add Piotroski score if available
                if 'piotroski_score' in row and row['piotroski_score'] is not None:
                    piotroski = row['piotroski_score']
                    if piotroski >= 7:
                        print(f"  📊 Piotroski Score: {piotroski}/9 (Strong)")
                    elif piotroski <= 3:
                        print(f"  📊 Piotroski Score: {piotroski}/9 (Weak)")
                    else:
                        print(f"  📊 Piotroski Score: {piotroski}/9 (Moderate)")
                
                # Add announcement time if available
                if 'announcement_time' in row and row['announcement_time']:
                    print(f"  🕐 Announcement Time: {row['announcement_time']} (IST)")
                
                # Add shareholding pattern for last 5 quarters if available
                if 'shareholding_pattern' in row and row['shareholding_pattern']:
                    shareholding = row['shareholding_pattern']
                    if 'Promoters +' in shareholding:
                        print(f"  📈 Shareholding Pattern (Last 5 Quarters):")
                        quarters = list(shareholding['Promoters +'].keys())
                        last_5_quarters = quarters[-5:] if len(quarters) >= 5 else quarters
                        
                        for quarter in last_5_quarters:
                            promoters = shareholding['Promoters +'].get(quarter, 'N/A')
                            fiis = shareholding.get('FIIs +', {}).get(quarter, 'N/A')
                            diis = shareholding.get('DIIs +', {}).get(quarter, 'N/A')
                            public = shareholding.get('Public +', {}).get(quarter, 'N/A')
                            print(f"    {quarter}: Promoters {promoters} | FIIs {fiis} | DIIs {diis} | Public {public}")
                
                if row['price'] > 0:
                    print(f"  Price: ₹{row['price']:.2f} | Market Cap: ₹{row['market_cap']/10000000:.1f} Cr")
                print()
        
        print("="*100)


def main():
    """Main function to run the date range scraper"""
    print("🔍 Date Range Screener.in Quarterly Results Scraper")
    print("=" * 60)
    print("This scraper extracts quarterly financial results for specific date ranges")
    print("and analyzes top 5 best/worst performing companies.")
    print("Features:")
    print("• Handles pagination (multiple pages per date)")
    print("• Filters companies with market cap >= 1000 Cr")
    print("• Comprehensive financial analysis")
    print("• Extracts PDF links for detailed results")
    print("• Fetches announcement times from NSE (IST)")
    print("• Calculates Piotroski F-Score (0-9)")
    print("• Extracts shareholding patterns (last 5 quarters)")
    print("=" * 60)
    print("📝 Note: Announcement times are fetched from NSE website")
    print("   Format: DD-Mon-YYYY HH:MM (IST)")
    print("   Example: 29-Jul-2025 18:42")
    print("   ⚠️  NSE data is loaded dynamically - times may not be available")
    print("   📄 PDF links provide detailed reports with announcement times")
    print("=" * 60)
    
    # Check if credentials are properly configured
    if SCREENER_EMAIL == "your_email@example.com":
        print("\n⚠️  Please configure your credentials in config_local.py")
        return
    
    # Initialize scraper
    scraper = DateRangeScreenerScraper()
    
    print(f"\n👤 Using credentials for: {SCREENER_EMAIL}")
    
    # Ask user for date range
    print("\n📅 Enter date range to scrape:")
    start_date = input("Start date (YYYY-MM-DD, e.g., 2025-07-29): ").strip()
    end_date = input("End date (YYYY-MM-DD, e.g., 2025-07-29): ").strip()
    
    if not start_date or not end_date:
        print("❌ Please provide valid start and end dates")
        return
    
    try:
        # Validate dates
        datetime.strptime(start_date, '%Y-%m-%d')
        datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        print("❌ Invalid date format. Please use YYYY-MM-DD")
        return
    
    print(f"\n📅 Scraping date range: {start_date} to {end_date}")
    
    try:
        # Scrape the date range
        print("\n⏳ Starting data collection...")
        df = scraper.scrape_date_range(start_date, end_date)
        
        if df.empty:
            print("\n❌ No data found. This might be due to:")
            print("   1. No quarterly results available for the specified date range")
            print("   2. Website structure has changed")
            print("   3. Authentication failed")
            return
        
        print(f"\n✅ Successfully scraped data for {len(df)} companies")
        
        # Show data summary
        print(f"\n📊 Data Summary:")
        print(f"   Total Companies (Market Cap >= 1000 Cr): {len(df)}")
        print(f"   Companies with Sales Data: {len(df[df['sales'] > 0])}")
        print(f"   Companies with EBIDT Data: {len(df[df['ebidt'] != 0])}")
        print(f"   Companies with Net Profit Data: {len(df[df['net_profit'] != 0])}")
        print(f"   Companies with EPS Data: {len(df[df['eps'] != 0])}")
        print(f"   Companies with Growth Data: {len(df[df['sales_growth'] != 0])}")
        
        # Show market cap distribution
        if not df.empty:
            print(f"\n💰 Market Cap Distribution:")
            print(f"   Average Market Cap: ₹{df['market_cap'].mean()/10000000:.1f} Cr")
            print(f"   Median Market Cap: ₹{df['market_cap'].median()/10000000:.1f} Cr")
            print(f"   Min Market Cap: ₹{df['market_cap'].min()/10000000:.1f} Cr")
            print(f"   Max Market Cap: ₹{df['market_cap'].max()/10000000:.1f} Cr")
        
        # Show companies by date
        if not df.empty:
            print(f"\n📅 Companies by date:")
            date_counts = df['result_date'].value_counts().sort_index()
            for date, count in date_counts.items():
                print(f"   {date}: {count} companies")
        
        # Analyze results
        print("\n📈 Analyzing results...")
        top_5_best, top_5_worst = scraper.analyze_results(df)
        
        # Print analysis
        scraper.print_analysis(top_5_best, top_5_worst)
        
        # Save to CSV
        output_file = os.path.join(OUTPUT_DIR, f"date_range_screener_results_{start_date}_to_{end_date}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        df.to_csv(output_file, index=False)
        print(f"\n💾 Data saved to: {output_file}")
        
        # Show sample of raw data
        if not df.empty:
            print(f"\n📋 Sample of scraped data:")
            # Show key columns for better readability
            available_columns = ['name', 'market_cap', 'sales_growth', 'ebidt_growth', 'net_profit_growth', 'eps_growth']
            if 'composite_score' in df.columns:
                available_columns.append('composite_score')
            if 'announcement_time' in df.columns:
                available_columns.append('announcement_time')
            print(df[available_columns].head(3).to_string(index=False))
            
            # Show PDF links if available
            if 'pdf_url' in df.columns and not df['pdf_url'].isna().all():
                print(f"\n📄 PDF Links Available: {len(df[df['pdf_url'] != ''])} companies have PDF links")
                print("   Check the CSV file for complete PDF URLs")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Scraping interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        print("Please check your internet connection and try again.")


if __name__ == "__main__":
    main() 