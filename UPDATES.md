# System Update Summary

## Updated Requirements

The system has been configured to identify multi-family properties with the following specific criteria:

### Target Locations
- **Manhattan**
- **Brooklyn** 
- **Bronx**
- **Queens**

*(Staten Island excluded)*

### Property Criteria
- **Price**: ≤ $2,500,000
- **Bedrooms**: ≥ 5
- **Bathrooms**: ≥ 4
- **Property Type**: Multi Family only
- **HPD Requirement**: Must have B units

### Data Fields Captured

#### From Zillow
- Address (full street address)
- Borough
- Price
- Number of bedrooms
- Number of bathrooms
- Property type
- Zillow URL
- Listing ID (ZPID)
- Square footage
- **Lot size** (NEW)
- **Year built** (NEW)
- Days on market
- Listing status

#### From HPD
- Building ID
- BIN (Building Identification Number)
- **BBL (Borough-Block-Lot)** (NEW)
- Unit breakdown
- B unit classification and count
- Total number of units
- **Building class** (NEW)
- Borough
- Registration information
- Landlord details

## Files Modified

### 1. Configuration Files
- **[.env.example](.env.example)**: Updated with new price limit ($2.5M), added bedroom/bathroom minimums, borough list
- **[config.py](config.py)**: Updated FilterCriteria model with new fields

### 2. Data Models
- **[models.py](models.py)**: 
  - Added `lot_size` and `year_built` to ZillowProperty
  - Added `bbl` and `building_class` to HPDBuilding

### 3. Filtering Logic
- **[filters.py](filters.py)**: 
  - Added `meets_bedroom_criteria()` method
  - Added `meets_bathroom_criteria()` method
  - Renamed `meets_neighborhood_criteria()` to `meets_borough_criteria()`
  - Updated filter criteria to check all new requirements
  - Updated `get_filter_summary()` to display new criteria

### 4. Web Scrapers
- **[scrapers/zillow_scraper.py](scrapers/zillow_scraper.py)**:
  - Updated search URL to filter for multi-family properties
  - Added extraction of lot size and year built
  - Enhanced property card parsing

- **[scrapers/hpd_client.py](scrapers/hpd_client.py)**:
  - Added BBL extraction from API response
  - Added building class extraction
  - Enhanced logging to include new fields

### 5. Export/Reporting
- **[exporter.py](exporter.py)**: Updated to include all new fields in CSV/Excel/JSON exports

## How to Use

### 1. Configure Environment
```bash
cp .env.example .env
# Edit .env if you want to adjust any settings
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the System

**Option A: Interactive Menu**
```bash
python run.py
```

**Option B: Direct Execution**
```bash
python main.py
```

### 4. Review Results
Check the `output/` directory for:
- CSV file with all matching properties
- Excel file with formatted data
- JSON file with complete data
- Summary report with statistics

## Current Filter Configuration

The system is now configured to find properties that meet ALL of the following:

✓ **Location**: Manhattan, Brooklyn, Bronx, or Queens  
✓ **Price**: ≤ $2,500,000  
✓ **Bedrooms**: ≥ 5  
✓ **Bathrooms**: ≥ 4  
✓ **Type**: Multi Family  
✓ **Units**: ≥ 2 (minimum)  
✓ **B Units**: Must be present (verified via HPD)  

## Output Columns

The exported data now includes these columns:

**Property Information**
- Address, Street, Borough, Zip Code
- Price, Bedrooms, Bathrooms
- Square Feet, Lot Size (sqft), Year Built
- Property Type, Listing Status, Days on Market
- Zillow URL, ZPID

**HPD Data**
- HPD Match (Yes/No)
- Match Confidence (High/Medium/Low)
- Total Units, B Unit Count
- Building ID, BIN, BBL
- Building Class
- Landlord

**Analysis**
- Meets Criteria (Yes/No)
- Investment Score (0-100)
- Price Per Unit
- B Unit Numbers (list)
- Timestamps

## Investment Scoring

Properties are ranked (0-100 points) based on:
- **B Units Present**: 30 points
- **B Unit Count**: 10 points each (max 30)
- **Total Units**: 5 points each (max 25)
- **Price/Unit Ratio**: up to 15 points
- **Recency**: up to 10 points

Higher scores indicate better investment opportunities.

## Important Notes

### Zillow Scraping
⚠️ **Zillow actively blocks scrapers**. Consider:
- Using residential proxies
- Implementing longer delays
- Using Zillow's official API if available
- Using a commercial data service

### HPD API
- Free tier: 1,000 requests/day
- With app token: Higher limits
- Get token at: https://data.cityofnewyork.us/

### Data Accuracy
- Always verify property details independently
- Cross-reference with official sources
- This tool is for research only, not investment advice

## Testing the System

Test individual components:
```bash
python examples.py
```

This will demonstrate:
- HPD database search
- Filter criteria display

## Next Steps

1. Copy `.env.example` to `.env`
2. (Optional) Add HPD app token to `.env` for better rate limits
3. Run the system: `python run.py`
4. Review results in `output/` directory
5. Adjust criteria in `.env` as needed

## Support

For issues or questions:
1. Check the [README.md](README.md) for full documentation
2. Review log files in `logs/` directory
3. Verify your `.env` configuration

---

**Last Updated**: January 17, 2026
