#!/usr/bin/env python3
"""
Test Configuration Setup for Screener Scraper
This script verifies that the configuration is properly set up.
"""

import os
import sys
from pathlib import Path

def test_config_files():
    """Test if configuration files exist and are properly set up."""
    print("🔧 Testing Screener Configuration Setup...")
    
    # Check if we're in the right directory
    current_dir = Path.cwd()
    print(f"📁 Current directory: {current_dir}")
    
    # Check if config_local.py exists
    config_local_path = Path("config_local.py")
    if config_local_path.exists():
        print("✅ config_local.py found")
        
        # Try to import and check credentials
        try:
            sys.path.insert(0, str(current_dir))
            from config_local import SCREENER_EMAIL, SCREENER_PASSWORD
            
            if SCREENER_EMAIL and SCREENER_EMAIL != "your_email@example.com":
                print(f"✅ Email configured: {SCREENER_EMAIL}")
            else:
                print("❌ Email not properly configured")
                
            if SCREENER_PASSWORD and SCREENER_PASSWORD != "your_password_here":
                print("✅ Password configured (hidden for security)")
            else:
                print("❌ Password not properly configured")
                
        except ImportError as e:
            print(f"❌ Error importing config_local.py: {e}")
    else:
        print("❌ config_local.py not found")
        print("   Please copy config.py to config_local.py and add your credentials")
    
    # Check if config.py exists
    config_path = Path("config.py")
    if config_path.exists():
        print("✅ config.py template found")
    else:
        print("❌ config.py not found")
    
    # Check if .gitignore includes config_local.py
    gitignore_path = Path("../.gitignore")
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            content = f.read()
            if "config_local.py" in content:
                print("✅ config_local.py is in .gitignore (secure)")
            else:
                print("⚠️  config_local.py not in .gitignore")
    else:
        print("⚠️  .gitignore not found")
    
    # Check if output directory exists
    output_path = Path("output")
    if output_path.exists():
        print("✅ output directory found")
    else:
        print("❌ output directory not found")
    
    print("\n🎯 Configuration Test Complete!")

if __name__ == "__main__":
    test_config_files() 