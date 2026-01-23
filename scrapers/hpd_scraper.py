"""
NYC HPD Online web scraper.

Scrapes building and B unit information from https://hpdonline.nyc.gov/hpdonline/
"""
import time
import random
from typing import List, Optional
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from models import HPDBuilding, HPDBUnit, Address
from utils.logger import logger


class HPDScraper:
    """Scraper for HPD Online website."""
    
    def __init__(self):
        self.base_url = "https://hpdonline.nyc.gov/hpdonline/"
        self.driver = None
    
    def _setup_driver(self):
        """Initialize undetected ChromeDriver."""
        options = uc.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        
        self.driver = uc.Chrome(
            options=options,
            use_subprocess=True,
            version_main=None,
        )
        
        logger.info("✅ HPD Scraper - Undetected ChromeDriver initialized")
    
    def _close_driver(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            logger.info("HPD Scraper - ChromeDriver closed")
    
    def search_by_address(self, address: Address) -> Optional[HPDBuilding]:
        """
        Search HPD Online for a building by address and extract B unit information.
        
        Args:
            address: Address object
            
        Returns:
            HPDBuilding object if found, None otherwise
        """
        try:
            if not self.driver:
                self._setup_driver()
            
            search_query = f"{address.street}, {address.borough or 'Brooklyn'}, NY"
            logger.info(f"🔎 HPD Search Query: {search_query}")
            
            # Navigate to HPD Online
            self.driver.get(self.base_url)
            time.sleep(random.uniform(2, 4))
            
            # Close the notification popup if present
            try:
                logger.info("  🔍 Checking for notification popup...")
                
                # Look for the specific close button with these classes
                close_button_selectors = [
                    "button.close-button[aria-label='Close']",
                    "button.close-button",
                    "button[aria-label='Close']",
                    "button.p-button.close-button",
                    "button[class*='close-button']"
                ]
                
                popup_closed = False
                for selector in close_button_selectors:
                    try:
                        close_button = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        if close_button.is_displayed():
                            close_button.click()
                            logger.info("  ✅ Closed notification popup")
                            popup_closed = True
                            time.sleep(1)
                            break
                    except:
                        continue
                
                if not popup_closed:
                    logger.debug("  No notification popup found (or already closed)")
                    
            except Exception as e:
                logger.debug(f"  No popup to close: {e}")
            
            # Find and fill the address search field
            try:
                # Look for various possible search input selectors
                search_input = None
                selectors = [
                    "input[name='address']",
                    "input[id*='address']",
                    "input[placeholder*='address']",
                    "input[placeholder*='Address']",
                    "input[type='text']",
                    "input[type='search']"
                ]
                
                for selector in selectors:
                    try:
                        search_input = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        if search_input.is_displayed():
                            break
                    except:
                        continue
                
                if not search_input:
                    logger.error("Could not find address search input on HPD website")
                    return None
                
                # Enter the address
                search_input.clear()
                search_input.send_keys(search_query)
                logger.info(f"  ✏️  Entered: {search_query}")
                time.sleep(1)
                
                # Submit the search (press Enter or click search button)
                search_input.send_keys(Keys.RETURN)
                
                # Wait for results to load
                logger.info("  ⏳ Waiting for search results...")
                time.sleep(random.uniform(3, 5))
                
                # Find and click the FIRST result in the search results list
                try:
                    logger.info("  🔍 Looking for search results...")
                    
                    # Look for the specific HPD result items with list-item-detail class
                    result_selectors = [
                        "div.list-item-detail",  # Primary HPD result item
                        "div[class*='list-item-detail']",
                        "div[class*='list-item']",
                        "div.MuiPaper-root",
                        "div[class*='search-result']",
                        "div[role='button']"
                    ]
                    
                    first_result = None
                    total_found = 0
                    
                    for selector in result_selectors:
                        try:
                            results = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            # Filter to only clickable, visible elements
                            clickable_results = [r for r in results if r.is_displayed() and r.is_enabled()]
                            
                            if clickable_results and len(clickable_results) > 0:
                                total_found = len(clickable_results)
                                
                                # Log the first few results to help debug
                                logger.info(f"  ✅ Found {total_found} result(s) using selector: {selector}")
                                for i, result in enumerate(clickable_results[:3]):
                                    try:
                                        # Try to find the address text inside span.list-item-title
                                        try:
                                            title_span = result.find_element(By.CSS_SELECTOR, "span.list-item-title")
                                            result_text = title_span.text if title_span else result.text[:100]
                                        except:
                                            result_text = result.text[:100] if result.text else "No text"
                                        logger.info(f"    Result #{i+1}: {result_text}")
                                    except:
                                        pass
                                
                                # Check if first result has "No text" - indicates server error
                                try:
                                    first_result_elem = clickable_results[0]
                                    try:
                                        title_span = first_result_elem.find_element(By.CSS_SELECTOR, "span.list-item-title")
                                        check_text = title_span.text if title_span else first_result_elem.text
                                    except:
                                        check_text = first_result_elem.text if first_result_elem.text else "No text"
                                    
                                    if not check_text or check_text.strip() == "" or check_text == "No text":
                                        logger.warning("  ⚠️  First result has no text (server error) - skipping this address")
                                        return None
                                except:
                                    pass
                                
                                # Select THE FIRST result
                                first_result = clickable_results[0]
                                logger.info(f"  🎯 Will click FIRST result (result #1)")
                                break
                        except Exception as e:
                            logger.debug(f"  Selector '{selector}' failed: {e}")
                            continue
                    
                    if first_result:
                        # Scroll the first result into view
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", first_result)
                        time.sleep(0.5)
                        
                        # Click the FIRST result
                        try:
                            first_result.click()
                            logger.info("  🖱️  Clicked FIRST search result")
                        except:
                            # If direct click fails, use JavaScript
                            self.driver.execute_script("arguments[0].click();", first_result)
                            logger.info("  🖱️  Clicked FIRST search result (via JavaScript)")
                        
                        # Wait for building details page to load
                        time.sleep(random.uniform(3, 5))
                    else:
                        logger.warning("  ⚠️  No search results found to click")
                        return None
                        
                except Exception as e:
                    logger.error(f"  ❌ Error clicking search result: {e}")
                    return None
                
                # Parse the results from the detail page
                building_data = self._parse_building_results(address)
                
                return building_data
                
            except Exception as e:
                logger.error(f"Error searching HPD website: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error in HPD search: {e}")
            return None
    
    def _parse_building_results(self, original_address: Address) -> Optional[HPDBuilding]:
        """
        Parse building information and B units from HPD search results.
        
        Args:
            original_address: Original search address
            
        Returns:
            HPDBuilding object or None
        """
        try:
            # Wait for building details page to load
            time.sleep(2)
            
            # Get page source for text-based extraction
            page_text = self.driver.page_source
            
            # Look for B UNITS section specifically
            # <div class="card-content-top fs-sm">B UNITS</div>
            try:
                b_units_header = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'card-content-top') and contains(text(), 'B UNITS')]")
                if b_units_header:
                    logger.info(f"  ✅ Found 'B UNITS' section on page")
                else:
                    logger.info(f"  ℹ️  No 'B UNITS' section found on page")
            except:
                logger.debug("  Could not check for B UNITS section")
            
            # Look for total units
            total_units = self._extract_total_units(page_text)
            
            # Look for B units using updated logic
            b_units = self._extract_b_units_from_page()
            
            # Extract BIN, BBL if available
            bin_number = self._extract_field(page_text, ['BIN', 'Building ID', 'Building Identification Number'])
            bbl = self._extract_field(page_text, ['BBL', 'Borough Block Lot'])
            building_id = self._extract_field(page_text, ['Building ID', 'HPD Building ID'])
            
            building = HPDBuilding(
                building_id=building_id,
                bin=bin_number,
                bbl=bbl,
                address=original_address,
                total_units=total_units,
                residential_units=total_units,
                b_units=b_units,
                has_b_units=len(b_units) > 0,
                building_class=None
            )
            
            logger.info(f"✅ Found HPD building: {total_units} total units, {len(b_units)} B units")
            
            return building
            
        except Exception as e:
            logger.error(f"Error parsing HPD results: {e}")
            return None
    
    def _extract_total_units(self, page_text: str) -> int:
        """Extract total number of units from page."""
        import re
        
        # Look for patterns like "Total Units: 10" or "10 units"
        patterns = [
            r'total\s+units?\s*:?\s*(\d+)',
            r'(\d+)\s+total\s+units?',
            r'number\s+of\s+units?\s*:?\s*(\d+)',
            r'units?\s*:?\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        logger.debug("Could not extract total units count")
        return 0
    
    def _extract_b_units_from_page(self) -> List[HPDBUnit]:
        """Extract B units count from the current page using Selenium."""
        b_units = []
        
        try:
            # Look for the B UNITS field value
            # The page shows it as: B UNITS with a numeric value below it
            try:
                # Find elements containing "B UNITS" text
                b_units_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'B UNITS')]")
                
                if b_units_elements:
                    logger.info(f"  ✅ Found 'B UNITS' field on page")
                    
                    # Try to find the value (usually in a sibling or nearby element)
                    for elem in b_units_elements:
                        try:
                            # Get parent element and look for the value
                            parent = elem.find_element(By.XPATH, "..")
                            
                            # Look for numeric value in parent or nearby elements
                            value_elements = parent.find_elements(By.XPATH, ".//*")
                            for val_elem in value_elements:
                                text = val_elem.text.strip()
                                if text.isdigit():
                                    b_unit_count = int(text)
                                    logger.info(f"  📊 B UNITS count: {b_unit_count}")
                                    
                                    # Create B unit objects based on count
                                    for i in range(b_unit_count):
                                        b_unit = HPDBUnit(
                                            unit_number=f"B{i+1}",
                                            unit_type='Basement',
                                            is_b_unit=True
                                        )
                                        b_units.append(b_unit)
                                        logger.debug(f"    Added B unit: B{i+1}")
                                    
                                    return b_units
                        except:
                            continue
                else:
                    logger.info(f"  ℹ️  No 'B UNITS' field found on page")
            
            except Exception as e:
                logger.debug(f"  Error finding B UNITS field: {e}")
            
            # Fallback: search page source for pattern like "B UNITS" followed by a number
            import re
            page_text = self.driver.page_source
            
            # Look for "B UNITS" followed by a number
            pattern = r'B\s+UNITS[^\d]*(\d+)'
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                b_unit_count = int(match.group(1))
                logger.info(f"  📊 B UNITS count (from text): {b_unit_count}")
                
                for i in range(b_unit_count):
                    b_unit = HPDBUnit(
                        unit_number=f"B{i+1}",
                        unit_type='Basement',
                        is_b_unit=True
                    )
                    b_units.append(b_unit)
            
            logger.info(f"  📊 Total B units extracted: {len(b_units)}")
            return b_units
            
        except Exception as e:
            logger.error(f"  ❌ Error extracting B units from page: {e}")
            return []
    
    def _extract_b_units(self, page_text: str) -> List[HPDBUnit]:
        """Extract B units from page."""
        import re
        b_units = []
        
        # Look for apartment/unit listings
        # Pattern for apartment numbers like "B1", "B2", "BSMT", "BASEMENT 1", etc.
        patterns = [
            r'(?:apartment|apt|unit)\s*#?\s*:?\s*(B\w*|BSMT\w*|BASEMENT\w*)',
            r'(B\d+|BSMT\d*|BASEMENT\s*\d*)',
        ]
        
        found_units = set()
        for pattern in patterns:
            matches = re.finditer(pattern, page_text, re.IGNORECASE)
            for match in matches:
                unit_number = match.group(1).strip()
                if unit_number and unit_number not in found_units:
                    found_units.add(unit_number)
                    b_unit = HPDBUnit(
                        unit_number=unit_number,
                        unit_type='Basement',
                        is_b_unit=True
                    )
                    b_units.append(b_unit)
        
        logger.debug(f"Extracted {len(b_units)} B units from page")
        return b_units
    
    def _extract_field(self, page_text: str, field_names: List[str]) -> Optional[str]:
        """Extract a field value by searching for field names."""
        import re
        
        for field_name in field_names:
            pattern = rf'{field_name}\s*:?\s*([A-Z0-9\-]+)'
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def batch_search(self, addresses: List[Address]) -> List[Optional[HPDBuilding]]:
        """
        Search for multiple buildings.
        
        Args:
            addresses: List of Address objects
            
        Returns:
            List of HPDBuilding objects (None for not found)
        """
        results = []
        
        try:
            self._setup_driver()
            
            for i, address in enumerate(addresses):
                logger.info(f"Searching HPD {i+1}/{len(addresses)}: {address.street}")
                
                building = self.search_by_address(address)
                results.append(building)
                
                # Random delay between searches
                if i < len(addresses) - 1:
                    time.sleep(random.uniform(2, 4))
            
        finally:
            self._close_driver()
        
        return results
