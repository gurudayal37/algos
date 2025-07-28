# Screener Web Scraper

This folder contains the complete web scraper for extracting quarterly results from [Screener.in](https://www.screener.in/results/latest/).

## 📁 Files Overview

### 🎯 **Main Scrapers**
- **`working_screener_scraper.py`** - Scrapes current quarterly results
- **`date_range_screener_scraper.py`** - Scrapes results for a specific date range

### ⚙️ **Configuration**
- **`config.py`** - Template configuration file (safe to commit)
- **`config_local.py`** - Your actual credentials (DO NOT COMMIT)
- **`test_config.py`** - Tests if configuration is properly set up

### 📊 **Output**
- **`output/`** - Directory containing scraped results in CSV format

### 📚 **Documentation**
- **`README_Configuration.md`** - Detailed setup instructions

## 🚀 Quick Start

### 1. Setup Configuration
```bash
cd screener
python test_config.py
```

### 2. Run Current Results Scraper
```bash
python working_screener_scraper.py
```

### 3. Run Date Range Scraper
```bash
python date_range_screener_scraper.py
```

## 🔧 Configuration

### Required Credentials
You need a Screener.in account. Add your credentials to `config_local.py`:

```python
SCREENER_EMAIL = "your_email@example.com"
SCREENER_PASSWORD = "your_password_here"
```

### Security
- `config_local.py` is automatically ignored by Git
- Never commit your actual credentials
- Use `config.py` as a template

## 📈 Features

### Data Extracted
- Company name and symbol
- Sales growth
- EBIDT growth  
- Net Profit growth
- EPS growth
- Composite performance score

### Analysis
- Top 5 companies with best results
- Top 5 companies with worst results
- Daily analysis for date ranges
- Weighted scoring system

### Robustness
- Login authentication
- Retry logic with exponential backoff
- Random delays between requests
- User-agent rotation
- Error handling and logging

## 📊 Output Format

Results are saved as CSV files with columns:
- `name` - Company name
- `symbol` - Stock symbol
- `sales_growth` - Sales growth percentage
- `ebidt_growth` - EBIDT growth percentage
- `net_profit_growth` - Net profit growth percentage
- `eps_growth` - EPS growth percentage
- `composite_score` - Weighted performance score
- `result_date` - Date of quarterly results
- `scrape_date` - When data was scraped

## 🛠️ Troubleshooting

### Common Issues
1. **Login Failed**: Check credentials in `config_local.py`
2. **No Results**: Verify date range and website availability
3. **Rate Limiting**: Increase delays in configuration

### Debug Mode
Set `DEBUG_MODE = True` in config to save HTML files for debugging.

## 📝 Usage Examples

### Scrape Current Results
```python
from working_screener_scraper import WorkingScreenerScraper

scraper = WorkingScreenerScraper()
df = scraper.scrape_current_results()
```

### Scrape Date Range
```python
from date_range_screener_scraper import DateRangeScreenerScraper

scraper = DateRangeScreenerScraper()
df = scraper.scrape_date_range("2025-07-04", "2025-07-28")
```

## 🔒 Security Notes

- Credentials are stored locally only
- HTTPS requests for secure data transmission
- Session management for authentication
- No sensitive data in logs

## 📞 Support

For issues or questions:
1. Check the configuration with `test_config.py`
2. Review error logs in console output
3. Enable debug mode for detailed HTML inspection 