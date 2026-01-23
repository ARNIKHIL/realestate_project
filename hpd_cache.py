"""
HPD data caching system to avoid re-scraping addresses.
"""
import pandas as pd
from pathlib import Path
from typing import Optional, Dict
from models import Address, HPDBuilding, HPDBUnit
from utils.logger import logger


class HPDCache:
    """Manages cached HPD data to avoid redundant scraping."""
    
    def __init__(self, cache_file: str = "./output/master_hpd_data.xlsx"):
        self.cache_file = Path(cache_file)
        self.cache_data: Dict[str, dict] = {}
        self._load_cache()
    
    def _normalize_address(self, address: Address) -> str:
        """Normalize address for consistent lookup."""
        # Create a normalized key: "STREET, BOROUGH"
        street = address.street.upper().strip()
        borough = (address.borough or "BROOKLYN").upper().strip()
        return f"{street}, {borough}"
    
    def _load_cache(self):
        """Load existing HPD data from Excel cache."""
        if not self.cache_file.exists():
            logger.info(f"📂 No HPD cache found at {self.cache_file}")
            logger.info("   Will create new cache after scraping")
            return
        
        try:
            df = pd.read_excel(self.cache_file)
            logger.info(f"📂 Loaded HPD cache: {len(df)} addresses found")
            
            # Convert DataFrame to dict keyed by normalized address
            for _, row in df.iterrows():
                key = f"{row['Street'].upper()}, {row['Borough'].upper()}"
                self.cache_data[key] = row.to_dict()
            
            logger.info(f"✅ HPD cache loaded: {len(self.cache_data)} addresses ready")
            
        except Exception as e:
            logger.warning(f"⚠️  Could not load HPD cache: {e}")
            logger.info("   Will create new cache")
    
    def get_cached_hpd_data(self, address: Address) -> Optional[HPDBuilding]:
        """
        Get cached HPD data for an address.
        
        Args:
            address: Address to lookup
            
        Returns:
            HPDBuilding if found in cache, None otherwise
        """
        key = self._normalize_address(address)
        
        if key not in self.cache_data:
            return None
        
        row = self.cache_data[key]
        logger.info(f"  💾 Found in cache: {address.street}")
        
        # Reconstruct HPDBuilding from cached row
        try:
            # Parse B units from cached data
            b_units = []
            b_unit_count = row.get('B Unit Count', 0)
            if b_unit_count and b_unit_count > 0:
                for i in range(int(b_unit_count)):
                    b_unit = HPDBUnit(
                        unit_number=f"B{i+1}",
                        unit_type='Basement',
                        is_b_unit=True
                    )
                    b_units.append(b_unit)
            
            building = HPDBuilding(
                building_id=str(row.get('Building ID', '')),
                bin=str(row.get('BIN', '')),
                bbl=str(row.get('BBL', '')),
                address=address,
                total_units=int(row.get('Total Units', 0)) if pd.notna(row.get('Total Units')) else 0,
                residential_units=int(row.get('Total Units', 0)) if pd.notna(row.get('Total Units')) else 0,
                b_units=b_units,
                has_b_units=len(b_units) > 0,
                building_class=str(row.get('Building Class', '')) if pd.notna(row.get('Building Class')) else None
            )
            
            return building
            
        except Exception as e:
            logger.warning(f"  ⚠️  Error reconstructing cached data: {e}")
            return None
    
    def save_to_cache(self, enriched_properties: list):
        """
        Save enriched property data (Zillow + HPD) to cache Excel file.
        
        Args:
            enriched_properties: List of EnrichedProperty objects with both Zillow and HPD data
        """
        if not enriched_properties:
            logger.info("No new data to save to cache")
            return
        
        # Merge with existing cache
        new_data = []
        
        # Add existing cache data
        for key, row_dict in self.cache_data.items():
            new_data.append(row_dict)
        
        # Add new scraped data
        for prop in enriched_properties:
            # Only save properties that have HPD data
            if not prop.hpd_match_found or not prop.hpd_data:
                continue
                
            key = self._normalize_address(prop.zillow_data.address)
            
            # Skip if already in cache
            if key in self.cache_data:
                continue
            
            zillow = prop.zillow_data
            building = prop.hpd_data
            
            row = {
                # Zillow data
                'Street': zillow.address.street,
                'Borough': zillow.address.borough or 'Brooklyn',
                'Zillow Price': zillow.price,
                'Bedrooms': zillow.bedrooms,
                'Bathrooms': zillow.bathrooms,
                'Zillow URL': zillow.url or 'N/A',
                
                # HPD data
                'B Unit Count': len(building.b_units),
                'Has B Units': 'Yes' if building.has_b_units else 'No',
                'B Unit Numbers': ', '.join([f"B{b.unit_number}" for b in building.b_units]) if building.b_units else 'N/A',
                
                # Match metadata
                'Match Confidence': prop.match_confidence or 'N/A',
                'Scraped Date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            new_data.append(row)
            self.cache_data[key] = row
        
        # Save to Excel
        try:
            df = pd.DataFrame(new_data)
            
            # Ensure output directory exists
            self.cache_file.parent.mkdir(exist_ok=True, parents=True)
            
            df.to_excel(self.cache_file, index=False)
            logger.info(f"💾 Saved HPD cache: {len(df)} total addresses")
            logger.info(f"   Cache file: {self.cache_file}")
            
        except Exception as e:
            logger.error(f"❌ Error saving HPD cache: {e}")
