#!/usr/bin/env python3
"""Debug scraper with screenshots when no results found."""

import asyncio
import logging
from tradescout.scraper import GoogleMapsScraper
from tradescout.models import SearchConfig
from tradescout.tiling import generate_tiles
from tradescout.cache import DedupeCache, ResultsCache
from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

async def debug_scraper_with_screenshots():
    """Debug scraper and save screenshots when no results found."""
    logger = logging.getLogger(__name__)
    
    # Simple config for Dublin center
    config = SearchConfig(
        center_lat=53.3498,
        center_lng=-6.2603,
        radius_km=0.5,
        max_results=1,
        max_runtime_min=1,
        categories=["restaurant"],  # Try restaurant instead of plumber
        tile_size_km=0.5,
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
                # Navigate to Google Maps directly to debug
                page = await scraper.context.new_page()
                
                # Build the URL manually
                query = f"restaurant near {tile.center_lat},{tile.center_lng}"
                maps_url = f"https://www.google.com/maps/search/{query}"
                
                logger.info(f"Navigating to: {maps_url}")
                await page.goto(maps_url)
                
                # Wait a bit for the page to load
                await page.wait_for_timeout(3000)
                
                # Save screenshot
                await page.screenshot(path="debug_maps_initial.png")
                logger.info("Saved debug_maps_initial.png")
                
                # Check for consent dialog
                consent_selectors = [
                    "form[action*='consent'] button",
                    "[data-value='accept'] button", 
                    "#L2AGLb",
                    "button:has-text('Accept all')",
                    "button:has-text('I agree')",
                    "button:has-text('Accept')"
                ]
                
                consent_handled = False
                for selector in consent_selectors:
                    try:
                        consent_button = page.locator(selector).first
                        if await consent_button.is_visible(timeout=2000):
                            logger.info(f"Found consent dialog with selector: {selector}")
                            await consent_button.click()
                            await page.wait_for_timeout(2000)
                            consent_handled = True
                            break
                    except Exception as e:
                        logger.debug(f"Consent selector {selector} not found: {e}")
                
                if consent_handled:
                    await page.screenshot(path="debug_maps_after_consent.png")
                    logger.info("Saved debug_maps_after_consent.png")
                else:
                    logger.info("No consent dialog found")
                
                # Wait for listings to load
                await page.wait_for_timeout(5000)
                
                # Save final screenshot
                await page.screenshot(path="debug_maps_final.png")
                logger.info("Saved debug_maps_final.png")
                
                # Check for listings
                listing_selectors = [
                    "div[jsaction*='mouseover'] a[href*='/maps/place/']",
                    "a[data-value='Directions']",
                    "div[role='article']",
                    "[data-result-index]"
                ]
                
                listings_found = 0
                for selector in listing_selectors:
                    try:
                        listings = page.locator(selector)
                        count = await listings.count()
                        if count > 0:
                            logger.info(f"Found {count} elements with selector: {selector}")
                            listings_found = count
                            break
                    except Exception as e:
                        logger.debug(f"Listing selector {selector} failed: {e}")
                
                logger.info(f"Total listings found with manual selectors: {listings_found}")
                
                # Now try the actual scraper method
                found_count = await scraper.search_tile_category(tile, "restaurant", dedupe_cache, results_cache)
                
                logger.info(f"Scraper found: {found_count} businesses")
                
                # Get the businesses from the results cache
                businesses = results_cache.get_results()
                
                for i, business in enumerate(businesses):
                    logger.info(f"Business {i+1}: {business.name} - {business.review_count} reviews")
                    
                await page.close()
                    
            except Exception as e:
                logger.error(f"Error during scraping: {e}", exc_info=True)
    else:
        logger.error("No tiles generated")

if __name__ == "__main__":
    asyncio.run(debug_scraper_with_screenshots())
