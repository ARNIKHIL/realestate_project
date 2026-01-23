"""
Zillow property scraper.

Note: Zillow actively blocks scrapers. This implementation uses Selenium for browser automation.
Consider using Zillow's official API if available, or use a proxy service.
"""
import time
import re
from typing import List, Optional
from datetime import datetime
import random
try:
    import undetected_chromedriver as uc
    UNDETECTED_AVAILABLE = True
except ImportError:
    UNDETECTED_AVAILABLE = False
    
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

from models import ZillowProperty, Address
from config import config
from utils.logger import logger


class ZillowScraper:
    """Scraper for Zillow property listings."""
    
    def __init__(self):
        self.config = config.zillow
        self.scraping_config = config.scraping
        self.driver = None
        
    def _setup_driver(self, headless: bool = False, use_existing: bool = False):
        """Initialize ChromeDriver - uses undetected if available and configured, otherwise regular Selenium.
        
        Args:
            headless: Run Chrome in headless mode (not recommended for CAPTCHA)
            use_existing: Not used with undetected-chromedriver
        """
        use_undetected = getattr(self.config, 'use_undetected', False) and UNDETECTED_AVAILABLE
        
        if use_undetected:
            logger.info("Attempting to use undetected-chromedriver...")
            try:
                options = uc.ChromeOptions()
                
                # Basic options
                if headless:
                    options.add_argument("--headless=new")
                    options.add_argument("--window-size=1920,1080")
                    logger.warning("Headless mode may trigger more CAPTCHAs")
                
                # Additional preferences for better stealth and stability
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-gpu")
                options.add_argument("--disable-software-rasterizer")
                options.add_argument("--disable-extensions")
                
                # Prevent crashes
                options.add_argument("--disable-crash-reporter")
                options.add_argument("--disable-in-process-stack-traces")
                
                # Use undetected-chromedriver with auto-detected version
                self.driver = uc.Chrome(
                    options=options,
                    use_subprocess=False,  # Changed to False for better stability
                    version_main=None,  # Auto-detect Chrome version
                    driver_executable_path=None,
                    browser_executable_path=None,
                )
                
                logger.info("✅ Undetected ChromeDriver initialized - bypassing bot detection")
                
                # Test that the driver is working
                self.driver.get("about:blank")
                time.sleep(1)
                return
                
            except Exception as e:
                logger.error(f"Failed to initialize undetected ChromeDriver: {e}")
                logger.info("Falling back to regular Selenium...")
                raise  # Re-raise to stop if undetected is required
        
        # Fallback to regular Selenium
        logger.info("Using regular Selenium ChromeDriver...")
        options = Options()
        
        if headless:
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
        
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--start-maximized")
        
        # Use webdriver-manager to auto-download correct chromedriver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
        logger.info("✅ Regular ChromeDriver initialized")
        
        # Test that the driver is working
        self.driver.get("about:blank")
        time.sleep(1)
    
    def _login_to_zillow(self) -> bool:
        """Login to Zillow account to avoid bot detection."""
        if not self.config.email or not self.config.password:
            logger.warning("No Zillow credentials provided, skipping login")
            return False
        
        try:
            logger.info("🔐 Logging into Zillow account...")
            
            # Navigate to home page
            self.driver.get("https://www.zillow.com/")
            time.sleep(3)
            
            # Click sign in button (will redirect to identity.zillow.com)
            try:
                sign_in_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-test='header-sign-in-button'], a[href*='signin']"))
                )
                sign_in_btn.click()
                logger.info("Clicked sign in, redirecting to identity.zillow.com...")
                time.sleep(5)
            except TimeoutException:
                logger.warning("Could not find sign in button, trying direct URL")
                self.driver.get("https://identity.zillow.com/")
                time.sleep(5)
            
            # IMMEDIATELY check for CAPTCHA on identity page
            logger.info("Checking for CAPTCHA on identity page...")
            max_captcha_attempts = 3
            for attempt in range(max_captcha_attempts):
                if self._check_and_solve_captcha():
                    logger.info(f"Solved CAPTCHA (attempt {attempt + 1})")
                    time.sleep(3)
                else:
                    break  # No CAPTCHA found, continue with login
            
            # STEP 1: Enter email/username on first page
            logger.info("Step 1: Entering email...")
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name='email'], input#email, input[name='username']"))
            )
            email_input.clear()
            email_input.send_keys(self.config.email)
            time.sleep(1)
            
            # Click "Continue" or "Next" button to go to password page
            try:
                next_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], button:contains('Continue'), button:contains('Next')")
                next_btn.click()
                logger.info("Clicked Continue, waiting for password page...")
                time.sleep(4)
            except NoSuchElementException:
                # Try pressing Enter instead
                from selenium.webdriver.common.keys import Keys
                email_input.send_keys(Keys.RETURN)
                time.sleep(4)
            
            # Check for CAPTCHA after email submission
            if self._check_and_solve_captcha():
                logger.info("Solved CAPTCHA after email step")
            
            # STEP 2: Enter password on second page
            logger.info("Step 2: Entering password...")
            password_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password'], input[name='password'], input#password"))
            )
            password_input.clear()
            password_input.send_keys(self.config.password)
            time.sleep(1)
            
            # Click submit/sign in button
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], button[data-test='signin-button']")
            submit_btn.click()
            
            # Wait for login to complete
            logger.info("Waiting for login to complete...")
            time.sleep(5)
            
            # Check for CAPTCHA after password submission
            if self._check_and_solve_captcha():
                logger.info("Solved CAPTCHA after password step")
                time.sleep(3)
            
            # Check if logged in
            page_source = self.driver.page_source.lower()
            if 'sign out' in page_source or 'my profile' in page_source or 'account settings' in page_source:
                logger.info("✅ Successfully logged into Zillow!")
                return True
            else:
                logger.warning("Login may have failed, continuing anyway...")
                return False
                
        except Exception as e:
            logger.error(f"Error during login: {e}")
            logger.info("Continuing without login...")
            return False
    
    def _check_and_solve_captcha(self) -> bool:
        """Check if CAPTCHA is present and solve it automatically."""
        page_source = self.driver.page_source.lower()
        
        if 'press & hold' in page_source or 'press and hold' in page_source:
            logger.warning("⚠️  CAPTCHA detected! Attempting to solve...")
            
            # Try to solve it
            if self._handle_press_and_hold_captcha():
                logger.info("✅ CAPTCHA solved successfully!")
                return True
            else:
                logger.error("❌ Failed to solve CAPTCHA automatically")
                logger.warning("You may need to solve it manually...")
                time.sleep(15)  # Give user time to solve manually
                return False
        
        return False
        
    def _handle_press_and_hold_captcha(self) -> bool:
        """Attempt to solve 'Press & Hold' CAPTCHA automatically."""
        try:
            logger.info("🤖 Attempting to solve Press & Hold CAPTCHA...")
            
            # Search directly for the button (will check iframes and main content)
            return self._find_and_click_captcha_button()
                
        except Exception as e:
            logger.error(f"Error solving CAPTCHA: {e}")
            return False
    
    def _find_and_click_captcha_button(self) -> bool:
        """Find and click the CAPTCHA button - Shadow DOM is closed, try alternative approach."""
        logger.info("⏳ Waiting for CAPTCHA button to appear...")
        max_wait = 20
        
        for i in range(max_wait):
            try:
                # Approach 1: Find iframes with "Human verification challenge" title
                iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                
                if i == 0:
                    logger.info(f"Found {len(iframes)} total iframes on page")
                
                for idx, iframe in enumerate(iframes):
                    try:
                        title = iframe.get_attribute("title") or ""
                        token = iframe.get_attribute("token") or ""
                        
                        if i == 0:
                            logger.info(f"  Iframe #{idx}: title='{title}', has_token={bool(token)}")
                        
                        # Look for verification challenge iframe
                        if "verification" in title.lower() or "challenge" in title.lower() or token:
                            if i == 0:
                                logger.info(f"  Trying iframe #{idx} with verification/token")
                            
                            self.driver.switch_to.frame(iframe)
                            
                            # Look for button
                            buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                                "[role='button'], div[aria-label*='Press'], div[aria-label*='press'], "
                                "div[tabindex='0'], button, div[class*='button']")
                            
                            if i == 0 and buttons:
                                logger.info(f"  Found {len(buttons)} button candidates in iframe #{idx}")
                            
                            for btn in buttons:
                                try:
                                    if not btn.is_displayed():
                                        if i == 0:
                                            logger.debug(f"    Button not displayed, skipping")
                                        continue
                                    
                                    aria_label = btn.get_attribute("aria-label") or ""
                                    class_name = btn.get_attribute("class") or ""
                                    text = btn.text.lower() if btn.text else ""
                                    
                                    if i == 0:
                                        logger.info(f"    Checking button: aria='{aria_label[:50]}', class='{class_name[:30]}', text='{text[:30]}'")
                                    
                                    if ("press" in aria_label.lower() or "hold" in aria_label.lower() or
                                        "press" in text or "button" in class_name.lower()):
                                        logger.info(f"✓ Found CAPTCHA button in iframe #{idx} after {i}s!")
                                        logger.info(f"  Button details: aria-label='{aria_label}', class='{class_name}'")
                                        result = self._click_and_hold_button(btn)
                                        self.driver.switch_to.default_content()
                                        return result
                                except Exception as btn_err:
                                    if i == 0:
                                        logger.debug(f"    Button check error: {str(btn_err)[:50]}")
                                    continue
                            
                            self.driver.switch_to.default_content()
                    except Exception as e:
                        if i == 0:
                            logger.debug(f"Iframe #{idx} error: {str(e)[:60]}")
                        try:
                            self.driver.switch_to.default_content()
                        except:
                            pass
                
                # Approach 2: Try clicking the px-captcha div directly (might work as fallback)
                try:
                    captcha_div = self.driver.find_element(By.ID, "px-captcha")
                    if captcha_div and captcha_div.is_displayed():
                        if i == 5:  # Try this after waiting a bit
                            logger.info("Attempting to click px-captcha div directly...")
                            result = self._click_and_hold_button(captcha_div)
                            if result:
                                return result
                except:
                    pass
                
            except Exception as e:
                if i == 0:
                    logger.error(f"Search error: {str(e)[:100]}")
            
            if i < max_wait - 1:
                time.sleep(1)
        
        logger.error(f"❌ Button did not appear after {max_wait} seconds")
        logger.warning("💡 PerimeterX CAPTCHA uses closed Shadow DOM - automation may not be possible")
        return False
    
    def _click_and_hold_button(self, button) -> bool:
        """Click and hold the given button element with human-like behavior."""
        import random
        
        try:
            # Random delay before interacting (looks more human)
            time.sleep(random.uniform(0.5, 1.5))
            
            # Scroll button into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
            time.sleep(random.uniform(0.5, 1.0))
            
            logger.info(f"Button location: {button.location}, size: {button.size}")
            
            # Create ActionChains with human-like behavior
            actions = ActionChains(self.driver)
            
            # Move to button with slight random offset (more human-like)
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-5, 5)
            actions.move_to_element_with_offset(button, offset_x, offset_y)
            actions.pause(random.uniform(0.3, 0.8))
            
            # CRITICAL: Hold for full duration WITHOUT releasing
            # PerimeterX requires 40-50 seconds of continuous pressure
            hold_duration = random.uniform(45.0, 55.0)
            logger.info(f"⏱️  Pressing and holding for {hold_duration:.1f} seconds...")
            logger.info("   (Maintaining continuous pressure - DO NOT move mouse)")
            
            # Start the hold
            actions.click_and_hold()
            actions.perform()
            
            # Keep the button pressed for the ENTIRE duration
            # Use time.sleep to ensure we don't release early
            time.sleep(hold_duration)
            
            # Now release
            logger.info("   Releasing button...")
            release_action = ActionChains(self.driver)
            release_action.release()
            release_action.perform()
            
            # Wait for verification
            logger.info("⏳ Waiting for CAPTCHA verification...")
            time.sleep(6)
            
            # Check if CAPTCHA solved
            page_source = self.driver.page_source.lower()
            if 'press & hold' not in page_source and 'please try again' not in page_source:
                logger.info("✅ CAPTCHA solved successfully!")
                return True
            else:
                logger.warning("CAPTCHA failed - 'Please try again' or still present")
                return False
                
        except Exception as e:
            logger.error(f"Error handling CAPTCHA: {e}")
            return False
    
    def _close_driver(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            logger.info("Chrome WebDriver closed")
    
    def _build_search_url(self, page: int = 1, location_name: str = "Brooklyn", region_id: int = 37607) -> str:
        """
        Build Zillow search URL with filters applied for a specific location.
        
        Args:
            page: Page number to scrape
            location_name: Name of the location (e.g., "Manhattan", "Brooklyn")
            region_id: Zillow region ID for the location
        
        Filters applied in URL:
        - Location: Dynamic based on input
        - Property type: Multi-family/Duplex
        - Price: max $2,500,000
        - Bedrooms: min 5
        - Bathrooms: min 4
        """
        from config import config
        
        # Build base URL with location
        location_slug = location_name.lower().replace(" ", "-")
        base = f"{self.config.base_url}/{location_slug}-new-york-ny/duplex/"
        
        # Build filter state with all criteria
        # Based on the user's example URL structure
        filter_state = {
            "sort": {"value": "globalrelevanceex"},  # Relevance sort
            "price": {"max": int(config.filters.max_price)},
            "mp": {"max": int(config.filters.max_price / 200)},  # Monthly payment estimate
            "beds": {"min": config.filters.min_bedrooms},
            "baths": {"min": int(config.filters.min_bathrooms)},
            # Exclude other property types
            "sf": {"value": False},      # Single family
            "tow": {"value": False},     # Townhouse
            "con": {"value": False},     # Condo
            "land": {"value": False},    # Land
            "apa": {"value": False},     # Apartment
            "manu": {"value": False},    # Manufactured
            "apco": {"value": False}     # Apt/Condo
        }
        
        # Build the search query state
        search_state = {
            "pagination": {"currentPage": page} if page > 1 else {},
            "isMapVisible": True,
            "mapBounds": {
                "west": -74.91808229663286,
                "east": -73.57500368335161,
                "south": 40.13454713467564,
                "north": 40.97758383487431
            },
            "regionSelection": [{"regionId": region_id, "regionType": 17}],  # Dynamic region
            "filterState": filter_state,
            "isListVisible": True,
            "usersSearchTerm": f"{location_name} New York NY"
        }
        
        # Convert to URL-encoded JSON
        import json
        import urllib.parse
        
        query_json = json.dumps(search_state, separators=(',', ':'))
        encoded_query = urllib.parse.quote(query_json)
        
        url = f"{base}?searchQueryState={encoded_query}"
        
        logger.debug(f"Built Zillow URL with filters: Price≤${config.filters.max_price:,}, Beds≥{config.filters.min_bedrooms}, Baths≥{config.filters.min_bathrooms}")
        
        return url
    
    def _parse_property_card(self, card_element) -> Optional[ZillowProperty]:
        """Parse a single property card element."""
        try:
            # Extract address - try multiple selectors
            address_text = ""
            try:
                address_elem = card_element.find_element(By.CSS_SELECTOR, "address")
                address_text = address_elem.text
            except NoSuchElementException:
                # Try alternative selectors
                try:
                    address_elem = card_element.find_element(By.CSS_SELECTOR, "[data-test='property-card-addr']")
                    address_text = address_elem.text
                except NoSuchElementException:
                    logger.debug("Could not find address element")
                    return None
            
            if not address_text:
                logger.debug("Empty address text")
                return None
            
            # Parse address components
            address_parts = address_text.split(",")
            if len(address_parts) < 1:
                logger.warning(f"Could not parse address: {address_text}")
                return None
            
            street = address_parts[0].strip()
            
            # Extract borough from address text
            borough = self._extract_borough(address_text)
            if not borough:
                # Default to Brooklyn since our search is Brooklyn-focused
                borough = "Brooklyn"
                logger.debug(f"No borough found in address, defaulting to Brooklyn: {address_text}")
            
            # Extract price - try multiple selectors
            price = None
            try:
                price_elem = card_element.find_element(By.CSS_SELECTOR, "span[data-test='property-card-price']")
                price_text = price_elem.text if price_elem else None
                if price_text:
                    price = self._parse_price(price_text)
            except NoSuchElementException:
                # Try alternative price selector
                try:
                    price_elem = card_element.find_element(By.CSS_SELECTOR, "[class*='price']")
                    price_text = price_elem.text
                    price = self._parse_price(price_text) if price_text else None
                except:
                    logger.debug(f"Could not find price for {street}")
            
            # Extract property details
            beds, baths, sqft = None, None, None
            try:
                # Try finding the details list
                details_elem = card_element.find_element(By.CSS_SELECTOR, "ul")
                details_text = details_elem.text
                beds, baths, sqft = self._parse_details(details_text)
            except NoSuchElementException:
                # Try alternative: individual bed/bath elements
                try:
                    bed_elem = card_element.find_element(By.CSS_SELECTOR, "[data-test='property-card-beds']")
                    beds = int(bed_elem.text.split()[0]) if bed_elem.text else None
                except:
                    pass
                try:
                    bath_elem = card_element.find_element(By.CSS_SELECTOR, "[data-test='property-card-baths']")
                    baths = float(bath_elem.text.split()[0]) if bath_elem.text else None
                except:
                    pass
                try:
                    sqft_elem = card_element.find_element(By.CSS_SELECTOR, "[data-test='property-card-sqft']")
                    sqft_text = sqft_elem.text.replace(',', '').replace('sqft', '').strip()
                    sqft = int(sqft_text) if sqft_text else None
                except:
                    pass
            
            # Extract URL - try multiple selectors
            url = None
            try:
                link_elem = card_element.find_element(By.CSS_SELECTOR, "a[data-test='property-card-link']")
                url = link_elem.get_attribute("href")
            except NoSuchElementException:
                try:
                    link_elem = card_element.find_element(By.CSS_SELECTOR, "a[href*='/homedetails/']")
                    url = link_elem.get_attribute("href")
                except:
                    logger.debug(f"Could not find URL for {street}")
            
            # Extract ZPID from URL
            zpid = None
            if url:
                zpid_match = re.search(r'/(\d+)_zpid/', url)
                if zpid_match:
                    zpid = zpid_match.group(1)
            
            # Extract property type
            property_type = "Multi Family"  # Default based on our search
            try:
                type_elem = card_element.find_element(By.CSS_SELECTOR, "span[data-test='property-card-type']")
                property_type = type_elem.text if type_elem.text else property_type
            except NoSuchElementException:
                pass
            
            # Try to extract lot size and year built from card text
            lot_size = None
            year_built = None
            try:
                card_text = card_element.text.lower()
                # Look for lot size
                lot_match = re.search(r'([\d,]+)\s*sqft\s*lot', card_text)
                if lot_match:
                    lot_size = int(lot_match.group(1).replace(',', ''))
                # Look for year built
                year_match = re.search(r'built\s+(\d{4})', card_text)
                if year_match:
                    year_built = int(year_match.group(1))
            except Exception:
                pass
            
            address = Address(
                street=street,
                city="New York",
                state="NY",
                zip_code=None,
                borough=borough
            )
            
            property_data = ZillowProperty(
                zpid=zpid,
                address=address,
                price=price,
                bedrooms=beds,
                bathrooms=baths,
                square_feet=sqft,
                lot_size=lot_size,
                year_built=year_built,
                property_type=property_type,
                url=url,
                listing_status="For Sale"
            )
            
            logger.debug(f"✅ Parsed: {street}, ${price}, {beds}bd/{baths}ba")
            return property_data
            
        except Exception as e:
            logger.error(f"Error parsing property card: {e}")
            return None
    
    def _parse_price(self, price_text: str) -> Optional[float]:
        """Parse price from text."""
        try:
            # Remove $ and commas, handle + signs
            clean_price = re.sub(r'[^\d.]', '', price_text.split('+')[0])
            return float(clean_price) if clean_price else None
        except:
            return None
    
    def _parse_details(self, details_text: str) -> tuple:
        """Parse bedrooms, bathrooms, and square feet."""
        beds, baths, sqft = None, None, None
        
        # Extract beds
        beds_match = re.search(r'(\d+)\s*bd', details_text, re.IGNORECASE)
        if beds_match:
            beds = int(beds_match.group(1))
        
        # Extract baths
        baths_match = re.search(r'(\d+)\s*ba', details_text, re.IGNORECASE)
        if baths_match:
            baths = float(baths_match.group(1))
        
        # Extract sqft
        sqft_match = re.search(r'([\d,]+)\s*sqft', details_text, re.IGNORECASE)
        if sqft_match:
            sqft = int(sqft_match.group(1).replace(',', ''))
        
        return beds, baths, sqft
    
    def _extract_borough(self, address_text: str) -> Optional[str]:
        """Extract NYC borough from address."""
        boroughs = {
            'manhattan': 'Manhattan',
            'brooklyn': 'Brooklyn',
            'queens': 'Queens',
            'bronx': 'Bronx',
            'staten island': 'Staten Island'
        }
        
        address_lower = address_text.lower()
        for key, value in boroughs.items():
            if key in address_lower:
                return value
        
        return None
    
    def scrape_listings(self, max_pages: Optional[int] = None, location_name: str = "Brooklyn", region_id: int = 37607) -> List[ZillowProperty]:
        """
        Scrape property listings from Zillow for a specific location.
        
        Strategy: Login once, then reuse the same browser session for all pages.
        Logged-in users are trusted and rarely get CAPTCHAs.
        
        Args:
            max_pages: Maximum number of pages to scrape. Defaults to config value.
            location_name: Name of the location to scrape (e.g., "Manhattan", "Brooklyn")
            region_id: Zillow region ID for the location
            
        Returns:
            List of ZillowProperty objects
        """
        if max_pages is None:
            max_pages = self.config.max_pages
        
        all_properties = []
        
        logger.info("\n" + "="*60)
        logger.info(f"Scraping {location_name}, NY")
        logger.info("="*60)
        
        # Setup driver
        try:
            # Use undetected-chromedriver for automatic bot detection bypass
            self._setup_driver(headless=False)
            logger.info("Browser ready - starting scraping...")
        except Exception as e:
            logger.error(f"Error setting up driver: {e}")
            return all_properties
        
        # Scrape all pages for this location
        for page in range(1, max_pages + 1):
            logger.info(f"Scraping {location_name} - page {page}/{max_pages}")
            
            try:
                url = self._build_search_url(page, location_name, region_id)
                logger.debug(f"Loading URL: {url[:100]}...")
                self.driver.get(url)
                
                # Random delay to mimic human behavior
                import random
                human_delay = random.uniform(3, 6)
                logger.debug(f"Waiting {human_delay:.1f}s for page to load...")
                time.sleep(human_delay)
                
                # Simulate human mouse movements on page before checking CAPTCHA
                try:
                    body = self.driver.find_element(By.TAG_NAME, "body")
                    actions = ActionChains(self.driver)
                    # Random movements to build "human" profile
                    for _ in range(random.randint(2, 4)):
                        x_offset = random.randint(50, 300)
                        y_offset = random.randint(50, 300)
                        actions.move_to_element_with_offset(body, x_offset, y_offset)
                        actions.pause(random.uniform(0.1, 0.3))
                    actions.perform()
                except:
                    pass
                
                # Scroll to mimic human browsing (light scrolling to appear human)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
                time.sleep(random.uniform(0.3, 0.7))
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(random.uniform(0.3, 0.7))
                
                # Check for CAPTCHA FIRST - try to solve it automatically
                logger.info(f"Checking for CAPTCHA on page {page}...")
                page_source = self.driver.page_source.lower()
                
                if 'press & hold' in page_source or 'press and hold' in page_source:
                    logger.warning(f"⚠️  CAPTCHA detected on page {page}! Attempting to solve...")
                    
                    # Try to solve CAPTCHA
                    if self._check_and_solve_captcha():
                        logger.info("✅ CAPTCHA solved! Continuing with scraping...")
                        time.sleep(3)
                    else:
                        logger.error("❌ Could not solve CAPTCHA automatically")
                        logger.warning("⏸️  Browser will pause for 20 seconds - solve manually if needed")
                        time.sleep(20)
                        
                        # Check again if user solved it
                        page_source = self.driver.page_source.lower()
                        if 'press & hold' in page_source:
                            logger.error("CAPTCHA still present, skipping this page...")
                            continue
                
                # NOW scroll to load all lazy-loaded properties (AFTER CAPTCHA is solved)
                logger.info("📜 Finding and scrolling the actual listings container...")
                
                try:
                    # JavaScript to find all scrollable elements
                    find_scrollable_script = """
                    function findScrollableElements() {
                        const all = document.querySelectorAll('*');
                        const scrollable = [];
                        for (let el of all) {
                            const style = window.getComputedStyle(el);
                            const hasScrollbar = el.scrollHeight > el.clientHeight;
                            const isScrollable = style.overflowY === 'scroll' || style.overflowY === 'auto';
                            
                            if (hasScrollbar && isScrollable && el.scrollHeight > 1000) {
                                scrollable.push({
                                    element: el,
                                    scrollHeight: el.scrollHeight,
                                    clientHeight: el.clientHeight,
                                    tag: el.tagName,
                                    id: el.id,
                                    classes: el.className
                                });
                            }
                        }
                        return scrollable;
                    }
                    return findScrollableElements();
                    """
                    
                    scrollable_elements = self.driver.execute_script(find_scrollable_script)
                    
                    if scrollable_elements:
                        logger.info(f"  ✅ Found {len(scrollable_elements)} scrollable elements")
                        for i, elem_info in enumerate(scrollable_elements[:3]):  # Check top 3
                            logger.info(f"    #{i+1}: {elem_info['tag']} (height: {elem_info['scrollHeight']}px, id: {elem_info.get('id', 'N/A')})")
                        
                        # Get the first (likely main) scrollable element
                        scroll_script = """
                        const scrollable = arguments[0];
                        const scrollAmount = arguments[1];
                        scrollable.scrollTop += scrollAmount;
                        return scrollable.scrollTop;
                        """
                        
                        # Find the element again to scroll it
                        main_scrollable = self.driver.execute_script("""
                            const all = document.querySelectorAll('*');
                            for (let el of all) {
                                const style = window.getComputedStyle(el);
                                const hasScrollbar = el.scrollHeight > el.clientHeight;
                                const isScrollable = style.overflowY === 'scroll' || style.overflowY === 'auto';
                                if (hasScrollbar && isScrollable && el.scrollHeight > 1000) {
                                    return el;
                                }
                            }
                            return null;
                        """)
                        
                        if main_scrollable:
                            logger.info("  🎯 Found main scrollable container, scrolling it...")
                            
                            # Scroll progressively
                            for i in range(15):
                                scroll_pos = self.driver.execute_script(scroll_script, main_scrollable, 500)
                                logger.info(f"  ⬇️  Scroll #{i+1}/15 - position: {scroll_pos}px")
                                time.sleep(random.uniform(1, 2))
                            
                            # Wait for final load
                            time.sleep(3)
                            
                            # Scroll back to top
                            logger.info("  ⬆️  Scrolling back to top...")
                            self.driver.execute_script("arguments[0].scrollTop = 0;", main_scrollable)
                            time.sleep(1)
                        else:
                            logger.warning("  ⚠️  Could not get scrollable element reference")
                    else:
                        logger.warning("  ⚠️  No scrollable elements found, using fallback...")
                        # Fallback: scroll the window
                        for i in range(10):
                            self.driver.execute_script(f"window.scrollBy(0, 600);")
                            time.sleep(1.5)
                    
                except Exception as scroll_error:
                    logger.error(f"  ❌ Scroll error: {scroll_error}")
                    # Simple fallback
                    for i in range(8):
                        self.driver.execute_script(f"window.scrollBy(0, 700);")
                        time.sleep(1.5)
                
                # Wait for property cards to load
                try:
                    WebDriverWait(self.driver, self.scraping_config.timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "article[data-test='property-card']"))
                    )
                except TimeoutException:
                    logger.warning(f"Timeout waiting for property cards on page {page}")
                    
                    # Check if we've reached the end of results
                    no_results_indicators = [
                        "no results found",
                        "0 homes",
                        "no homes available",
                        "didn't find any results"
                    ]
                    
                    if any(indicator in page_source for indicator in no_results_indicators):
                        logger.info(f"Reached end of results at page {page}")
                        break
                    
                    logger.warning(f"Page {page} may have been blocked or has no results")
                    continue
                
                # Find all property cards
                property_cards = self.driver.find_elements(By.CSS_SELECTOR, "article[data-test='property-card']")
                logger.info(f"Found {len(property_cards)} property cards on page {page}")
                
                if len(property_cards) == 0:
                    logger.warning(f"No property cards found on page {page}")
                    # Don't break - might be temporary, try next page
                    continue
                
                # Parse each property card
                page_properties = 0
                for card in property_cards:
                    property_data = self._parse_property_card(card)
                    if property_data:
                        all_properties.append(property_data)
                        page_properties += 1
                        # Log each address found
                        logger.info(f"  📍 Found: {property_data.address.street}")
                
                logger.info(f"Successfully parsed {page_properties} properties from page {page}")
                
            except Exception as e:
                logger.error(f"Error scraping page {page}: {e}")
            
            # Wait between pages (keep browser open!)
            if page < max_pages:
                import random
                delay = random.uniform(3, 5)
                logger.info(f"Waiting {delay:.1f}s before next page...")
                time.sleep(delay)
        
        # Close driver after all pages
        self._close_driver()
        
        logger.info(f"Successfully scraped {len(all_properties)} properties from {location_name} across {max_pages} pages")
        return all_properties
    
    def scrape_all_locations(self, max_pages: Optional[int] = None) -> List[ZillowProperty]:
        """
        Scrape property listings from all configured NYC locations.
        
        This method iterates through all locations in the config (Manhattan, Brooklyn, Bronx, Queens)
        and scrapes properties from each location.
        
        Args:
            max_pages: Maximum number of pages to scrape per location. Defaults to config value.
            
        Returns:
            Combined list of ZillowProperty objects from all locations
        """
        if max_pages is None:
            max_pages = self.config.max_pages
        
        all_properties = []
        locations = self.config.locations
        
        logger.info("\n" + "="*80)
        logger.info(f"Starting multi-location scraping: {', '.join([loc['name'] for loc in locations])}")
        logger.info(f"Pages per location: {max_pages}")
        logger.info("="*80 + "\n")
        
        # Setup driver once for all locations
        try:
            self._setup_driver(headless=False)
            logger.info("Browser ready - starting multi-location scraping...")
            time.sleep(3)  # Give the browser time to fully initialize
        except Exception as e:
            logger.error(f"Error setting up driver: {e}")
            return all_properties
        
        # Scrape each location
        for idx, location in enumerate(locations, 1):
            location_name = location['name']
            region_id = location['region_id']
            
            logger.info("\n" + "="*80)
            logger.info(f"Location {idx}/{len(locations)}: {location_name}, NY")
            logger.info("="*80)
            
            # Scrape all pages for this location
            for page in range(1, max_pages + 1):
                logger.info(f"Scraping {location_name} - page {page}/{max_pages}")
                
                try:
                    # Check if driver is still alive, if not reinitialize
                    try:
                        _ = self.driver.current_url
                    except Exception as driver_error:
                        logger.warning(f"Driver connection lost, reinitializing: {driver_error}")
                        try:
                            self._close_driver()
                        except:
                            pass
                        self._setup_driver(headless=False)
                        time.sleep(2)
                    
                    url = self._build_search_url(page, location_name, region_id)
                    logger.debug(f"Loading URL: {url[:100]}...")
                    self.driver.get(url)
                    
                    # Random delay to mimic human behavior
                    import random
                    human_delay = random.uniform(3, 6)
                    logger.debug(f"Waiting {human_delay:.1f}s for page to load...")
                    time.sleep(human_delay)
                    
                    # Simulate human mouse movements
                    try:
                        body = self.driver.find_element(By.TAG_NAME, "body")
                        actions = ActionChains(self.driver)
                        for _ in range(random.randint(2, 4)):
                            x_offset = random.randint(50, 300)
                            y_offset = random.randint(50, 300)
                            actions.move_to_element_with_offset(body, x_offset, y_offset)
                            actions.pause(random.uniform(0.1, 0.3))
                        actions.perform()
                    except:
                        pass
                    
                    # Scroll
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
                    time.sleep(random.uniform(0.3, 0.7))
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                    time.sleep(random.uniform(0.3, 0.7))
                    
                    # Check for CAPTCHA
                    logger.info(f"Checking for CAPTCHA on page {page}...")
                    page_source = self.driver.page_source.lower()
                    
                    if 'press & hold' in page_source or 'press and hold' in page_source:
                        logger.warning(f"⚠️  CAPTCHA detected on page {page}! Attempting to solve...")
                        
                        if self._check_and_solve_captcha():
                            logger.info("✅ CAPTCHA solved! Continuing with scraping...")
                            time.sleep(3)
                        else:
                            logger.error("❌ Could not solve CAPTCHA automatically")
                            logger.warning("⏸️  Browser will pause for 20 seconds - solve manually if needed")
                            time.sleep(20)
                            
                            page_source = self.driver.page_source.lower()
                            if 'press & hold' in page_source:
                                logger.error("CAPTCHA still present, skipping this page...")
                                continue
                    
                    # Scroll to load all properties
                    logger.info("📜 Scrolling to load all listings...")
                    
                    try:
                        main_scrollable = self.driver.execute_script("""
                            const all = document.querySelectorAll('*');
                            for (let el of all) {
                                const style = window.getComputedStyle(el);
                                const hasScrollbar = el.scrollHeight > el.clientHeight;
                                const isScrollable = style.overflowY === 'scroll' || style.overflowY === 'auto';
                                if (hasScrollbar && isScrollable && el.scrollHeight > 1000) {
                                    return el;
                                }
                            }
                            return null;
                        """)
                        
                        if main_scrollable:
                            scroll_script = """
                            const scrollable = arguments[0];
                            const scrollAmount = arguments[1];
                            scrollable.scrollTop += scrollAmount;
                            return scrollable.scrollTop;
                            """
                            
                            for i in range(15):
                                self.driver.execute_script(scroll_script, main_scrollable, 500)
                                time.sleep(random.uniform(1, 2))
                            
                            time.sleep(3)
                            self.driver.execute_script("arguments[0].scrollTop = 0;", main_scrollable)
                            time.sleep(1)
                        else:
                            for i in range(10):
                                self.driver.execute_script(f"window.scrollBy(0, 600);")
                                time.sleep(1.5)
                    except Exception as scroll_error:
                        logger.error(f"Scroll error: {scroll_error}")
                        for i in range(8):
                            self.driver.execute_script(f"window.scrollBy(0, 700);")
                            time.sleep(1.5)
                    
                    # Wait for property cards
                    try:
                        WebDriverWait(self.driver, self.scraping_config.timeout).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "article[data-test='property-card']"))
                        )
                    except TimeoutException:
                        logger.warning(f"Timeout waiting for property cards on page {page} in {location_name}")
                        
                        no_results_indicators = [
                            "no results found",
                            "0 homes",
                            "no homes available",
                            "didn't find any results"
                        ]
                        
                        if any(indicator in page_source for indicator in no_results_indicators):
                            logger.info(f"Reached end of results at page {page} for {location_name}")
                            break
                        
                        logger.warning(f"Page {page} may have been blocked or has no results")
                        continue
                    
                    # Parse property cards
                    property_cards = self.driver.find_elements(By.CSS_SELECTOR, "article[data-test='property-card']")
                    logger.info(f"Found {len(property_cards)} property cards on page {page}")
                    
                    if len(property_cards) == 0:
                        logger.warning(f"No property cards found on page {page} in {location_name}")
                        continue
                    
                    # Parse each card
                    page_properties = 0
                    for card in property_cards:
                        property_data = self._parse_property_card(card)
                        if property_data:
                            all_properties.append(property_data)
                            page_properties += 1
                            logger.info(f"  📍 Found: {property_data.address.street}")
                    
                    logger.info(f"Successfully parsed {page_properties} properties from {location_name} page {page}")
                    
                except Exception as e:
                    logger.error(f"Error scraping {location_name} page {page}: {e}")
                
                # Wait between pages
                if page < max_pages:
                    import random
                    delay = random.uniform(3, 5)
                    logger.info(f"Waiting {delay:.1f}s before next page...")
                    time.sleep(delay)
            
            # Wait between locations
            if idx < len(locations):
                import random
                delay = random.uniform(5, 8)
                logger.info("\n" + "="*60)
                logger.info(f"Completed {location_name}: {sum(1 for p in all_properties if p.address.borough == location_name)} properties")
                logger.info(f"Waiting {delay:.1f}s before next location...")
                logger.info("="*60 + "\n")
                time.sleep(delay)
        
        # Close driver after all locations
        self._close_driver()
        
        logger.info("\n" + "="*80)
        logger.info("MULTI-LOCATION SCRAPING COMPLETE")
        logger.info("="*80)
        logger.info(f"Total properties scraped: {len(all_properties)}")
        
        # Log breakdown by location
        for location in locations:
            location_name = location['name']
            count = sum(1 for p in all_properties if p.address.borough == location_name)
            logger.info(f"  {location_name}: {count} properties")
        
        logger.info("="*80 + "\n")
        
        return all_properties
    
    def scrape_property_details(self, url: str) -> Optional[dict]:
        """
        Scrape detailed information from a specific property page.
        
        Args:
            url: Property URL
            
        Returns:
            Dictionary with additional property details
        """
        # This can be expanded to get more details from individual property pages
        # For now, we'll keep it as a placeholder
        logger.info(f"Detailed scraping not yet implemented for: {url}")
        return None
