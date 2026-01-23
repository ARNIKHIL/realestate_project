"""
Property filtering based on investment criteria.
"""
from typing import List
from models import EnrichedProperty
from config import config
from utils.logger import logger


class PropertyFilter:
    """Filters properties based on investment criteria."""
    
    def __init__(self):
        self.criteria = config.filters
        
    def meets_price_criteria(self, property: EnrichedProperty) -> bool:
        """Check if property meets price criteria."""
        if property.zillow_data.price is None:
            return False
        
        return (
            self.criteria.min_price <= property.zillow_data.price <= self.criteria.max_price
        )
    
    def meets_bedroom_criteria(self, property: EnrichedProperty) -> bool:
        """Check if property meets minimum bedroom requirement."""
        if property.zillow_data.bedrooms is None:
            return False
        
        return property.zillow_data.bedrooms >= self.criteria.min_bedrooms
    
    def meets_bathroom_criteria(self, property: EnrichedProperty) -> bool:
        """Check if property meets minimum bathroom requirement."""
        if property.zillow_data.bathrooms is None:
            return False
        
        return property.zillow_data.bathrooms >= self.criteria.min_bathrooms
    
    def meets_unit_criteria(self, property: EnrichedProperty) -> bool:
        """Check if property meets minimum unit requirement."""
        if not property.hpd_match_found:
            # If no HPD data, we can't verify units
            return False
        
        return property.total_units >= self.criteria.min_units
    
    def has_required_b_units(self, property: EnrichedProperty) -> bool:
        """Check if property has B units (if required)."""
        if not self.criteria.require_b_units:
            return True
        
        return property.has_b_units
    
    def meets_borough_criteria(self, property: EnrichedProperty) -> bool:
        """Check if property is in desired boroughs."""
        if not self.criteria.boroughs:
            # No specific borough requirement
            return True
        
        borough = property.zillow_data.address.borough
        if not borough:
            return False
        
        return borough in self.criteria.boroughs
    
    def meets_property_type_criteria(self, property: EnrichedProperty) -> bool:
        """Check if property type is acceptable."""
        if not self.criteria.property_types:
            # No specific property type requirement
            return True
        
        property_type = property.zillow_data.property_type
        if not property_type:
            return False
        
        # Case-insensitive matching
        property_type_lower = property_type.lower()
        return any(
            pt.lower() in property_type_lower
            for pt in self.criteria.property_types
        )
    
    def calculate_investment_score(self, property: EnrichedProperty) -> float:
        """
        Calculate an investment score for the property.
        
        Score factors:
        - Has B units: +30 points
        - Number of B units: +10 points per unit (max 30)
        - Total units: +5 points per unit (max 25)
        - Price per unit: lower is better (max 15 points)
        - Days on market: fewer is better (max 10 points)
        
        Returns:
            Score from 0-100
        """
        score = 0.0
        
        # B units presence
        if property.has_b_units:
            score += 30
        
        # Number of B units
        b_unit_score = min(property.b_unit_count * 10, 30)
        score += b_unit_score
        
        # Total units (more units = more cash flow potential)
        if property.total_units > 0:
            unit_score = min(property.total_units * 5, 25)
            score += unit_score
        
        # Price per unit (lower is better)
        if property.zillow_data.price and property.total_units > 0:
            price_per_unit = property.zillow_data.price / property.total_units
            
            # Assume $100k per unit is good, scale accordingly
            if price_per_unit <= 100000:
                score += 15
            elif price_per_unit <= 150000:
                score += 10
            elif price_per_unit <= 200000:
                score += 5
        
        # Days on market (newer listings get higher scores)
        if property.zillow_data.days_on_market is not None:
            if property.zillow_data.days_on_market <= 7:
                score += 10
            elif property.zillow_data.days_on_market <= 14:
                score += 7
            elif property.zillow_data.days_on_market <= 30:
                score += 5
        
        return min(score, 100)  # Cap at 100
    
    def filter_properties(self, properties: List[EnrichedProperty]) -> List[EnrichedProperty]:
        """
        Filter properties based on all criteria and calculate scores.
        
        Args:
            properties: List of EnrichedProperty objects
            
        Returns:
            Filtered list of properties that meet criteria, sorted by score
        """
        filtered = []
        
        for property in properties:
            # Check all criteria
            passes_all = (
                self.meets_price_criteria(property) and
                self.meets_bedroom_criteria(property) and
                self.meets_bathroom_criteria(property) and
                self.meets_unit_criteria(property) and
                self.has_required_b_units(property) and
                self.meets_borough_criteria(property) and
                self.meets_property_type_criteria(property)
            )
            
            if passes_all:
                property.meets_criteria = True
                
                # Calculate investment score
                score = self.calculate_investment_score(property)
                
                # Store score in notes for now
                property.notes = f"Investment Score: {score:.1f}/100"
                
                filtered.append(property)
                
                logger.debug(
                    f"Property passed filters: {property.zillow_data.address.street} "
                    f"(Score: {score:.1f})"
                )
        
        # Sort by investment score (highest first)
        filtered.sort(
            key=lambda p: float(p.notes.split(': ')[1].split('/')[0]) if p.notes else 0,
            reverse=True
        )
        
        logger.info(
            f"Filtered {len(filtered)}/{len(properties)} properties that meet criteria"
        )
        
        return filtered
    
    def get_filter_summary(self) -> dict:
        """Get a summary of current filter criteria."""
        return {
            "price_range": f"${self.criteria.min_price:,.0f} - ${self.criteria.max_price:,.0f}",
            "min_bedrooms": self.criteria.min_bedrooms,
            "min_bathrooms": self.criteria.min_bathrooms,
            "min_units": self.criteria.min_units,
            "require_b_units": self.criteria.require_b_units,
            "boroughs": ", ".join(self.criteria.boroughs) if self.criteria.boroughs else "Any",
            "property_types": ", ".join(self.criteria.property_types) if self.criteria.property_types else "Any"
        }
