"""
Enhanced Zillow scraper using undetected-chromedriver.
This version is much better at avoiding bot detection.
"""
import time
import re
from typing import List, Optional
from datetime import datetime
import random

try:
    import undetected_chromedriver as uc
    UC_AVAILABLE = True
except ImportError:
    UC_AVAILABLE = False
    print("⚠️  undetected-chromedriver not installed")
    print("   Install with: pip install undetected-chromedriver")

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

from models import ZillowProperty, Address
from config import config
from utils.logger import logger


class UndetectedZillowScraper:
    """
    Zillow scraper using undetected-chromedriver for better bot evasion.
    Use this if regular scraper gets too many CAPTCHAs.
    """
    
    def __init__(self):
        if not UC_AVAILABLE:
            raise ImportError("undetected-chromedriver not installed. Run: pip install undetected-chromedriver")
        
        self.config = config.zillow
        self.scraping_config = config.scraping
        self.driver = None
        
    def _setup_driver(self, headless: bool = True):
        """Initialize undetected Chrome driver."""
        options = uc.ChromeOptions()
        
        # Headless mode (no visible browser)
        if headless:
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
        else:
            options.add_argument("--start-maximized")
        
        # Less aggressive options (undetected handles most automatically)
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        
        # Create undetected Chrome instance
        self.driver = uc.Chrome(options=options, version_main=None, headless=headless)
        
        logger.info(f"Undetected Chrome WebDriver initialized ({'headless' if headless else 'visible'})")
    
    def _login_to_zillow(self) -> bool:
        """Login to Zillow account to avoid bot detection."""
        if not self.config.email or not self.config.password:
            logger.warning("No Zillow credentials provided, skipping login")
            return False
        
        try:
            logger.info("🔐 Logging into Zillow account...")
            
            # Navigate to sign in page
            self.driver.get("https://www.zillow.com/")
            time.sleep(random.uniform(2, 3))
            
            # Click sign in button
            try:
                sign_in_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-test='header-sign-in-button'], a[href*='signin']"))
                )
                sign_in_btn.click()
                time.sleep(random.uniform(2, 3))
            except TimeoutException:
                logger.warning("Could not find sign in button, trying direct URL")
                self.driver.get("https://www.zillow.com/user/acct/login/")
                time.sleep(random.uniform(2, 3))
            
            # Enter email
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name='email'], #email"))
            )
            email_input.clear()
            for char in self.config.email:
                email_input.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            time.sleep(random.uniform(0.5, 1.0))
            
            # Enter password
            password_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password'], input[name='password'], #password")
            password_input.clear()
            for char in self.config.password:
                password_input.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            time.sleep(random.uniform(0.5, 1.0))
            
            # Click submit
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], button[data-test='signin-button']")
            submit_btn.click()
            
            # Wait for login to complete
            time.sleep(random.uniform(4, 6))
            
            # Check if logged in
            page_source = self.driver.page_source.lower()
            if 'sign out' in page_source or 'my profile' in page_source or 'account' in page_source:
                logger.info("✅ Successfully logged into Zillow!")
                return True
            else:
                logger.warning("Login may have failed, continuing anyway...")
                return False
                
        except Exception as e:
            logger.error(f"Error during login: {e}")
            logger.info("Continuing without login...")
            return False
        
    def _close_driver(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            logger.info("Undetected Chrome WebDriver closed")
    
    def _solve_press_and_hold_captcha(self) -> bool:
        """Automatically solve 'Press & Hold' CAPTCHA."""
        try:
            logger.info("Attempting automatic CAPTCHA solve...")
            
            # Try multiple selectors for the button
            button_selectors = [
                "button[type='button']",
                "button.captcha-button",
                "div[role='button']",
                "//button[contains(., 'Press')]",
                "//div[contains(@class, 'captcha')]",
                "//*[contains(text(), 'Press')]"
            ]
            
            button = None
            for selector in button_selectors:
                try:
                    if selector.startswith('//'):
                        button = self.driver.find_element(By.XPATH, selector)
                    else:
                        button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if button and button.is_displayed():
                        logger.info(f"Found CAPTCHA button with selector: {selector}")
                        break
                except NoSuchElementException:
                    continue
            
            if not button:
                logger.warning("Could not locate CAPTCHA button")
                return False
            
            # Scroll button into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
            time.sleep(random.uniform(0.5, 1.0))
            
            # Create ActionChains for human-like interaction
            actions = ActionChains(self.driver)
            
            # Move to button with random offset
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-5, 5)
            actions.move_to_element_with_offset(button, offset_x, offset_y)
            actions.pause(random.uniform(0.3, 0.7))
            
            # Press and hold for 3-5 seconds
            hold_duration = random.uniform(3.0, 5.0)
            logger.info(f"Pressing and holding for {hold_duration:.1f} seconds...")
            actions.click_and_hold(button)
            actions.pause(hold_duration)
            actions.release()
            actions.perform()
            
            # Wait for CAPTCHA to clear
            time.sleep(3)
            
            # Verify CAPTCHA is solved
            page_source = self.driver.page_source.lower()
            if 'press & hold' not in page_source and 'captcha' not in page_source:
                logger.info("✅ CAPTCHA solved successfully!")
                return True
            else:
                logger.warning("CAPTCHA still present after attempt")
                return False
                
        except Exception as e:
            logger.error(f"Error solving CAPTCHA: {e}")
            return False
    
    def _build_search_url(self, page: int = 1) -> str:
        """Build Zillow search URL - same as regular scraper."""
        from config import config
        
        base = f"{self.config.base_url}/brooklyn-new-york-ny/duplex/"
        
        filter_state = {
            "sort": {"value": "globalrelevanceex"},
            "price": {"max": int(config.filters.max_price)},
            "mp": {"max": int(config.filters.max_price / 200)},
            "beds": {"min": config.filters.min_bedrooms},
            "baths": {"min": int(config.filters.min_bathrooms)},
            "sf": {"value": False},
            "tow": {"value": False},
            "con": {"value": False},
            "land": {"value": False},
            "apa": {"value": False},
            "manu": {"value": False},
            "apco": {"value": False}
        }
        
        search_state = {
            "pagination": {"currentPage": page} if page > 1 else {},
            "isMapVisible": True,
            "mapBounds": {
                "west": -74.91808229663286,
                "east": -73.57500368335161,
                "south": 40.13454713467564,
                "north": 40.97758383487431
            },
            "regionSelection": [{"regionId": 37607, "regionType": 17}],
            "filterState": filter_state,
            "isListVisible": True,
            "usersSearchTerm": "Brooklyn New York NY"
        }
        
        import json
        import urllib.parse
        
        query_json = json.dumps(search_state, separators=(',', ':'))
        encoded_query = urllib.parse.quote(query_json)
        
        return f"{base}?searchQueryState={encoded_query}"
    
    def scrape_listings(self, max_pages: Optional[int] = None, headless: bool = False) -> List[ZillowProperty]:
        """Scrape with undetected Chrome - much better bot evasion."""
        if max_pages is None:
            max_pages = self.config.max_pages
        
        all_properties = []
        logged_in = False
        
        # Setup driver once for all pages
        try:
            self._setup_driver(headless=headless)
            logger.info("Driver ready, attempting login...")
            
            # Try to login first (reduces bot detection significantly)
            if self.config.email and self.config.password:
                logged_in = self._login_to_zillow()
                if logged_in:
                    logger.info("✅ Logged in! Bot detection should be minimal now")
                    time.sleep(random.uniform(2, 3))
                else:
                    logger.warning("Login failed, continuing without login...")
            else:
                logger.warning("No credentials provided, scraping without login...")
        except Exception as e:
            logger.error(f"Error setting up driver: {e}")
            return all_properties
        
        # Scrape all pages with same browser session
        for page in range(1, max_pages + 1):
            logger.info(f"🚀 Scraping page {page}/{max_pages} {'(logged in)' if logged_in else '(no login)'}")
            
            try:
                url = self._build_search_url(page)
                self.driver.get(url)
                
                # Longer initial wait for undetected mode
                time.sleep(random.uniform(4, 7))
                
                # Human-like scrolling
                self.driver.execute_script("window.scrollTo(0, 400);")
                time.sleep(0.8)
                self.driver.execute_script("window.scrollTo(0, 800);")
                time.sleep(0.8)
                
                # Check for CAPTCHA - but only if button is actually visible
                page_source = self.driver.page_source.lower()
                captcha_detected = False
                
                if 'press & hold' in page_source or 'captcha' in page_source:
                    # Verify CAPTCHA is actually visible before attempting to solve
                    try:
                        # Try to find a visible CAPTCHA button
                        button_selectors = [
                            "button[type='button']",
                            "button.captcha-button",
                            "div[role='button']",
                            "//button[contains(., 'Press')]"
                        ]
                        
                        for selector in button_selectors:
                            try:
                                if selector.startswith('//'):
                                    btn = self.driver.find_element(By.XPATH, selector)
                                else:
                                    btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                                
                                # Check if button is actually visible and interactable
                                if btn and btn.is_displayed() and btn.size['height'] > 0 and btn.size['width'] > 0:
                                    captcha_detected = True
                                    logger.warning(f"⚠️  Visible CAPTCHA detected on page {page}")
                                    break
                            except (NoSuchElementException, Exception):
                                continue
                    except Exception:
                        pass
                
                if captcha_detected:
                    # Try automatic solving
                    captcha_solved = self._solve_press_and_hold_captcha()
                    
                    if captcha_solved:
                        logger.info("✅ CAPTCHA solved automatically! Continuing...")
                        time.sleep(2)
                    else:
                        # Try one more time with longer hold
                        logger.info("Retrying CAPTCHA solve with longer duration...")
                        time.sleep(2)
                        captcha_solved = self._solve_press_and_hold_captcha()
                        
                        if captcha_solved:
                            logger.info("✅ CAPTCHA solved on retry! Continuing...")
                            time.sleep(2)
                        else:
                            logger.error(f"❌ Could not solve CAPTCHA automatically on page {page}")
                            logger.info("Skipping this page and continuing...")
                            continue
                
                # Wait for property cards
                try:
                    WebDriverWait(self.driver, 30).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "article[data-test='property-card']"))
                    )
                except TimeoutException:
                    logger.warning(f"Timeout on page {page}")
                    continue
                
                # Get property cards
                property_cards = self.driver.find_elements(By.CSS_SELECTOR, "article[data-test='property-card']")
                logger.info(f"✅ Found {len(property_cards)} properties on page {page}")
                
                # Parse properties (use same parsing as regular scraper)
                from scrapers.zillow_scraper import ZillowScraper
                regular_scraper = ZillowScraper()
                
                for card in property_cards:
                    property_data = regular_scraper._parse_property_card(card)
                    if property_data:
                        all_properties.append(property_data)
                
            except Exception as e:
                logger.error(f"Error on page {page}: {e}")
            
            # Wait between pages (but don't close driver - keep session alive!)
            if page < max_pages:
                delay = random.uniform(3, 6)
                logger.info(f"⏳ Waiting {delay:.1f}s before next page...")
                time.sleep(delay)
        
        # Close driver after all pages scraped
        self._close_driver()
        
        logger.info(f"🎉 Total properties scraped: {len(all_properties)}")
        return all_properties
