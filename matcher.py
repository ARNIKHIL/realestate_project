"""
Property matcher - cross-checks Zillow listings with HPD database.
"""
import asyncio
from typing import List
from fuzzywuzzy import fuzz

from models import ZillowProperty, HPDBuilding, EnrichedProperty, Address
from scrapers.hpd_scraper import HPDScraper
from hpd_cache import HPDCache
from utils.logger import logger


class PropertyMatcher:
    """Matches Zillow properties with HPD building records."""
    
    def __init__(self):
        self.hpd_scraper = HPDScraper()
        self.hpd_cache = HPDCache()
        self.match_threshold = 80  # Fuzzy matching threshold
        self.new_hpd_data = {}  # Track newly scraped data for cache
        
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass
    
    def _normalize_address(self, address: Address) -> str:
        """Normalize address for comparison."""
        street = address.street.upper().strip()
        
        # Remove common abbreviations and standardize
        replacements = {
            'STREET': 'ST',
            'AVENUE': 'AVE',
            'ROAD': 'RD',
            'BOULEVARD': 'BLVD',
            'DRIVE': 'DR',
            'LANE': 'LN',
            'PLACE': 'PL',
            'EAST': 'E',
            'WEST': 'W',
            'NORTH': 'N',
            'SOUTH': 'S',
        }
        
        for old, new in replacements.items():
            street = street.replace(old, new)
        
        # Remove extra spaces
        street = ' '.join(street.split())
        
        return street
    
    def _calculate_address_similarity(self, addr1: Address, addr2: Address) -> float:
        """
        Calculate similarity score between two addresses.
        
        Returns:
            Similarity score (0-100)
        """
        norm1 = self._normalize_address(addr1)
        norm2 = self._normalize_address(addr2)
        
        # Use fuzzy string matching
        similarity = fuzz.ratio(norm1, norm2)
        
        # Boost score if boroughs match
        if addr1.borough and addr2.borough:
            if addr1.borough.upper() == addr2.borough.upper():
                similarity = min(100, similarity + 10)
        
        # Boost score if zip codes match
        if addr1.zip_code and addr2.zip_code:
            if addr1.zip_code == addr2.zip_code:
                similarity = min(100, similarity + 10)
        
        return similarity
    
    async def match_property(self, zillow_property: ZillowProperty) -> EnrichedProperty:
        """
        Match a single Zillow property with HPD data.
        
        Args:
            zillow_property: ZillowProperty object
            
        Returns:
            EnrichedProperty with HPD data (if found)
        """
        enriched = EnrichedProperty(
            zillow_data=zillow_property,
            hpd_match_found=False
        )
        
        try:
            # Log the address being searched
            address_str = f"{zillow_property.address.street}, {zillow_property.address.borough or 'Brooklyn'}, NY"
            logger.info(f"🔍 Searching HPD for: {address_str}")
            
            # FIRST: Check cache
            cached_building = self.hpd_cache.get_cached_hpd_data(zillow_property.address)
            
            if cached_building:
                hpd_building = cached_building
                logger.info(f"  💾 Using cached HPD data")
            else:
                # NOT in cache - scrape HPD website
                logger.info(f"  🌐 Not in cache, scraping HPD website...")
                hpd_building = self.hpd_scraper.search_by_address(zillow_property.address)
                
                # Save to new_hpd_data for caching later (only if valid data returned)
                if hpd_building:
                    self.new_hpd_data[address_str] = hpd_building
                else:
                    logger.info(f"  ⏭️  Skipping address (no valid HPD data) - will not be cached")
            
            if hpd_building:
                # Verify address match quality
                similarity = self._calculate_address_similarity(
                    zillow_property.address,
                    hpd_building.address
                )
                
                if similarity >= self.match_threshold:
                    enriched.hpd_data = hpd_building
                    enriched.hpd_match_found = True
                    enriched.has_b_units = hpd_building.has_b_units
                    enriched.b_unit_count = len(hpd_building.b_units)
                    enriched.total_units = hpd_building.total_units
                    
                    # Set match confidence
                    if similarity >= 95:
                        enriched.match_confidence = "High"
                    elif similarity >= 85:
                        enriched.match_confidence = "Medium"
                    else:
                        enriched.match_confidence = "Low"
                    
                    logger.info(
                        f"Matched property: {zillow_property.address.street} "
                        f"(Confidence: {enriched.match_confidence}, "
                        f"B units: {enriched.b_unit_count})"
                    )
                else:
                    logger.debug(
                        f"Address similarity too low ({similarity}%) for: "
                        f"{zillow_property.address.street}"
                    )
            else:
                logger.debug(f"No HPD match found for: {zillow_property.address.street}")
                
        except Exception as e:
            logger.error(f"Error matching property: {e}")
        
        return enriched
    
    async def match_properties_batch(
        self,
        zillow_properties: List[ZillowProperty],
        batch_size: int = 10
    ) -> List[EnrichedProperty]:
        """
        Match multiple properties in batches.
        
        Args:
            zillow_properties: List of ZillowProperty objects
            batch_size: Number of concurrent requests
            
        Returns:
            List of EnrichedProperty objects
        """
        enriched_properties = []
        
        logger.info(f"Matching {len(zillow_properties)} properties with HPD database")
        
        # Process in batches to avoid overwhelming the API
        for i in range(0, len(zillow_properties), batch_size):
            batch = zillow_properties[i:i + batch_size]
            
            logger.info(f"Processing batch {i // batch_size + 1}/{(len(zillow_properties) + batch_size - 1) // batch_size}")
            
            # Match properties in parallel within batch
            tasks = [self.match_property(prop) for prop in batch]
            results = await asyncio.gather(*tasks)
            
            enriched_properties.extend(results)
            
            # Small delay between batches
            if i + batch_size < len(zillow_properties):
                await asyncio.sleep(1)
        
        # Save enriched properties (with Zillow + HPD data) to master cache
        # Only save properties that were newly scraped (not from cache)
        new_enriched = [p for p in enriched_properties if p.hpd_match_found and 
                        f"{p.zillow_data.address.street}, {p.zillow_data.address.borough or 'Brooklyn'}, NY" in self.new_hpd_data]
        
        if new_enriched:
            logger.info(f"\n💾 Saving {len(new_enriched)} new addresses to master cache (with Zillow + HPD data)...")
            self.hpd_cache.save_to_cache(new_enriched)
        else:
            logger.info("\n💾 No new data to cache (all addresses were in cache)")
        
        # Log summary
        matched_count = sum(1 for p in enriched_properties if p.hpd_match_found)
        b_unit_count = sum(1 for p in enriched_properties if p.has_b_units)
        
        logger.info(
            f"Matching complete: {matched_count}/{len(zillow_properties)} matched, "
            f"{b_unit_count} with B units"
        )
        
        return enriched_properties
