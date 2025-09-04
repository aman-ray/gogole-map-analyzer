#!/usr/bin/env python3
"""Simple test to check if scraper can find any listings."""

import asyncio
import logging
from tradescout.scraper import GoogleMapsScraper
from tradescout.models import SearchConfig
from tradescout.tiling import generate_tiles
from tradescout.cache import DedupeCache, ResultsCache

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

async def test_simple_scraping():
    """Test basic scraping functionality."""
    logger = logging.getLogger(__name__)
    
    # Simple config for Dublin center
    config = SearchConfig(
        center_lat=53.3498,
        center_lng=-6.2603,
        radius_km=1.0,
        max_results=3,
        max_runtime_min=2,
        categories=["plumber"],
        tile_size_km=1.0,
        concurrency=1,
        max_review_count=10,
        headless=False
    )
    
    logger.info(f"Testing scraper with config: {config}")
    
    # Generate a single tile
    tiles = generate_tiles(config.center_lat, config.center_lng, config.radius_km, config.tile_size_km)
    
    logger.info(f"Generated {len(tiles)} tiles")
    
    # Use just the first tile
    if tiles:
        tile = tiles[0]
        logger.info(f"Testing with tile: center=({tile.center_lat}, {tile.center_lng})")
        
        # Initialize scraper and caches
        dedupe_cache = DedupeCache()
        results_cache = ResultsCache(".cache", config)
        
        async with GoogleMapsScraper(config) as scraper:
            try:
                # Search for businesses in this tile
                found_count = await scraper.search_tile_category(tile, "plumber", dedupe_cache, results_cache)
                
                logger.info(f"Found {found_count} businesses")
                
                # Get the businesses from the results cache
                businesses = results_cache.get_results()
                
                for i, business in enumerate(businesses):
                    logger.info(f"Business {i+1}: {business.name} - {business.review_count} reviews")
                    
            except Exception as e:
                logger.error(f"Error during scraping: {e}", exc_info=True)
    else:
        logger.error("No tiles generated")

if __name__ == "__main__":
    asyncio.run(test_simple_scraping())
