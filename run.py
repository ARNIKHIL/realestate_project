#!/usr/bin/env python3
"""
Quick start script for the Real Estate Property Analysis System.

This script provides an interactive setup and execution experience.
"""
import os
import sys
from pathlib import Path


def check_environment():
    """Check if .env file exists, create from template if not."""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if not env_file.exists():
        print("⚠️  No .env file found.")
        if env_example.exists():
            response = input("Would you like to create one from .env.example? (y/n): ")
            if response.lower() == 'y':
                env_file.write_text(env_example.read_text())
                print("✅ Created .env file. Please edit it with your settings.")
                print(f"   Edit: {env_file.absolute()}")
                return False
        else:
            print("❌ No .env.example found. Please create a .env file manually.")
            return False
    return True


def check_dependencies():
    """Check if required packages are installed."""
    try:
        import selenium
        import pandas
        import aiohttp
        import pydantic
        import loguru
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\nPlease install dependencies:")
        print("  pip install -r requirements.txt")
        return False


def show_banner():
    """Display welcome banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   Real Estate Property Analysis System                       ║
║   NYC B-Unit Investment Opportunity Finder                   ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def show_menu():
    """Display main menu."""
    print("\nWhat would you like to do?\n")
    print("  1. Run complete analysis (scrape + match + filter + export)")
    print("  2. Check configuration")
    print("  3. Test HPD API connection")
    print("  4. View help")
    print("  5. Exit")
    print()


def check_config():
    """Display current configuration."""
    from config import config
    
    print("\n" + "=" * 60)
    print("CURRENT CONFIGURATION")
    print("=" * 60)
    
    print("\n📍 Search Settings:")
    print(f"  Location: {config.zillow.search_location}")
    print(f"  Max Pages: {config.zillow.max_pages}")
    
    print("\n💰 Filter Criteria:")
    print(f"  Price Range: ${config.filters.min_price:,.0f} - ${config.filters.max_price:,.0f}")
    print(f"  Min Units: {config.filters.min_units}")
    print(f"  Require B Units: {config.filters.require_b_units}")
    
    print("\n⚙️  Scraping Settings:")
    print(f"  Request Delay: {config.scraping.request_delay}s")
    print(f"  Max Retries: {config.scraping.max_retries}")
    
    print("\n📤 Output Settings:")
    print(f"  Output Directory: {config.output.output_dir}")
    print(f"  Formats: {', '.join(config.output.output_formats)}")
    
    print("\n" + "=" * 60)


def test_hpd_connection():
    """Test connection to HPD API."""
    import asyncio
    from scrapers.hpd_client import HPDClient
    from models import Address
    
    print("\n🔍 Testing HPD API connection...")
    
    async def test():
        async with HPDClient() as client:
            # Test with a known NYC address
            test_address = Address(
                street="123 MAIN ST",
                city="New York",
                state="NY",
                borough="Manhattan"
            )
            
            print(f"  Querying: {test_address}")
            result = await client.search_by_address(test_address)
            
            if result:
                print("✅ HPD API connection successful!")
                print(f"  Found building with {result.total_units} units")
                if result.has_b_units:
                    print(f"  B Units: {len(result.b_units)}")
            else:
                print("⚠️  No results found (API working, but no match for test address)")
    
    try:
        asyncio.run(test())
    except Exception as e:
        print(f"❌ HPD API test failed: {e}")


def run_analysis():
    """Run the main analysis."""
    print("\n" + "=" * 60)
    print("STARTING ANALYSIS")
    print("=" * 60)
    print("\nThis will:")
    print("  1. Scrape property listings from Zillow")
    print("  2. Cross-check with HPD database")
    print("  3. Filter by investment criteria")
    print("  4. Export results")
    print("\n⏱️  This may take several minutes depending on settings...")
    print()
    
    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    print()
    from main import run
    run()


def show_help():
    """Display help information."""
    help_text = """
╔═══════════════════════════════════════════════════════════════╗
║  HELP - Real Estate Property Analysis System                 ║
╚═══════════════════════════════════════════════════════════════╝

QUICK START:
  1. Edit .env file with your settings
  2. Run option 1 to start analysis
  3. Check output/ directory for results

CONFIGURATION:
  Edit .env file to customize:
    - Search location and pages
    - Price range and unit requirements
    - Output formats

IMPORTANT NOTES:
  ⚠️  Zillow actively blocks scrapers - results may vary
  ⚠️  Consider using proxies or Zillow's official API
  ⚠️  HPD API token recommended for better rate limits
     Get token at: https://data.cityofnewyork.us/

OUTPUT FILES:
  - CSV: Spreadsheet format
  - Excel: Formatted spreadsheet
  - JSON: Complete data
  - Summary: Statistics and top picks

For full documentation, see README.md

    """
    print(help_text)


def main():
    """Main entry point."""
    show_banner()
    
    # Pre-flight checks
    if not check_dependencies():
        sys.exit(1)
    
    if not check_environment():
        print("\n👉 Please configure your .env file and run again.")
        sys.exit(0)
    
    # Main loop
    while True:
        show_menu()
        
        choice = input("Enter your choice (1-5): ").strip()
        
        if choice == '1':
            run_analysis()
        elif choice == '2':
            check_config()
        elif choice == '3':
            test_hpd_connection()
        elif choice == '4':
            show_help()
        elif choice == '5':
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-5.")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Goodbye!")
        sys.exit(0)
