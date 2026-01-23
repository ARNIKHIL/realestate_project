# Real Estate Property Analysis System

A comprehensive web scraping and analysis system that automatically identifies NYC investment properties with basement units (B units) by cross-referencing Zillow listings with the NYC Housing Preservation & Development (HPD) database.

## Features

- **Zillow Scraping**: Automatically scrapes recently listed properties from Zillow
- **HPD Integration**: Cross-checks properties against NYC HPD database
- **B Unit Detection**: Identifies properties with basement units or B-classified units
- **Investment Filtering**: Filters properties based on customizable investment criteria
- **Investment Scoring**: Ranks properties by investment potential
- **Multi-format Export**: Exports results to CSV, Excel, and JSON
- **Detailed Reporting**: Generates comprehensive summary reports

## System Architecture

```
realestate_pro/
├── main.py                 # Main orchestration script
├── config.py              # Configuration management
├── models.py              # Data models
├── matcher.py             # Property matching logic
├── filters.py             # Investment criteria filtering
├── exporter.py            # Data export functionality
├── scrapers/
│   ├── zillow_scraper.py  # Zillow web scraper
│   └── hpd_client.py      # HPD API client
├── utils/
│   └── logger.py          # Logging configuration
├── requirements.txt       # Python dependencies
└── .env.example          # Environment configuration template

```

## Installation

1. **Clone or navigate to the project directory**:
   ```bash
   cd /Users/nalampal/Documents/realestate_pro
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

## Configuration

Edit the `.env` file to customize your search parameters:

### Zillow Settings
- `ZILLOW_SEARCH_LOCATION`: Target location (default: "New York, NY")
- `ZILLOW_MAX_PAGES`: Maximum pages to scrape (default: 10)

### HPD API Settings
- `HPD_APP_TOKEN`: Optional NYC Open Data app token (recommended for higher rate limits)
- Get your token at: https://data.cityofnewyork.us/

### Filtering Criteria
- `MIN_PRICE`: Minimum property price (default: 0)
- `MAX_PRICE`: Maximum property price (default: 2,000,000)
- `MIN_UNITS`: Minimum number of units (default: 2)
- `REQUIRE_B_UNITS`: Require properties to have B units (default: true)

### Scraping Settings
- `REQUEST_DELAY`: Delay between requests in seconds (default: 2)
- `MAX_RETRIES`: Maximum retry attempts (default: 3)

## Usage

### Basic Usage

Run the complete analysis pipeline:

```bash
python main.py
```

This will:
1. Scrape property listings from Zillow
2. Cross-check each property with the HPD database
3. Identify properties with B units
4. Filter based on your investment criteria
5. Generate reports and export data

### Output

Results are saved to the `output/` directory:

- **CSV**: Spreadsheet format for easy analysis
- **Excel**: Formatted spreadsheet with auto-sized columns
- **JSON**: Machine-readable format with complete data
- **Summary Report**: Text file with statistics and top opportunities

### Example Output Structure

```
output/
├── properties_20260117_143022.csv
├── properties_20260117_143022.xlsx
├── properties_20260117_143022.json
└── summary_report_20260117_143022.txt
```

## Data Models

### EnrichedProperty
Combined data from Zillow and HPD with analysis:
- **Zillow Data**: Price, bedrooms, bathrooms, listing details
- **HPD Data**: Total units, B units, building ID, landlord info
- **Analysis**: Investment score, match confidence, criteria compliance

### HPDBuilding
HPD database information:
- Building ID and BIN
- Total units and unit breakdown
- B unit details (unit numbers, types)
- Registration and landlord information

## Investment Scoring

Properties are scored (0-100) based on:
- **B Units** (30 points): Presence of basement units
- **B Unit Count** (30 points): Number of B units (10 pts each, max 30)
- **Total Units** (25 points): More units = more cash flow (5 pts each, max 25)
- **Price per Unit** (15 points): Lower is better
- **Days on Market** (10 points): Newer listings score higher

## HPD Database Details

The system queries multiple NYC Open Data endpoints:

1. **Building Records** (`evjd-dqpz`): Basic building information
2. **HPD Registrations** (`tesw-yqqr`): Registration and landlord data
3. **Registration Contacts** (`feu5-ztfk`): Unit-level details for B unit identification

### B Unit Detection

B units are identified by:
- Unit numbers starting with "B"
- Units labeled as "BSMT" or "BASEMENT"
- HPD classification codes indicating basement units

## Rate Limiting & Best Practices

### Zillow Scraping
- Uses Selenium with headless Chrome
- Implements delays between requests
- Respects robots.txt
- **Note**: Zillow actively blocks scrapers - consider:
  - Using residential proxies
  - Rotating user agents
  - Implementing CAPTCHA solving
  - Using Zillow's official API if available

### HPD API
- Asynchronous batch requests for efficiency
- Respects API rate limits
- Free tier: 1,000 requests/day without token
- With app token: Higher limits available
- Implements retry logic with exponential backoff

## Troubleshooting

### Common Issues

**No properties found from Zillow**:
- Zillow may be blocking the scraper
- Try reducing `ZILLOW_MAX_PAGES`
- Consider using a proxy service
- Check if Zillow's HTML structure has changed

**HPD API errors**:
- Verify your app token is correct
- Check internet connectivity
- Ensure addresses are properly formatted
- NYC Open Data may be experiencing downtime

**No HPD matches**:
- Addresses from Zillow may not exactly match HPD format
- Try adjusting the fuzzy matching threshold in `matcher.py`
- Some properties may not be in the HPD database

**Low match confidence**:
- Address format differences are common
- Manual verification recommended for low-confidence matches
- Check the match_confidence field in exports

## Advanced Customization

### Custom Filtering

Edit `filters.py` to add custom filtering logic:

```python
def custom_filter(self, property: EnrichedProperty) -> bool:
    # Add your custom logic
    return True
```

### Modify Investment Score

Edit the `calculate_investment_score` method in `filters.py` to adjust scoring weights.

### Additional Data Sources

Add new scrapers in the `scrapers/` directory following the same pattern as existing scrapers.

## Legal & Ethical Considerations

⚠️ **Important Disclaimers**:

- **Terms of Service**: Web scraping may violate Zillow's Terms of Service
- **Rate Limiting**: Always respect website rate limits and robots.txt
- **Data Usage**: Scraped data is for personal research only
- **Accuracy**: Always verify property information independently
- **Investment**: This tool is for research only, not investment advice

### Recommendations:
1. Use Zillow's official API if available
2. Respect rate limits and implement delays
3. Consider commercial data services for production use
4. Verify all property information before making decisions
5. Consult with real estate and legal professionals

## Dependencies

Key dependencies:
- `selenium`: Browser automation for Zillow
- `beautifulsoup4`: HTML parsing
- `aiohttp`: Async HTTP client for HPD API
- `pandas`: Data manipulation and export
- `pydantic`: Data validation
- `loguru`: Logging
- `fuzzywuzzy`: Address matching

See `requirements.txt` for complete list.

## NYC Open Data Resources

- **HPD Buildings**: https://data.cityofnewyork.us/Housing-Development/Building-Footprints/nqwf-w8eh
- **HPD Registrations**: https://data.cityofnewyork.us/Housing-Development/Registration-Contacts/feu5-ztfk
- **API Documentation**: https://dev.socrata.com/foundry/data.cityofnewyork.us/

## Future Enhancements

Potential improvements:
- [ ] Integration with additional property databases
- [ ] Historical price tracking
- [ ] Neighborhood analysis and trends
- [ ] Property valuation estimates
- [ ] Email notifications for new listings
- [ ] Web dashboard for results visualization
- [ ] Machine learning for property scoring
- [ ] Integration with mortgage calculators
- [ ] Automated property comparison reports

## Support & Contributing

This is a custom tool built for property investment research. Feel free to modify and extend based on your needs.

## License

This project is provided as-is for educational and research purposes only.

---

**Created**: January 2026  
**Last Updated**: January 17, 2026
