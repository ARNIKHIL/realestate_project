"""
Example script showing how to use individual components.
"""
import asyncio
from models import Address
from scrapers import HPDClient


async def example_hpd_search():
    """Example: Search HPD database for a specific address."""
    print("Example: Searching HPD Database\n")
    
    # Create test address
    address = Address(
        street="100 GOLD STREET",
        city="New York",
        state="NY",
        borough="Manhattan"
    )
    
    print(f"Searching for: {address}\n")
    
    # Search HPD
    async with HPDClient() as client:
        building = await client.search_by_address(address)
        
        if building:
            print("✅ Building found!")
            print(f"  Building ID: {building.building_id}")
            print(f"  BIN: {building.bin}")
            print(f"  Total Units: {building.total_units}")
            print(f"  Has B Units: {building.has_b_units}")
            
            if building.has_b_units:
                print(f"  B Unit Count: {len(building.b_units)}")
                for unit in building.b_units:
                    print(f"    - {unit.unit_number}")
        else:
            print("❌ No building found")


def example_filtering():
    """Example: Show how filtering works."""
    from filters import PropertyFilter
    
    print("\nExample: Investment Filter Criteria\n")
    
    filter = PropertyFilter()
    summary = filter.get_filter_summary()
    
    print("Current filter settings:")
    for key, value in summary.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    print("=" * 60)
    print("Real Estate Analysis - Component Examples")
    print("=" * 60 + "\n")
    
    # Run HPD search example
    asyncio.run(example_hpd_search())
    
    # Show filter example
    example_filtering()
    
    print("\n" + "=" * 60)
    print("See main.py for complete workflow")
    print("=" * 60)
