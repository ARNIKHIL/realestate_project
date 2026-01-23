"""
Compass.com property scraper for Brooklyn multi-family homes.
"""
import time
import random
from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
from loguru import logger

from models import ZillowProperty, Address
from config import config


class CompassScraper:
    """Scraper for Compass.com real estate listings."""
    
    def __init__(self):
        self.config = config.zillow  # Reuse same config structure
        self.driver = None
    
    def _setup_driver(self, headless: bool = False):
        """Initialize Selenium WebDriver with Chrome."""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--window-size=1920,1080")
        else:
            chrome_options.add_argument("--start-maximized")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # Hide webdriver
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
        })
        
        logger.info("Chrome WebDriver initialized for Compass")
    
    def _perform_search(self):
        """Navigate to Compass.com and perform search with filters."""
        try:
            # Open Compass homepage
            logger.info("Opening Compass.com homepage...")
            self.driver.get("https://www.compass.com")
            time.sleep(random.uniform(2, 4))
            
            # Find and fill location search box
            logger.info("Entering location: Brooklyn, NY")
            try:
                # Try various selectors for search input
                search_input = None
                selectors = [
                    "input[placeholder*='City, Address, School']",
                    "input[type='search']",
                    "input[name='location']",
                    "input[id*='search']",
                    "input[data-tn*='search']"
                ]
                
                for selector in selectors:
                    try:
                        search_input = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        break
                    except:
                        continue
                
                if not search_input:
                    # Try XPath as fallback
                    search_input = self.driver.find_element(By.XPATH, "//input[contains(@placeholder, 'search') or contains(@placeholder, 'Search') or contains(@placeholder, 'City')]")
                
                if search_input:
                    search_input.clear()
                    search_input.send_keys("Brooklyn, NY")
                    time.sleep(1)
                    
                    # Submit search (press Enter or click search button)
                    search_input.send_keys(Keys.RETURN)
                    time.sleep(random.uniform(3, 5))
                    logger.info("✅ Location search submitted")
            except Exception as e:
                logger.warning(f"Could not enter location via search: {e}")
            
            # Now set filters
            self._set_search_filters()
            
        except Exception as e:
            logger.error(f"Error performing search: {e}")
            raise
    
    def _set_search_filters(self):
        """Set search filters for beds, baths, price, and property type."""
        try:
            logger.info("Setting search filters...")
            time.sleep(2)
            
            # Look for filters button/menu
            try:
                # Click on filters or more filters button
                filter_button = None
                filter_selectors = [
                    "button[data-tn*='filter']",
                    "button[aria-label*='filter']",
                    "button:has-text('Filters')",
                    "div[class*='filter']"
                ]
                
                for selector in filter_selectors:
                    try:
                        filter_button = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        filter_button.click()
                        time.sleep(1)
                        break
                    except:
                        continue
                        
            except Exception as e:
                logger.debug(f"Filters button not found or not needed: {e}")
            
            # Set minimum beds to 5
            self._set_filter_value("beds", "5", "min")
            
            # Set minimum baths to 4
            self._set_filter_value("baths", "4", "min")
            
            # Set max price to $2,500,000
            self._set_filter_value("price", "2500000", "max")
            
            # Set property type to multi-family
            self._select_property_type("multi-family")
            
            # Apply filters
            try:
                apply_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Apply') or contains(text(), 'Done') or contains(text(), 'Show')]")
                apply_button.click()
                time.sleep(random.uniform(2, 4))
                logger.info("✅ Filters applied")
            except:
                logger.debug("No Apply button found - filters may auto-apply")
            
        except Exception as e:
            logger.error(f"Error setting filters: {e}")
    
    def _set_filter_value(self, filter_type: str, value: str, min_or_max: str = "min"):
        """Set a specific filter value (beds, baths, price)."""
        try:
            # Look for input fields related to the filter type
            selectors = [
                f"input[name*='{filter_type}'][name*='{min_or_max}']",
                f"input[id*='{filter_type}'][id*='{min_or_max}']",
                f"input[data-tn*='{filter_type}'][data-tn*='{min_or_max}']",
                f"select[name*='{filter_type}'][name*='{min_or_max}']"
            ]
            
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    element.clear()
                    element.send_keys(value)
                    logger.info(f"✅ Set {filter_type} {min_or_max} to {value}")
                    time.sleep(0.5)
                    return
                except:
                    continue
            
            logger.warning(f"Could not find input for {filter_type} {min_or_max}")
            
        except Exception as e:
            logger.debug(f"Error setting {filter_type} {min_or_max}: {e}")
    
    def _select_property_type(self, property_type: str):
        """Select property type from dropdown or checkboxes."""
        try:
            # Look for multi-family checkbox or option
            selectors = [
                f"input[value*='multi'][type='checkbox']",
                f"label:has-text('{property_type}')",
                f"button:has-text('{property_type}')"
            ]
            
            # Try to find and click multi-family option
            try:
                element = self.driver.find_element(By.XPATH, f"//label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'multi')]")
                element.click()
                logger.info(f"✅ Selected property type: {property_type}")
                time.sleep(0.5)
            except:
                logger.warning(f"Could not select property type: {property_type}")
                
        except Exception as e:
            logger.debug(f"Error selecting property type: {e}")
    
    def scrape_listings(self, max_pages: Optional[int] = None) -> List[ZillowProperty]:
        """
        Scrape property listings from Compass.
        
        Args:
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of ZillowProperty objects
        """
        if max_pages is None:
            max_pages = self.config.max_pages
        
        all_properties = []
        
        try:
            self._setup_driver(headless=False)
            logger.info("Browser ready - starting Compass scraping...")
            
            # Perform search with filters
            self._perform_search()
            logger.info("Search completed, now scraping results...")
            
            for page in range(1, max_pages + 1):
                logger.info(f"Scraping Compass page {page}/{max_pages}")
                
                try:
                    # For page 1, we're already on the results page
                    # For subsequent pages, need to navigate
                    if page > 1:
                        self._navigate_to_page(page)
                    
                    # Wait for page to load
                    time.sleep(random.uniform(3, 5))
                    
                    # Scroll to load lazy-loaded content
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                    time.sleep(1)
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    
                    # Parse the page
                    properties = self._parse_listings_page()
                    logger.info(f"Found {len(properties)} properties on page {page}")
                    all_properties.extend(properties)
                    
                    # Random delay between pages
                    if page < max_pages:
                        delay = random.uniform(3, 6)
                        logger.info(f"Waiting {delay:.1f}s before next page...")
                        time.sleep(delay)
                        
                except Exception as e:
                    logger.error(f"Error scraping page {page}: {e}")
                    continue
            
            logger.info(f"✅ Scraped {len(all_properties)} total properties from Compass")
            
        except Exception as e:
            logger.error(f"Fatal error in Compass scraper: {e}")
        finally:
            self._close_driver()
        
        return all_properties
    
    def _navigate_to_page(self, page: int):
        """Navigate to a specific page of results."""
        try:
            # Look for pagination controls
            pagination_selectors = [
                f"a[aria-label='Page {page}']",
                f"button[aria-label='Page {page}']",
                f"a:has-text('{page}')",
                f"button:has-text('{page}')"
            ]
            
            for selector in pagination_selectors:
                try:
                    page_link = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    page_link.click()
                    logger.info(f"Navigated to page {page}")
                    time.sleep(random.uniform(2, 4))
                    return
                except:
                    continue
            
            # If no specific page link, try "Next" button
            try:
                next_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Next') or contains(@aria-label, 'Next')]")
                next_button.click()
                logger.info(f"Clicked Next to navigate to page {page}")
                time.sleep(random.uniform(2, 4))
            except:
                logger.warning(f"Could not navigate to page {page}")
                
        except Exception as e:
            logger.error(f"Error navigating to page {page}: {e}")
    
    def _parse_listings_page(self) -> List[ZillowProperty]:
        """Parse property listings from current page."""
        properties = []
        
        try:
            # Wait for listings to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-tn='listings-container'], div[class*='listing'], article"))
            )
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find all listing cards - Compass uses various selectors
            listing_cards = soup.find_all(['article', 'div'], class_=lambda x: x and ('listing' in x.lower() or 'card' in x.lower()))
            
            if not listing_cards:
                # Try alternative selectors
                listing_cards = soup.find_all('div', attrs={'data-tn': lambda x: x and 'listing' in str(x).lower()})
            
            logger.info(f"Found {len(listing_cards)} listing cards on page")
            
            for card in listing_cards:
                try:
                    property_data = self._parse_listing_card(card)
                    if property_data:
                        properties.append(property_data)
                except Exception as e:
                    logger.debug(f"Error parsing listing card: {e}")
                    continue
                    
        except TimeoutException:
            logger.warning("Timeout waiting for listings to load")
        except Exception as e:
            logger.error(f"Error parsing listings page: {e}")
        
        return properties
    
    def _parse_listing_card(self, card) -> Optional[ZillowProperty]:
        """Parse a single listing card into a ZillowProperty object."""
        try:
            # Extract address
            address_elem = card.find(['h3', 'h2', 'div'], class_=lambda x: x and 'address' in str(x).lower())
            if not address_elem:
                address_elem = card.find('a', attrs={'data-tn': lambda x: x and 'address' in str(x).lower()})
            
            address_text = address_elem.get_text(strip=True) if address_elem else None
            
            if not address_text:
                return None
            
            # Parse address into components
            address_obj = self._parse_address(address_text)
            if not address_obj:
                return None
            
            # Extract price
            price_text = None
            price_elem = card.find(['span', 'div'], class_=lambda x: x and 'price' in str(x).lower())
            if price_elem:
                price_text = price_elem.get_text(strip=True)
            
            price = self._parse_price(price_text) if price_text else None
            
            # Extract bedrooms
            beds = None
            bed_elem = card.find(text=lambda x: x and ('bed' in str(x).lower() or 'bd' in str(x).lower()))
            if bed_elem:
                beds = self._extract_number(str(bed_elem))
            
            # Extract bathrooms
            baths = None
            bath_elem = card.find(text=lambda x: x and ('bath' in str(x).lower() or 'ba' in str(x).lower()))
            if bath_elem:
                baths = self._extract_number(str(bath_elem))
            
            # Extract square footage
            sqft = None
            sqft_elem = card.find(text=lambda x: x and 'sqft' in str(x).lower())
            if sqft_elem:
                sqft = self._extract_number(str(sqft_elem))
            
            # Extract property URL
            url = None
            link_elem = card.find('a', href=True)
            if link_elem:
                url = link_elem['href']
                if not url.startswith('http'):
                    url = f"https://www.compass.com{url}"
            
            # Create ZillowProperty object
            property_obj = ZillowProperty(
                address=address_obj,
                price=price,
                bedrooms=int(beds) if beds else None,
                bathrooms=float(baths) if baths else None,
                square_feet=int(sqft) if sqft else None,
                property_type="Multi Family",  # Assume multi-family based on search
                url=url
            )
            
            return property_obj
            
        except Exception as e:
            logger.debug(f"Error parsing listing card: {e}")
            return None
    
    def _parse_address(self, address_text: str) -> Optional[Address]:
        """Parse address text into Address object."""
        try:
            # Address format: "123 Main St, Brooklyn, NY 11201"
            parts = [p.strip() for p in address_text.split(',')]
            
            if len(parts) >= 3:
                street = parts[0]
                city = parts[1] if len(parts) > 1 else "Brooklyn"
                
                # Parse state and zip from last part
                state_zip = parts[-1].split() if len(parts) > 2 else []
                state = state_zip[0] if len(state_zip) > 0 else "NY"
                zip_code = state_zip[1] if len(state_zip) > 1 else None
                
                return Address(
                    street=street,
                    city=city,
                    state=state,
                    zip_code=zip_code,
                    borough="Brooklyn"
                )
            else:
                # Fallback - use raw text as street
                return Address(
                    street=address_text,
                    city="Brooklyn",
                    state="NY",
                    borough="Brooklyn"
                )
        except Exception as e:
            logger.debug(f"Error parsing address: {e}")
            return None
    
    def _parse_price(self, price_text: str) -> Optional[float]:
        """Parse price from text like '$1,295,000' to 1295000.0"""
        try:
            price_text = price_text.replace('$', '').replace(',', '').strip()
            # Handle 'K' and 'M' suffixes
            if 'k' in price_text.lower():
                return float(price_text.lower().replace('k', '')) * 1000
            elif 'm' in price_text.lower():
                return float(price_text.lower().replace('m', '')) * 1000000
            else:
                return float(price_text)
        except:
            return None
    
    def _extract_number(self, text: str) -> Optional[float]:
        """Extract first number from text."""
        import re
        match = re.search(r'(\d+\.?\d*)', text)
        if match:
            return float(match.group(1))
        return None
    
    def _close_driver(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            logger.info("Chrome WebDriver closed")
