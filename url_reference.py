"""
URL Builder Reference - Shows how Zillow search URLs are constructed
"""

def show_url_structure():
    """Display the Zillow URL structure with filters."""
    
    print("=" * 70)
    print("ZILLOW SEARCH URL STRUCTURE - BROOKLYN MULTI-FAMILY")
    print("=" * 70)
    print()
    
    print("BASE URL:")
    print("  https://www.zillow.com/brooklyn-new-york-ny/duplex/")
    print()
    
    print("SEARCH QUERY STATE (JSON, then URL-encoded):")
    print("-" * 70)
    
    search_state = """
{
  "regionSelection": [
    {"regionId": 37607, "regionType": 17}  // Brooklyn
  ],
  "filterState": {
    "price": {"max": 2500000},              // Max $2.5M
    "beds": {"min": 5},                     // Min 5 bedrooms
    "baths": {"min": 4},                    // Min 4 bathrooms
    "mp": {"max": 12500},                   // Monthly payment ~$12.5k
    
    // EXCLUDE these property types:
    "sf": {"value": false},                 // Single family
    "tow": {"value": false},                // Townhouse  
    "con": {"value": false},                // Condo
    "land": {"value": false},               // Land
    "apa": {"value": false},                // Apartment
    "manu": {"value": false},               // Manufactured
    "apco": {"value": false},               // Apt/Condo
    
    "sort": {"value": "globalrelevanceex"}  // Sort by relevance
  },
  "mapBounds": {
    "west": -74.91808229663286,
    "east": -73.57500368335161,
    "south": 40.13454713467564,
    "north": 40.97758383487431
  },
  "isMapVisible": true,
  "isListVisible": true,
  "usersSearchTerm": "Brooklyn New York NY",
  "pagination": {"currentPage": 1}          // Page number
}
    """
    
    print(search_state)
    print()
    print("-" * 70)
    
    print()
    print("FULL URL FORMAT:")
    print("  [BASE_URL]?searchQueryState=[URL_ENCODED_JSON]")
    print()
    
    print("WHAT ZILLOW RETURNS:")
    print("  ✓ Only properties in Brooklyn")
    print("  ✓ Only duplex/multi-family properties")
    print("  ✓ Only properties ≤ $2,500,000")
    print("  ✓ Only properties with ≥ 5 bedrooms")
    print("  ✓ Only properties with ≥ 4 bathrooms")
    print()
    
    print("WHAT WE STILL NEED TO FILTER:")
    print("  ✓ B units (from HPD database)")
    print()
    
    print("=" * 70)
    print()


def show_region_ids():
    """Display NYC borough region IDs."""
    print("NYC BOROUGH REGION IDs FOR ZILLOW")
    print("=" * 70)
    print()
    print("  Brooklyn:      37607   ← CURRENT TARGET")
    print("  Manhattan:     12530")
    print("  Queens:        270915")
    print("  Bronx:         14286")
    print("  Staten Island: 2042")
    print()
    print("To switch boroughs, update in .env:")
    print("  ZILLOW_REGION_ID=37607")
    print("  ZILLOW_SEARCH_LOCATION=Brooklyn, NY")
    print("  BOROUGHS=Brooklyn")
    print()
    print("=" * 70)


def show_filter_mapping():
    """Show how config filters map to URL parameters."""
    print()
    print("FILTER MAPPING: Config → Zillow URL")
    print("=" * 70)
    print()
    
    mappings = [
        ("config.filters.max_price", "filterState.price.max", "2500000"),
        ("config.filters.min_bedrooms", "filterState.beds.min", "5"),
        ("config.filters.min_bathrooms", "filterState.baths.min", "4"),
        ("config.filters.boroughs[0]", "regionSelection[0].regionId", "37607"),
        ("config.filters.property_types", "URL path segment", "/duplex/"),
    ]
    
    for config_path, url_path, value in mappings:
        print(f"  {config_path:<30} → {url_path:<30} = {value}")
    
    print()
    print("=" * 70)


if __name__ == "__main__":
    show_url_structure()
    show_region_ids()
    show_filter_mapping()
    
    print()
    print("💡 TIP: The actual URL in the scraper is URL-encoded.")
    print("   Run the scraper with debug logging to see the full URL.")
    print()
