# 🔐 Secure Configuration Setup for Screener.in Scraper

This document explains how to securely configure your Screener.in credentials without exposing them to GitHub.

## 📁 Configuration Files

### **1. `config.py` (Template)**
- **Purpose**: Template configuration file with placeholder values
- **Status**: ✅ Safe to commit to GitHub
- **Contains**: Example structure and default settings

### **2. `config_local.py` (Your Credentials)**
- **Purpose**: Your actual credentials and settings
- **Status**: ❌ **NEVER commit to GitHub** (already in .gitignore)
- **Contains**: Your real email and password

## 🔧 Setup Instructions

### **Step 1: Create Your Local Configuration**
```bash
# Copy the template to create your local config
cp config.py config_local.py
```

### **Step 2: Update Your Credentials**
Edit `config_local.py` and replace the placeholder values:

```python
# Screener.in Login Credentials
SCREENER_EMAIL = "thefitinvestors@gmail.com"
SCREENER_PASSWORD = "1234Stock4321!"
```

### **Step 3: Test Your Configuration**
```bash
python test_config.py
```

You should see:
```
✅ config_local.py found
✅ Credentials loaded successfully
   Email: thefitinvestors@gmail.com
   Password: **************
✅ Real credentials detected
```

## 🛡️ Security Features

### **Git Protection**
- `config_local.py` is automatically added to `.gitignore`
- Your credentials will never be pushed to GitHub
- Template file (`config.py`) is safe to share

### **Configuration Options**
```python
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
```

## 🚀 Usage

### **Run the Scraper**
```bash
python final_screener_scraper.py
```

The scraper will automatically:
1. Load your credentials from `config_local.py`
2. Use the configured date range
3. Save results to the `output/` directory
4. Create debug files if `DEBUG_MODE = True`

### **Expected Output**
```
✅ Loaded local configuration with credentials
📅 Scraping date range: 2025-07-04 to 2025-07-28
👤 Using credentials for: thefitinvestors@gmail.com
```

## 📊 Output Files

All output files are saved to the `output/` directory:

- **CSV Results**: `final_screener_results_YYYY-MM-DD_to_YYYY-MM-DD.csv`
- **Debug HTML**: `debug_final_page_YYYY-MM-DD.html` (if DEBUG_MODE = True)
- **Analysis**: Printed to console with top 5 best/worst companies per day

## 🔍 Troubleshooting

### **Configuration Issues**
```bash
# Test your configuration
python test_config.py

# Check if files exist
ls -la config*.py
```

### **Common Problems**

1. **"No configuration file found"**
   - Solution: Create `config_local.py` from `config.py`

2. **"Using template email"**
   - Solution: Update `config_local.py` with real credentials

3. **"config_local.py not in .gitignore"**
   - Solution: Add `config_local.py` to `.gitignore`

### **Security Checklist**
- [ ] `config_local.py` exists with your credentials
- [ ] `config_local.py` is in `.gitignore`
- [ ] `config.py` template is safe to share
- [ ] Credentials are not hardcoded in any other files

## 🔄 Updating Configuration

### **Change Date Range**
Edit `config_local.py`:
```python
DEFAULT_START_DATE = "2025-07-21"
DEFAULT_END_DATE = "2025-07-22"
```

### **Adjust Analysis Weights**
```python
COMPOSITE_SCORE_WEIGHTS = {
    'sales_growth': 0.3,      # Increase weight for sales
    'ebidt_growth': 0.2,      # Decrease weight for EBIDT
    'net_profit_growth': 0.3, # Keep profit weight
    'eps_growth': 0.2         # Keep EPS weight
}
```

### **Disable Debug Mode**
```python
DEBUG_MODE = False  # No debug HTML files will be created
```

## 📝 File Structure
```
algos/
├── config.py              # Template (safe to commit)
├── config_local.py        # Your credentials (ignored by git)
├── test_config.py         # Configuration tester
├── final_screener_scraper.py  # Main scraper
├── output/                # Results directory
│   ├── *.csv             # Scraped data
│   └── debug_*.html      # Debug files
└── .gitignore            # Protects config_local.py
```

## ⚠️ Important Notes

1. **Never commit `config_local.py`** - it contains your real credentials
2. **Share `config.py`** - it's safe and helps others set up the scraper
3. **Test configuration** - always run `test_config.py` after setup
4. **Keep credentials secure** - don't share them in code or documentation

## 🆘 Need Help?

If you encounter issues:
1. Run `python test_config.py` to diagnose problems
2. Check that `config_local.py` exists and has correct credentials
3. Verify `.gitignore` includes `config_local.py`
4. Ensure all required Python packages are installed 