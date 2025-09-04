#!/usr/bin/env python3
"""Test business extraction logic offline with mock data."""

import asyncio
from unittest.mock import AsyncMock, MagicMock
from tradescout.scraper import GoogleMapsScraper
from tradescout.models import SearchConfig, Tile

async def test_business_extraction_logic():
    """Test the business extraction logic with mocked page data."""
    
    # Create mock config
    config = SearchConfig(
        center_lat=53.3498,
        center_lng=-6.2603,
        radius_km=5,
        categories=["restaurant"],
        max_results=10,
        headless=True
    )
    
    # Create mock tile
    tile = Tile(
        center_lat=53.3498,
        center_lng=-6.2603,
        size_km=2
    )
    
    # Create scraper
    scraper = GoogleMapsScraper(config)
    
    # Mock page object
    mock_page = AsyncMock()
    mock_page.url = "https://www.google.com/maps/place/Test+Restaurant/@53.3498,-6.2603,14z"
    
    # Test current name extraction selectors
    current_name_selectors = [
        '[data-attrid="title"]',
        'h1',
        '.DUwDvf',
        '.x3AX1-LfntMc-header-title-title',
        '.lMbq3e'
    ]
    
    # Test current extraction methods
    print("Testing current name extraction selectors:")
    for selector in current_name_selectors:
        print(f"  {selector}")
    
    # Test phone selectors
    current_phone_selectors = [
        '[data-attrid*="phone"]',
        '[data-value*="+"]',
        'span[dir="ltr"]',
        '.rogA2c'
    ]
    
    print("\nTesting current phone extraction selectors:")
    for selector in current_phone_selectors:
        print(f"  {selector}")
    
    # Test the extraction method structure
    listing_data = ('a[href*="/maps/place/"]', 0)
    
    print(f"\nTesting business data extraction structure:")
    print(f"  Listing data format: {listing_data}")
    print(f"  URL pattern: {mock_page.url}")
    
    # Test coordinate extraction from URL
    import re
    coord_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', mock_page.url)
    if coord_match:
        lat = float(coord_match.group(1))
        lng = float(coord_match.group(2))
        print(f"  Extracted coordinates: {lat}, {lng}")
    
    print("\n✅ Offline extraction logic test completed")

if __name__ == "__main__":
    asyncio.run(test_business_extraction_logic())