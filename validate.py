#!/usr/bin/env python3
"""
Validation script to verify system configuration and requirements.
"""
import sys
from pathlib import Path


def check_python_version():
    """Check Python version."""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True


def check_dependencies():
    """Check if required packages are installed."""
    required = {
        'selenium': 'Zillow scraping',
        'pandas': 'Data processing',
        'aiohttp': 'HPD API client',
        'pydantic': 'Data validation',
        'loguru': 'Logging',
        'beautifulsoup4': 'HTML parsing',
        'openpyxl': 'Excel export',
        'fuzzywuzzy': 'Address matching'
    }
    
    missing = []
    for package, purpose in required.items():
        try:
            __import__(package)
            print(f"✅ {package:<20} ({purpose})")
        except ImportError:
            print(f"❌ {package:<20} ({purpose}) - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n❌ Missing {len(missing)} package(s)")
        print("   Run: pip install -r requirements.txt")
        return False
    return True


def check_configuration():
    """Check configuration file."""
    try:
        from config import config
        
        print("\n📋 CURRENT CONFIGURATION")
        print("=" * 60)
        
        # Zillow config
        print(f"Zillow Location:     {config.zillow.search_location}")
        print(f"Max Pages:           {config.zillow.max_pages}")
        
        # Filters
        print(f"\nPrice Range:         ${config.filters.min_price:,.0f} - ${config.filters.max_price:,.0f}")
        print(f"Min Bedrooms:        {config.filters.min_bedrooms}")
        print(f"Min Bathrooms:       {config.filters.min_bathrooms}")
        print(f"Min Units:           {config.filters.min_units}")
        print(f"Require B Units:     {config.filters.require_b_units}")
        
        if config.filters.boroughs:
            print(f"Target Boroughs:     {', '.join(config.filters.boroughs)}")
        
        if config.filters.property_types:
            print(f"Property Types:      {', '.join(config.filters.property_types)}")
        
        # Output
        print(f"\nOutput Directory:    {config.output.output_dir}")
        print(f"Output Formats:      {', '.join(config.output.output_formats)}")
        
        print("=" * 60)
        
        # Validate requirements
        print("\n🎯 REQUIREMENT VALIDATION")
        print("=" * 60)
        
        errors = []
        
        # Check price
        if config.filters.max_price != 2_500_000:
            errors.append(f"Price should be ≤ $2,500,000 (currently: ${config.filters.max_price:,.0f})")
        else:
            print("✅ Price limit: $2,500,000")
        
        # Check bedrooms
        if config.filters.min_bedrooms != 5:
            errors.append(f"Min bedrooms should be 5 (currently: {config.filters.min_bedrooms})")
        else:
            print("✅ Min bedrooms: 5")
        
        # Check bathrooms
        if config.filters.min_bathrooms != 4.0:
            errors.append(f"Min bathrooms should be 4 (currently: {config.filters.min_bathrooms})")
        else:
            print("✅ Min bathrooms: 4")
        
        # Check boroughs
        expected_boroughs = {"Brooklyn"}
        actual_boroughs = set(config.filters.boroughs) if config.filters.boroughs else set()
        
        if actual_boroughs != expected_boroughs:
            errors.append(f"Boroughs should be {expected_boroughs} (currently: {actual_boroughs})")
        else:
            print("✅ Borough: Brooklyn")
        
        # Check property types
        if config.filters.property_types:
            if any('multi' in pt.lower() or 'duplex' in pt.lower() for pt in config.filters.property_types):
                print("✅ Property type: Multi Family / Duplex")
            else:
                errors.append("Property types should include 'Multi Family' or 'Duplex'")
        
        # Check B units requirement
        if not config.filters.require_b_units:
            errors.append("B units should be required")
        else:
            print("✅ Require B units: Yes")
        
        print("=" * 60)
        
        if errors:
            print("\n⚠️  CONFIGURATION WARNINGS:")
            for error in errors:
                print(f"   • {error}")
            print("\nEdit .env file to fix configuration.")
            return False
        else:
            print("\n✅ Configuration matches requirements!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return False


def check_file_structure():
    """Check if all required files exist."""
    required_files = [
        'main.py',
        'config.py',
        'models.py',
        'matcher.py',
        'filters.py',
        'exporter.py',
        'scrapers/zillow_scraper.py',
        'scrapers/hpd_client.py',
        'utils/logger.py',
        'requirements.txt',
        '.env.example'
    ]
    
    print("\n📁 FILE STRUCTURE")
    print("=" * 60)
    
    missing = []
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            missing.append(file_path)
    
    print("=" * 60)
    
    if missing:
        print(f"\n❌ Missing {len(missing)} file(s)")
        return False
    return True


def check_env_file():
    """Check if .env file exists."""
    if Path('.env').exists():
        print("✅ .env file exists")
        return True
    else:
        print("⚠️  .env file not found")
        print("   Copy .env.example to .env and configure")
        return True  # Not critical


def main():
    """Run all validation checks."""
    print("=" * 60)
    print("REAL ESTATE PROPERTY FINDER - SYSTEM VALIDATION")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("File Structure", check_file_structure),
        ("Environment File", check_env_file),
        ("Dependencies", check_dependencies),
        ("Configuration", check_configuration),
    ]
    
    results = []
    
    for name, check_func in checks:
        print(f"\n🔍 Checking {name}...")
        print("-" * 60)
        result = check_func()
        results.append((name, result))
    
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:<30} {status}")
    
    print("=" * 60)
    
    if all(result for _, result in results):
        print("\n🎉 All checks passed! System is ready to run.")
        print("\nNext steps:")
        print("  1. Review .env configuration")
        print("  2. Run: python run.py")
        print("  3. Select option 1 to start analysis")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please fix issues before running.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
