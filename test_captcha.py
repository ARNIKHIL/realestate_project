"""
Test script to compare regular vs undetected scraper.
The undetected version should have much better success rate.
"""
import sys
from scrapers.zillow_scraper import ZillowScraper
from scrapers.zillow_scraper_undetected import UndetectedZillowScraper
from utils.logger import logger

def test_regular_scraper():
    """Test the regular scraper with CAPTCHA solving."""
    logger.info("=" * 60)
    logger.info("TESTING REGULAR SCRAPER (with ActionChains CAPTCHA solver)")
    logger.info("=" * 60)
    
    scraper = ZillowScraper()
    properties = scraper.scrape_listings(max_pages=3)
    
    logger.info(f"\n✅ Regular scraper found {len(properties)} properties")
    return len(properties)

def test_undetected_scraper():
    """Test the undetected scraper (better bot evasion)."""
    logger.info("=" * 60)
    logger.info("TESTING UNDETECTED SCRAPER (superior bot evasion)")
    logger.info("=" * 60)
    
    try:
        scraper = UndetectedZillowScraper()
        properties = scraper.scrape_listings(max_pages=3)
        
        logger.info(f"\n✅ Undetected scraper found {len(properties)} properties")
        return len(properties)
    except ImportError as e:
        logger.error(f"❌ {e}")
        logger.info("Run: pip install undetected-chromedriver")
        return 0

def main():
    print("\n" + "=" * 60)
    print("CAPTCHA BYPASS TEST - Brooklyn Multi-Family Properties")
    print("=" * 60)
    print("\nThis script tests two scraping approaches:")
    print("1. Regular Selenium with ActionChains CAPTCHA solving")
    print("2. Undetected-chromedriver (better bot evasion)")
    print("\nBoth will scrape 3 pages (~27 properties)")
    print("=" * 60 + "\n")
    
    choice = input("Choose scraper:\n  1 = Regular (ActionChains)\n  2 = Undetected\n  3 = Both\nChoice: ").strip()
    
    results = {}
    
    if choice in ['1', '3']:
        results['regular'] = test_regular_scraper()
    
    if choice in ['2', '3']:
        results['undetected'] = test_undetected_scraper()
    
    # Summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    for scraper_type, count in results.items():
        success_rate = (count / 27) * 100 if count > 0 else 0
        print(f"{scraper_type.upper()}: {count} properties ({success_rate:.1f}% success)")
    print("=" * 60)
    
    if 'undetected' in results and results['undetected'] > results.get('regular', 0):
        print("\n💡 Recommendation: Use UndetectedZillowScraper")
        print("   Update main.py to use zillow_scraper_undetected")
    elif 'regular' in results and results['regular'] >= 20:
        print("\n💡 Regular scraper working well with ActionChains!")

if __name__ == "__main__":
    main()
