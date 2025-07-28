# Screener.in Configuration
# Fill in your credentials below and rename this file to config_local.py

# Screener.in Login Credentials
SCREENER_EMAIL = "your_email@example.com"
SCREENER_PASSWORD = "your_password_here"

# Scraping Configuration
MAX_RETRIES = 3
DELAY_RANGE = (1, 3)  # seconds between requests

# Date Range Configuration
DEFAULT_START_DATE = "2025-07-04"
DEFAULT_END_DATE = "2025-07-28"

# Analysis Configuration
COMPOSITE_SCORE_WEIGHTS = {
    'sales_growth': 0.25,
    'ebidt_growth': 0.25,
    'net_profit_growth': 0.3,
    'eps_growth': 0.2
}

# Output Configuration
OUTPUT_DIR = "output"
DEBUG_MODE = True  # Set to False to disable debug HTML files 