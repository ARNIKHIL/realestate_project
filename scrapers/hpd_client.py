"""
NYC HPD (Housing Preservation & Development) API client.

This module interacts with NYC Open Data API to retrieve building information
and identify properties with B units (basement units).
"""
import aiohttp
import asyncio
from typing import List, Optional, Dict
from datetime import datetime
from urllib.parse import urlencode

from models import HPDBuilding, HPDBUnit, Address
from config import config
from utils.logger import logger


class HPDClient:
    """Client for NYC HPD Open Data API."""
    
    def __init__(self):
        self.config = config.hpd
        self.scraping_config = config.scraping
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self._init_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._close_session()
        
    async def _init_session(self):
        """Initialize aiohttp session."""
        headers = {
            'User-Agent': self.scraping_config.user_agent,
        }
        if self.config.app_token:
            headers['X-App-Token'] = self.config.app_token
            
        timeout = aiohttp.ClientTimeout(total=self.scraping_config.timeout)
        self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        logger.info("HPD API session initialized")
    
    async def _close_session(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            logger.info("HPD API session closed")
    
    def _build_api_url(self, endpoint: str, params: Dict) -> str:
        """Build API URL with parameters."""
        base_url = f"{self.config.api_base_url}{endpoint}"
        if params:
            query_string = urlencode(params)
            return f"{base_url}?{query_string}"
        return base_url
    
    async def search_by_address(self, address: Address) -> Optional[HPDBuilding]:
        """
        Search HPD database for a building by address.
        
        Args:
            address: Address object
            
        Returns:
            HPDBuilding object if found, None otherwise
        """
        try:
            # Clean address for API query
            street = address.street.upper().strip()
            
            # Query HPD Building dataset
            params = {
                "$where": f"upper(housenumber) || ' ' || upper(streetname) LIKE '%{street}%'",
                "$limit": 10
            }
            
            url = self._build_api_url(self.config.buildings_endpoint, params)
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data and len(data) > 0:
                        # Take the first match
                        building_data = data[0]
                        return await self._parse_building_data(building_data, address)
                    else:
                        logger.debug(f"No HPD data found for address: {address}")
                        return None
                else:
                    logger.error(f"HPD API error: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error searching HPD by address: {e}")
            return None
    
    async def search_by_bin(self, bin_number: str) -> Optional[HPDBuilding]:
        """
        Search HPD database by BIN (Building Identification Number).
        
        Args:
            bin_number: NYC Building Identification Number
            
        Returns:
            HPDBuilding object if found, None otherwise
        """
        try:
            params = {
                "bin": bin_number,
                "$limit": 1
            }
            
            url = self._build_api_url(self.config.buildings_endpoint, params)
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data and len(data) > 0:
                        return await self._parse_building_data(data[0])
                    else:
                        logger.debug(f"No HPD data found for BIN: {bin_number}")
                        return None
                else:
                    logger.error(f"HPD API error: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error searching HPD by BIN: {e}")
            return None
    
    async def get_registration_info(self, building_id: str) -> Optional[Dict]:
        """
        Get registration information for a building.
        
        Args:
            building_id: HPD Building ID
            
        Returns:
            Registration data dictionary
        """
        try:
            params = {
                "buildingid": building_id,
                "$order": "lastregistrationdate DESC",
                "$limit": 1
            }
            
            url = self._build_api_url(self.config.registrations_endpoint, params)
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data[0] if data else None
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting registration info: {e}")
            return None
    
    async def _parse_building_data(self, data: Dict, original_address: Optional[Address] = None) -> HPDBuilding:
        """
        Parse HPD building data into HPDBuilding object.
        
        Args:
            data: Raw building data from API
            original_address: Original search address (if available)
            
        Returns:
            HPDBuilding object
        """
        # Extract address
        house_number = data.get('housenumber', '')
        street_name = data.get('streetname', '')
        zip_code = data.get('zip', '')
        borough_name = self._get_borough_name(data.get('boroid', ''))
        
        address = Address(
            street=f"{house_number} {street_name}".strip(),
            city="New York",
            state="NY",
            zip_code=zip_code,
            borough=borough_name
        )
        
        # If we have the original address, use it for better consistency
        if original_address:
            address = original_address
        
        building_id = data.get('buildingid')
        bin_number = data.get('bin')
        bbl = data.get('bbl')  # Borough-Block-Lot
        building_class = data.get('buildingclass')
        
        # Get registration info if building_id exists
        registration_data = None
        if building_id:
            registration_data = await self.get_registration_info(building_id)
        
        # Parse unit information to identify B units
        b_units = await self._identify_b_units(building_id or bin_number)
        
        # Calculate total units
        total_units = int(data.get('numberofdwellings', 0))
        residential_units = int(data.get('residentialunits', total_units))
        
        building = HPDBuilding(
            building_id=building_id,
            bin=bin_number,
            bbl=bbl,
            address=address,
            total_units=total_units,
            residential_units=residential_units,
            b_units=b_units,
            has_b_units=len(b_units) > 0,
            building_class=building_class
        )
        
        # Add registration info if available
        if registration_data:
            building.registration_id = registration_data.get('registrationid')
            
            last_reg_date = registration_data.get('lastregistrationdate')
            if last_reg_date:
                try:
                    building.last_registration_date = datetime.fromisoformat(last_reg_date.replace('Z', '+00:00'))
                except:
                    pass
            
            building.landlord_name = registration_data.get('corporationname') or registration_data.get('ownername')
            
        logger.debug(f"Parsed HPD building: {address}, {total_units} units, {len(b_units)} B units, BBL: {building.bbl}, Class: {building.building_class}")
        return building
    
    async def _identify_b_units(self, building_identifier: str) -> List[HPDBUnit]:
        """
        Identify B units (basement units) in a building.
        
        This searches for units with 'B' classification or basement designation.
        
        Args:
            building_identifier: Building ID or BIN
            
        Returns:
            List of HPDBUnit objects that are B units
        """
        b_units = []
        
        try:
            # Query the HPD Multiple Dwelling Registrations dataset
            # This dataset contains unit-level information
            params = {
                "$where": f"buildingid='{building_identifier}' AND (upper(apartment) LIKE 'B%' OR upper(apartment) LIKE '%BSMT%' OR upper(apartment) LIKE '%BASEMENT%')",
                "$limit": 100
            }
            
            # Note: Adjust endpoint based on actual HPD dataset structure
            # The registrations contact endpoint might have unit info
            url = self._build_api_url("feu5-ztfk.json", params)  # Registration contacts dataset
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for unit_data in data:
                        apartment = unit_data.get('apartment', '')
                        
                        # Check if it's a B unit
                        is_b = (
                            apartment.upper().startswith('B') or
                            'BSMT' in apartment.upper() or
                            'BASEMENT' in apartment.upper()
                        )
                        
                        if is_b:
                            unit = HPDBUnit(
                                unit_number=apartment,
                                unit_type='Basement',
                                is_b_unit=True
                            )
                            b_units.append(unit)
                    
                    logger.debug(f"Found {len(b_units)} B units for building {building_identifier}")
        
        except Exception as e:
            logger.error(f"Error identifying B units: {e}")
        
        return b_units
    
    def _get_borough_name(self, boro_id: str) -> Optional[str]:
        """Convert borough ID to borough name."""
        borough_map = {
            '1': 'Manhattan',
            '2': 'Bronx',
            '3': 'Brooklyn',
            '4': 'Queens',
            '5': 'Staten Island'
        }
        return borough_map.get(str(boro_id))
    
    async def batch_search(self, addresses: List[Address]) -> List[Optional[HPDBuilding]]:
        """
        Search for multiple buildings in batch.
        
        Args:
            addresses: List of Address objects
            
        Returns:
            List of HPDBuilding objects (None for not found)
        """
        tasks = [self.search_by_address(addr) for addr in addresses]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        buildings = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error searching address {addresses[i]}: {result}")
                buildings.append(None)
            else:
                buildings.append(result)
        
        return buildings
