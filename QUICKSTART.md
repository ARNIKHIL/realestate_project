# NYC Multi-Family B-Unit Property Finder

## 🎯 System Overview

This system automatically identifies investment-grade multi-family properties in NYC that contain basement units (B units) by cross-referencing Zillow listings with HPD database records.

## ✅ Current Configuration

### Target Criteria (ALL must be met)
```
✓ Location:    Brooklyn only
✓ Price:       ≤ $2,500,000
✓ Bedrooms:    ≥ 5
✓ Bathrooms:   ≥ 4
✓ Type:        Multi Family / Duplex
✓ B Units:     Must be verified in HPD
```

## 🔄 System Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: ZILLOW SCRAPING WITH FILTERS                       │
│  ─────────────────────────────────────                      │
│  → Search Brooklyn multi-family/duplex properties           │
│  → APPLY FILTERS IN ZILLOW SEARCH:                          │
│    • Price ≤ $2,500,000                                     │
│    • Bedrooms ≥ 5                                           │
│    • Bathrooms ≥ 4                                          │
│    • Property type: Multi-family/Duplex                     │
│  → Extract: address, price, beds, baths, sqft, lot, year    │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: HPD DATABASE CROSS-CHECK                           │
│  ──────────────────────────────────                         │
│  → Match each property with HPD records                     │
│  → Identify B units (basement classifications)              │
│  → Extract: BBL, BIN, building class, unit details          │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: B-UNIT FILTERING                                   │
│  ─────────────────────                                      │
│  → Verify properties have B units in HPD                    │
│  → Calculate investment score (0-100)                       │
│  → Rank by B-unit count and investment potential            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: EXPORT & REPORTING                                 │
│  ────────────────────────                                   │
│  → Generate CSV/Excel/JSON exports                          │
│  → Rank by investment score                                 │
│  → Create summary report                                    │
│  → Output to /output directory                              │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Data Fields Captured

### Zillow Data
| Field | Description |
|-------|-------------|
| Address | Full street address |
| Borough | Brooklyn |
| Price | Listing price (≤$2.5M pre-filtered) |
| Bedrooms | Number of bedrooms (≥5 pre-filtered) |
| Bathrooms | Number of bathrooms (≥4 pre-filtered) |
| Square Feet | Interior square footage |
| **Lot Size** | Lot size in square feet |
| **Year Built** | Construction year |
| Property Type | Multi Family / Duplex (pre-filtered) |
| ZPID | Zillow Property ID |
| URL | Link to Zillow listing |

### HPD Database
| Field | Description |
|-------|-------------|
| Building ID | HPD building identifier |
| BIN | Building Identification Number |
| **BBL** | Borough-Block-Lot number |
| **Building Class** | NYC building classification |
| Total Units | Total dwelling units |
| B Units | List of basement units |
| B Unit Count | Number of B units |
| Landlord | Property owner name |

### Calculated Metrics
| Field | Description |
|-------|-------------|
| Investment Score | 0-100 ranking |
| Price per Unit | Price divided by total units |
| Match Confidence | High/Medium/Low |
| Meets Criteria | Yes/No based on all filters |

## 🏗️ Project Structure

```
realestate_pro/
│
├── main.py                    # Main execution script
├── run.py                     # Interactive launcher
├── config.py                  # Configuration management
├── models.py                  # Data models
├── matcher.py                 # Zillow ↔ HPD matching logic
├── filters.py                 # Investment criteria filtering ⭐
├── exporter.py                # Data export & reporting
│
├── scrapers/
│   ├── zillow_scraper.py      # Zillow web scraper
│   └── hpd_client.py          # HPD API client
│
├── utils/
│   └── logger.py              # Logging configuration
│
├── .env.example               # Configuration template
├── requirements.txt           # Python dependencies
├── README.md                  # Full documentation
├── UPDATES.md                 # Recent changes
└── requirements_reference.py  # Quick reference
```

## 🚀 Quick Start

### 1. Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
```

### 2. Run
```bash
# Interactive mode (recommended)
python run.py

# Or direct execution
python main.py
```

### 3. Review Results
```bash
# Check output directory
ls output/

# Files created:
# - properties_YYYYMMDD_HHMMSS.csv
# - properties_YYYYMMDD_HHMMSS.xlsx
# - properties_YYYYMMDD_HHMMSS.json
# - summary_report_YYYYMMDD_HHMMSS.txt
```

## 📊 Investment Scoring Algorithm

Properties receive a score from 0-100 based on:

| Factor | Points | Description |
|--------|--------|-------------|
| Has B Units | 30 | Basement units present |
| B Unit Count | 10 each (max 30) | More B units = higher score |
| Total Units | 5 each (max 25) | More cash flow potential |
| Price per Unit | up to 15 | Lower = better |
| Days on Market | up to 10 | Newer = better |

**Example:**
- 3 B units: 30 + 30 = 60 points
- 6 total units: 25 points (capped)
- Good price/unit: 15 points
- Listed < 7 days: 10 points
- **Total: 100 points** ⭐

## ⚙️ Customization

### Adjust Criteria
Edit `.env` file:
```bash
MAX_PRICE=2500000
MIN_BEDROOMS=5
MIN_BATHROOMS=4
BOROUGHS=Manhattan,Brooklyn,Bronx,Queens
PROPERTY_TYPES=Multi Family,Multifamily
REQUIRE_B_UNITS=true
```

### Change Search Area
Edit in `.env` to search other boroughs:
```bash
ZILLOW_SEARCH_LOCATION=Manhattan, NY
ZILLOW_REGION_ID=12530  # Manhattan region ID
BOROUGHS=Manhattan
```

Brooklyn region IDs for reference:
- Brooklyn: 37607
- Manhattan: 12530
- Queens: 270915
- Bronx: 14286

### Adjust Output
Edit in `.env`:
```bash
OUTPUT_FORMAT=csv,excel,json
OUTPUT_DIR=./my_results
```

## ⚠️ Important Considerations

### Legal & Ethical
- ⚠️ Zillow actively blocks scrapers
- Consider using Zillow's official API
- Respect rate limits and ToS
- Data is for research only

### Data Accuracy
- Always verify property details
- Cross-reference with official sources
- HPD data may be outdated
- Not investment advice

### Technical
- Requires stable internet
- HPD API may have rate limits
- Selenium requires Chrome browser
- Process may take several minutes

## 🔧 Troubleshooting

### No Zillow Results
- Zillow may be blocking requests
- Try reducing `ZILLOW_MAX_PAGES`
- Consider using proxies
- Check if HTML structure changed

### No HPD Matches
- Address format may differ
- Try adjusting fuzzy match threshold
- Some properties not in HPD database
- Check borough spelling

### No Properties Meet Criteria
- Criteria may be too strict
- Try adjusting price/bed/bath limits
- Check if boroughs are spelled correctly
- Verify B units actually exist in area

## 📞 Getting Help

1. Check logs in `logs/` directory
2. Review [README.md](README.md) for full docs
3. Run `python requirements_reference.py` for config summary
4. Check [UPDATES.md](UP/Duplex properties with B units in **Brooklyn**  
**Filtering**: Applied at Zillow search level (price, beds, baths, type)

---

**System Status**: ✅ Configured and Ready  
**Last Updated**: January 17, 2026  
**Target**: Multi-family properties with B units in Manhattan, Brooklyn, Bronx, Queens
