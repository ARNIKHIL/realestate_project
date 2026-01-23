"""
Main orchestration script for the real estate property analysis system.

This script coordinates:
1. Scraping Compass for property listings
2. Cross-checking against HPD database for B units
3. Filtering based on investment criteria
4. Exporting results
"""
import asyncio
from scrapers.zillow_scraper import ZillowScraper
from matcher import PropertyMatcher
from filters import PropertyFilter
from exporter import DataExporter
from config import config
from utils.logger import logger


async def main():
    """Main execution function."""
    logger.info("=" * 80)
    logger.info("REAL ESTATE PROPERTY ANALYSIS SYSTEM - STARTING")
    logger.info("=" * 80)
    
    # Initialize components
    zillow_scraper = ZillowScraper()
    property_filter = PropertyFilter()
    data_exporter = DataExporter()
    
    try:
        # Step 1: Scrape Zillow listings from all locations
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: Scraping Zillow Property Listings from Multiple Locations")
        logger.info(f"Locations: Manhattan, Brooklyn, Bronx, Queens")
        logger.info("=" * 80)
        
        zillow_properties = zillow_scraper.scrape_all_locations()
        
        if not zillow_properties:
            logger.error("No properties found from Zillow. Exiting.")
            return
        
        logger.info(f"Successfully scraped {len(zillow_properties)} properties from Zillow across all locations")
        
        # Export master list of ALL scraped properties
        logger.info("\n" + "=" * 80)
        logger.info("EXPORTING MASTER LIST: All Scraped Properties")
        logger.info("=" * 80)
        
        master_files = data_exporter.export_all_formats(
            zillow_properties,
            filename_prefix="master_all_properties"
        )
        
        logger.info("Master list exported (use this to decide which addresses to check in HPD):")
        for format_type, filepath in master_files.items():
            logger.info(f"  {format_type.upper()}: {filepath}")
        
        # Step 2: Match with HPD database (uses cache for already-scraped addresses)
        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: Cross-Checking with HPD Database (with caching)")
        logger.info("=" * 80)
        
        async with PropertyMatcher() as matcher:
            enriched_properties = await matcher.match_properties_batch(zillow_properties)
        
        logger.info(f"Successfully matched {len(enriched_properties)} properties with HPD data")
        
        # Log matching statistics
        matched_count = sum(1 for p in enriched_properties if p.hpd_match_found)
        b_unit_count = sum(1 for p in enriched_properties if p.has_b_units)
        logger.info(f"HPD matches: {matched_count}/{len(enriched_properties)}")
        logger.info(f"Properties with B units: {b_unit_count}/{len(enriched_properties)}")
        
        # Step 3: Export final results with HPD data
        logger.info("\n" + "=" * 80)
        logger.info("STEP 3: Exporting Final Results with HPD Data")
        logger.info("=" * 80)
        
        if enriched_properties:
            export_files = data_exporter.export_all_formats(
                enriched_properties,
                filename_prefix="final_with_hpd_data"
            )
            
            logger.info("Export complete! Files created:")
            for format_type, filepath in export_files.items():
                logger.info(f"  {format_type.upper()}: {filepath}")
        else:
            logger.warning("No enriched properties to export.")
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("EXECUTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Properties scraped:        {len(zillow_properties)}")
        logger.info(f"HPD matches found:         {matched_count}")
        logger.info(f"Properties with B units:   {b_unit_count}")
        logger.info("=" * 80)
        logger.info("FILES CREATED:")
        logger.info("  1. master_all_properties_*.xlsx - All Zillow scraped addresses")
        logger.info("  2. final_with_hpd_data_*.xlsx - Properties enriched with HPD B-unit data")
        logger.info("  3. master_hpd_data.xlsx - Master cache with Zillow + HPD data (reused on next run)")
        logger.info("=" * 80)
        logger.info("REAL ESTATE PROPERTY ANALYSIS SYSTEM - COMPLETE")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        raise


def run():
    """Synchronous wrapper for async main function."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
