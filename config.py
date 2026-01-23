"""
Configuration management for the real estate scraping system.
"""
import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class ZillowConfig(BaseModel):
    """Zillow scraper configuration."""
    base_url: str = Field(default="https://www.zillow.com")
    # Multiple locations to scrape: Manhattan, Brooklyn, Bronx, Queens
    locations: list[dict] = Field(default=[
        {"name": "Manhattan", "search_location": "Manhattan, NY", "region_id": 12530},
        {"name": "Brooklyn", "search_location": "Brooklyn, NY", "region_id": 37607},
        {"name": "Bronx", "search_location": "Bronx, NY", "region_id": 28779},
        {"name": "Queens", "search_location": "Queens, NY", "region_id": 270915}
    ])
    max_pages: int = Field(default=1)  # Number of pages to scrape per location (1 for testing)    

class HPDConfig(BaseModel):
    """HPD API configuration."""
    api_base_url: str = Field(default="https://data.cityofnewyork.us/resource/")
    app_token: Optional[str] = Field(default=None)
    buildings_endpoint: str = Field(default="evjd-dqpz.json")  # HPD Building Records
    registrations_endpoint: str = Field(default="tesw-yqqr.json")  # HPD Registrations


class ScrapingConfig(BaseModel):
    """General scraping settings."""
    request_delay: int = Field(default=2)
    max_retries: int = Field(default=3)
    timeout: int = Field(default=30)
    user_agent: str = Field(
        default="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    )


class FilterCriteria(BaseModel):
    """Investment criteria for filtering properties."""
    min_price: float = Field(default=0)
    max_price: float = Field(default=2500000)
    min_bedrooms: int = Field(default=5)
    min_bathrooms: float = Field(default=4.0)
    min_units: int = Field(default=2)
    require_b_units: bool = Field(default=True)
    boroughs: Optional[list[str]] = Field(default=["Manhattan", "Brooklyn", "Bronx", "Queens"])
    property_types: Optional[list[str]] = Field(default=["Multi Family", "Multifamily", "Duplex"])


class OutputConfig(BaseModel):
    """Output settings."""
    output_dir: str = Field(default="./output")
    output_formats: list[str] = Field(default=["csv", "excel"])


class Config:
    """Main configuration class."""
    
    def __init__(self):
        # Load locations from environment or use defaults
        default_locations = [
            {"name": "Manhattan", "search_location": "Manhattan, NY", "region_id": 12530},
            {"name": "Brooklyn", "search_location": "Brooklyn, NY", "region_id": 37607},
            {"name": "Bronx", "search_location": "Bronx, NY", "region_id": 28779},
            {"name": "Queens", "search_location": "Queens, NY", "region_id": 270915}
        ]
        
        self.zillow = ZillowConfig(
            base_url=os.getenv("ZILLOW_BASE_URL", "https://www.zillow.com"),
            locations=default_locations,
            max_pages=int(os.getenv("ZILLOW_MAX_PAGES", "1"))  # Default to 1 page per location
        )
        
        self.hpd = HPDConfig(
            api_base_url=os.getenv("HPD_API_BASE_URL", "https://data.cityofnewyork.us/resource/"),
            app_token=os.getenv("HPD_APP_TOKEN")
        )
        
        self.scraping = ScrapingConfig(
            request_delay=int(os.getenv("REQUEST_DELAY", "2")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            timeout=int(os.getenv("TIMEOUT", "30"))
        )
        
        boroughs_str = os.getenv("BOROUGHS", "Manhattan,Brooklyn,Bronx,Queens")
        boroughs = [b.strip() for b in boroughs_str.split(",")] if boroughs_str else None
        
        property_types_str = os.getenv("PROPERTY_TYPES", "Multi Family,Multifamily")
        property_types = [pt.strip() for pt in property_types_str.split(",")] if property_types_str else None
        
        self.filters = FilterCriteria(
            min_price=float(os.getenv("MIN_PRICE", "0")),
            max_price=float(os.getenv("MAX_PRICE", "2500000")),
            min_bedrooms=int(os.getenv("MIN_BEDROOMS", "5")),
            min_bathrooms=float(os.getenv("MIN_BATHROOMS", "4.0")),
            min_units=int(os.getenv("MIN_UNITS", "2")),
            require_b_units=os.getenv("REQUIRE_B_UNITS", "true").lower() == "true",
            boroughs=boroughs,
            property_types=property_types
        )
        
        self.output = OutputConfig(
            output_dir=os.getenv("OUTPUT_DIR", "./output"),
            output_formats=os.getenv("OUTPUT_FORMAT", "csv,excel").split(",")
        )


# Global config instance
config = Config()
