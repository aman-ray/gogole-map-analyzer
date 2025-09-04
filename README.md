# Tradescout - Google Maps Tradesmen Finder

A Python CLI tool that discovers local tradespeople within a specified radius using Google Maps. Filters for businesses with ≤1 review, no website listed, and a visible phone number. Exports clean, deduplicated data to multiple formats.

## Features

- **Browser-based scraping** using Playwright for reliable Google Maps interaction
- **Geographic tiling system** for comprehensive coverage of search areas
- **Smart filtering** for businesses with minimal reviews and no website
- **Multiple export formats**: CSV, Parquet, SQLite, and JSONL
- **Deduplication** with intelligent caching
- **Human-like pacing** with jitter and backoff for respectful scraping
- **Resilient operation** with retries and error handling

## Installation

```bash
# Clone the repository
git clone https://github.com/aman-ray/gogole-map-analyzer.git
cd gogole-map-analyzer

# Install the package
pip install -e .

# Install Playwright browsers (REQUIRED for scraping)
playwright install chromium
```

**⚠️ Important**: You must run `playwright install chromium` after installation, otherwise you'll get 0 results.

## Usage

### Basic Usage

```bash
# Search around a specific address
tradescout --center "Lucan, Dublin" --radius-km 10 --output out/lucan

# Search using coordinates
tradescout --center "53.3498,-6.2603" --radius-km 10 --output out/dublin_center
```

### Advanced Usage

```bash
# Specific categories with higher limits
tradescout --center "53.3498,-6.2603" --radius-km 10 \
  --categories "plumber,heating engineer,locksmith" \
  --max-results 800 --concurrency 3 --output out/dublin_plumbers

# Debug mode with browser visible
tradescout --center "Tallaght, Dublin" --radius-km 5 \
  --no-headless --keep-trace --output out/tallaght_debug
```

## Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--center` | *required* | Center location (lat,lng or address) |
| `--radius-km` | 10 | Search radius in kilometers |
| `--categories` | See below | Comma-separated trade categories |
| `--max-results` | 500 | Maximum number of results |
| `--max-runtime-min` | 20 | Maximum runtime in minutes |
| `--concurrency` | 2 | Number of concurrent browsers |
| `--headless` | true | Run browser in headless mode |
| `--output` | "out" | Output file prefix |
| `--keep-trace` | false | Keep browser traces for debugging |
| `--tile-size-km` | 2.5 | Geographic tile size |
| `--retry` | 3 | Number of retries per search |
| `--jitter-ms` | 350 | Random delay between requests |
| `--log-level` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `--log-dir` | logs | Directory for log files |

## Default Categories

```
plumber, electrician, carpenter, roofer, painter, tiler, locksmith, 
plasterer, handyman, heating engineer, glazier, pest control, 
landscaper, gardener, chimney sweep
```

## Data Model

Each business record includes:

- `place_name` - Business name
- `category` - Trade category searched
- `rating` - Google Maps rating (if available)
- `review_count` - Number of reviews (≤1 for included results)
- `website` - Website URL (empty for included results)
- `phone` - Phone number (required, normalized to E.164)
- `address_full` - Complete address
- `locality` - City/town
- `postal_code` - Postal/ZIP code
- `lat`/`lng` - Coordinates
- `maps_profile_url` - Google Maps profile URL
- `source` - Data source ("maps_ui")
- `scraped_at` - Timestamp (UTC ISO8601)
- `dedupe_key` - Unique identifier for deduplication

## Output Formats

The tool exports to four formats:

- **CSV** (`output.csv`) - For spreadsheet analysis
- **Parquet** (`output.parquet`) - For data analysis tools
- **SQLite** (`output.sqlite`) - For SQL queries
- **JSONL** (`output.jsonl`) - For JSON processing

## Architecture

1. **Geographic Tiling** - Divides search area into overlapping tiles
2. **Browser Automation** - Uses Playwright to interact with Google Maps
3. **Data Extraction** - Parses business information from map listings
4. **Filtering** - Applies inclusion criteria (≤1 review, no website, has phone)
5. **Deduplication** - Uses normalized name+phone combinations
6. **Export** - Outputs to multiple formats simultaneously

## Compliance & Ethics

- Scrapes only publicly visible information
- Uses human-like pacing with delays and jitter
- Respects rate limits and implements backoff
- Handles cookie consent gracefully
- Does not attempt to bypass any restrictions

## Troubleshooting

### "0 Results" Issue

**Problem**: Always getting 0 results from searches.

**Cause**: Missing Playwright browser installation.

**Solution**:
```bash
playwright install chromium
```

### Common Issues

1. **"No listings found"** - Try reducing tile size or checking the location
2. **"Browser not found"** - Run `playwright install chromium`
3. **"Geocoding failed"** - Use coordinates instead of address
4. **"Export failed"** - Check disk space and permissions

### Debug Mode

Run with debug logging to diagnose issues:
```bash
tradescout --center "Dublin, Ireland" --radius-km 5 --log-level DEBUG --no-headless
```

### Logs

- Log files are created in `logs/` directory with date format: `tradescout_YYYY-MM-DD.log`
- Use `tail -f logs/tradescout_$(date +%Y-%m-%d).log` to monitor real-time logging
- Different log levels: DEBUG, INFO, WARNING, ERROR

## Examples

### Find Dublin Plumbers
```bash
tradescout --center "Dublin, Ireland" --radius-km 15 \
  --categories "plumber,heating engineer" \
  --max-results 200 --output data/dublin_plumbers
```

### Quick Local Search
```bash
tradescout --center "51.5074,-0.1278" --radius-km 5 \
  --max-runtime-min 10 --output quick_search
```

### Comprehensive Area Survey
```bash
tradescout --center "Manchester, UK" --radius-km 20 \
  --max-results 1000 --concurrency 4 \
  --max-runtime-min 45 --output survey/manchester
```

## License

MIT License - see LICENSE file for details.