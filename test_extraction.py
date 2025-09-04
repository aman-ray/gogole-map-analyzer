#!/usr/bin/env python3
"""Test just the business extraction part."""

import asyncio
from playwright.async_api import async_playwright

async def test_business_extraction():
    """Test clicking on actual listings and extracting data."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Navigate to Google Maps
        query = "restaurant near 53.3498,-6.2603"
        maps_url = f"https://www.google.com/maps/search/{query}"
        
        print(f"Navigating to: {maps_url}")
        await page.goto(maps_url)
        await page.wait_for_timeout(3000)
        
        # Handle consent if needed
        if "consent.google.com" in page.url:
            print("Handling consent...")
            try:
                consent_button = page.locator('button:has-text("Accept all")').first
                await consent_button.click()
                await page.wait_for_timeout(3000)
                print("Consent handled")
            except Exception as e:
                print(f"Consent error: {e}")
        
        # Wait for listings to load
        await page.wait_for_timeout(5000)
        
        # Find listings
        selector = 'a[href*="/maps/place/"]'
        listings = await page.query_selector_all(selector)
        print(f"Found {len(listings)} listings")
        
        if listings:
            # Try clicking the first listing
            try:
                print("Clicking first listing...")
                await listings[0].click()
                await page.wait_for_timeout(3000)
                
                # Try to extract name
                name_selectors = [
                    'h1',
                    '[data-attrid="title"]',
                    '.DUwDvf',
                    '.x3AX1-LfntMc-header-title-title',
                    '.lMbq3e'
                ]
                
                name = None
                for name_sel in name_selectors:
                    try:
                        name_elem = await page.query_selector(name_sel)
                        if name_elem:
                            name = await name_elem.text_content()
                            if name and name.strip():
                                print(f"Found name with {name_sel}: {name.strip()}")
                                break
                    except Exception as e:
                        print(f"Name selector {name_sel} failed: {e}")
                
                if not name:
                    print("Could not extract business name")
                
                # Save screenshot
                await page.screenshot(path="business_details.png")
                print("Saved business_details.png")
                
            except Exception as e:
                print(f"Error clicking listing: {e}")
        
        # Keep browser open for inspection
        print("Keeping browser open for 20 seconds...")
        await page.wait_for_timeout(20000)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_business_extraction())
