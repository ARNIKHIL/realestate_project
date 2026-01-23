# Brooklyn-Focused Update - January 17, 2026

## 🎯 Key Changes

### ✅ What Changed

**1. Location Focus**
- **Before**: All 4 boroughs (Manhattan, Brooklyn, Bronx, Queens)
- **Now**: Brooklyn ONLY

**2. Filtering Strategy** ⭐ MAJOR CHANGE
- **Before**: Scraped all properties, then filtered by criteria
- **Now**: Filters applied DIRECTLY in Zillow search URL

### 🔍 Filtering Now Happens at Scraping Level

All criteria are now built into the Zillow search URL:

```
✓ Location:    Brooklyn (Region ID: 37607)
✓ Price:       ≤ $2,500,000  ← Applied in Zillow URL
✓ Bedrooms:    ≥ 5           ← Applied in Zillow URL
✓ Bathrooms:   ≥ 4           ← Applied in Zillow URL
✓ Type:        Duplex/Multi-family ← Applied in Zillow URL
✓ B Units:     Verified via HPD (only step 3)
```

### 📝 Updated Workflow

```
STEP 1: Zillow Scraping WITH FILTERS
  ↓ Only returns properties matching:
  ↓ • Brooklyn location
  ↓ • Price ≤ $2.5M
  ↓ • Beds ≥ 5
  ↓ • Baths ≥ 4
  ↓ • Multi-family/Duplex type

STEP 2: HPD Cross-Check
  ↓ Match with HPD database
  ↓ Extract B unit information

STEP 3: B-Unit Filtering
  ↓ Only keep properties with B units
  ↓ Calculate investment scores

STEP 4: Export Results
```

## 🔧 Technical Changes

### Files Modified

1. **[.env.example](.env.example)**
   - Changed `ZILLOW_SEARCH_LOCATION` to "Brooklyn, NY"
   - Added `ZILLOW_REGION_ID=37607`
   - Changed `BOROUGHS=Brooklyn`
   - Added "Duplex" to property types

2. **[config.py](config.py)**
   - Updated `ZillowConfig` with `region_id` field
   - Changed default boroughs to `["Brooklyn"]`
   - Added "Duplex" to default property types

3. **[scrapers/zillow_scraper.py](scrapers/zillow_scraper.py)**
   - **Completely rewrote `_build_search_url()` method**
   - Now builds structured JSON query with all filters
   - URL format matches user's example
   - Filters embedded in search query:
     - `price.max: 2500000`
     - `beds.min: 5`
     - `baths.min: 4`
     - Property type restrictions

4. **[QUICKSTART.md](QUICKSTART.md)**
   - Updated to show filtering happens at Step 1
   - Changed target from 4 boroughs to Brooklyn only
   - Added region ID reference table

5. **[validate.py](validate.py)**
   - Updated validation to expect Brooklyn only
   - Added Duplex to valid property types

## 🆕 New Zillow URL Structure

The scraper now builds URLs like this:

```
https://www.zillow.com/brooklyn-new-york-ny/duplex/
?searchQueryState={
  "regionSelection": [{"regionId": 37607, "regionType": 17}],
  "filterState": {
    "price": {"max": 2500000},
    "beds": {"min": 5},
    "baths": {"min": 4},
    "sf": {"value": false},    # Exclude single family
    "tow": {"value": false},   # Exclude townhouse
    "con": {"value": false},   # Exclude condo
    ...
  },
  "usersSearchTerm": "Brooklyn New York NY"
}
```

**Result**: Zillow only returns properties that already meet our criteria!

## 📊 Benefits

1. **More Efficient**: Don't waste time scraping irrelevant properties
2. **Faster**: Fewer pages to process
3. **Accurate**: Zillow's own filters ensure data quality
4. **Focused**: All results are in Brooklyn with correct price/bed/bath
5. **Scalable**: Only need to check B units, not all other criteria

## 🚀 Usage

### Configuration is Pre-Set

The system is now configured for Brooklyn. Just run:

```bash
python validate.py  # Verify setup
python run.py       # Start scraping
```

### To Change to Another Borough

Edit `.env`:
```bash
ZILLOW_SEARCH_LOCATION=Manhattan, NY
ZILLOW_REGION_ID=12530
BOROUGHS=Manhattan
```

**Region IDs:**
- Brooklyn: 37607
- Manhattan: 12530
- Queens: 270915
- Bronx: 14286

### Test the URL

The scraper will log the built URL. You can test it manually in a browser to verify it's filtering correctly.

## ⚠️ Important Notes

### Why This Is Better

**Old Approach:**
1. Scrape 1000s of properties (all types, prices, locations)
2. Filter down to ~50 that meet criteria
3. Waste: 95%+ of scraped data discarded

**New Approach:**
1. Zillow only returns ~50 properties (pre-filtered)
2. Check B units on those 50
3. Waste: Minimal

### Zillow URL Complexity

The URL contains encoded JSON. The scraper handles this automatically using:
- Python's `json.dumps()` for structure
- `urllib.parse.quote()` for URL encoding

### What Still Gets Filtered Post-Scraping

Only ONE thing: **B units verification**

This can't be done in Zillow because B units are only in the HPD database.

## 🎯 Current System State

✅ **Brooklyn-only** focus  
✅ **Filters in Zillow URL** (price, beds, baths, type)  
✅ **HPD B-unit verification** (only post-filter needed)  
✅ **Multi-format export** (CSV, Excel, JSON)  
✅ **Investment scoring** (0-100 based on B units)

## 📞 Next Steps

1. Run `python validate.py` to confirm Brooklyn setup
2. Review `.env` file (it's pre-configured)
3. Run `python run.py` to start
4. Check `output/` directory for results

The system will now scrape ONLY Brooklyn properties that match your exact criteria!

---

**Updated**: January 17, 2026  
**Focus**: Brooklyn Multi-Family/Duplex with B Units  
**Filtering**: Applied at Zillow search level ✅
