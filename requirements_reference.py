"""
Quick reference for the current system configuration and requirements.
"""

SYSTEM_REQUIREMENTS = {
    "objective": "Find multi-family properties in NYC with B units",
    
    "target_boroughs": [
        "Manhattan",
        "Brooklyn",
        "Bronx",
        "Queens"
    ],
    
    "property_criteria": {
        "price_max": 2_500_000,  # $2.5 million
        "bedrooms_min": 5,
        "bathrooms_min": 4.0,
        "property_type": "Multi Family",
        "require_b_units": True,
        "min_units": 2
    },
    
    "zillow_fields": [
        "Address (full)",
        "Borough",
        "Price",
        "Number of bedrooms",
        "Number of bathrooms",
        "Property type",
        "Zillow URL",
        "Listing ID (ZPID)",
        "Square footage",
        "Lot size",
        "Year built",
        "Days on market"
    ],
    
    "hpd_fields": [
        "Building ID",
        "BIN (Building Identification Number)",
        "BBL (Borough-Block-Lot)",
        "Unit breakdown",
        "B unit classification",
        "Total number of B units",
        "Building class",
        "Borough",
        "Registration info",
        "Landlord details"
    ],
    
    "filtering_logic": """
    Properties must meet ALL of the following:
    1. Location: One of the 4 target boroughs
    2. Price: ≤ $2,500,000
    3. Bedrooms: ≥ 5
    4. Bathrooms: ≥ 4
    5. Property Type: Multi Family
    6. B Units: Must be verified in HPD database
    7. Total Units: ≥ 2
    """,
    
    "output_formats": [
        "CSV (spreadsheet)",
        "Excel (formatted)",
        "JSON (complete data)",
        "Summary report (text)"
    ]
}


def print_requirements():
    """Print current system requirements."""
    print("=" * 70)
    print("NYC MULTI-FAMILY PROPERTY FINDER - REQUIREMENTS")
    print("=" * 70)
    print()
    print("🎯 OBJECTIVE:")
    print(f"   {SYSTEM_REQUIREMENTS['objective']}")
    print()
    print("📍 TARGET BOROUGHS:")
    for borough in SYSTEM_REQUIREMENTS['target_boroughs']:
        print(f"   • {borough}")
    print()
    print("🏘️  PROPERTY CRITERIA:")
    criteria = SYSTEM_REQUIREMENTS['property_criteria']
    print(f"   • Max Price: ${criteria['price_max']:,}")
    print(f"   • Min Bedrooms: {criteria['bedrooms_min']}")
    print(f"   • Min Bathrooms: {criteria['bathrooms_min']}")
    print(f"   • Property Type: {criteria['property_type']}")
    print(f"   • Requires B Units: {criteria['require_b_units']}")
    print(f"   • Min Total Units: {criteria['min_units']}")
    print()
    print("📊 DATA SOURCES:")
    print("   Zillow + NYC HPD Database")
    print()
    print("📤 OUTPUT FORMATS:")
    for fmt in SYSTEM_REQUIREMENTS['output_formats']:
        print(f"   • {fmt}")
    print()
    print("=" * 70)


if __name__ == "__main__":
    print_requirements()
