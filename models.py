"""
Data models for property information.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class Address(BaseModel):
    """Property address information."""
    street: str
    city: str
    state: str
    zip_code: Optional[str] = None
    borough: Optional[str] = None
    
    def __str__(self):
        return f"{self.street}, {self.city}, {self.state} {self.zip_code or ''}".strip()


class ZillowProperty(BaseModel):
    """Zillow property listing data."""
    zpid: Optional[str] = None  # Zillow Property ID
    address: Address
    price: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    lot_size: Optional[int] = None  # in square feet
    year_built: Optional[int] = None
    property_type: Optional[str] = None
    listing_status: str = "For Sale"
    days_on_market: Optional[int] = None
    url: Optional[str] = None
    listing_date: Optional[datetime] = None
    description: Optional[str] = None
    scraped_at: datetime = Field(default_factory=datetime.now)


class HPDBUnit(BaseModel):
    """HPD Building unit information."""
    unit_number: Optional[str] = None
    unit_type: Optional[str] = None  # Will check for 'B' classification
    is_b_unit: bool = False
    

class HPDBuilding(BaseModel):
    """HPD building record."""
    building_id: Optional[str] = None
    bin: Optional[str] = None  # Building Identification Number
    bbl: Optional[str] = None  # Borough-Block-Lot
    address: Address
    total_units: int = 0
    residential_units: int = 0
    b_units: List[HPDBUnit] = Field(default_factory=list)
    has_b_units: bool = False
    building_class: Optional[str] = None
    registration_id: Optional[str] = None
    last_registration_date: Optional[datetime] = None
    landlord_name: Optional[str] = None
    landlord_address: Optional[str] = None
    

class EnrichedProperty(BaseModel):
    """Combined property data from Zillow and HPD."""
    # Zillow data
    zillow_data: ZillowProperty
    
    # HPD data
    hpd_data: Optional[HPDBuilding] = None
    hpd_match_found: bool = False
    
    # Analysis
    has_b_units: bool = False
    b_unit_count: int = 0
    total_units: int = 0
    meets_criteria: bool = False
    
    # Metadata
    processed_at: datetime = Field(default_factory=datetime.now)
    match_confidence: Optional[str] = None  # "High", "Medium", "Low"
    notes: Optional[str] = None
    
    def calculate_metrics(self):
        """Calculate investment metrics."""
        if self.hpd_data:
            self.has_b_units = self.hpd_data.has_b_units
            self.b_unit_count = len(self.hpd_data.b_units)
            self.total_units = self.hpd_data.total_units
