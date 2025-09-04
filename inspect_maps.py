#!/usr/bin/env python3
"""Quick test to see what's actually on the Google Maps page."""

import asyncio
from playwright.async_api import async_playwright

async def inspect_google_maps():
    """Navigate to Google Maps and inspect the page structure."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Navigate to Google Maps with a search
        query = "restaurant near 53.3498,-6.2603"
        maps_url = f"https://www.google.com/maps/search/{query}"
        
        print(f"Navigating to: {maps_url}")
        await page.goto(maps_url)
        
        # Wait for page to load
        await page.wait_for_timeout(5000)
        
        # Check for common listing selectors
        selectors_to_test = [
            '[data-result-index]',
            '.Nv2PK',
            '[jsaction*="mouseover"]',
            '.bfdHYd',
            'div[role="article"]',
            'a[href*="/maps/place/"]',
            '[data-value="Directions"]',
            '.hfpxzc',  # Common Google Maps listing class
            '.VkpGBb',  # Another common class
            '.lI9IFe',  # Business name container
            '.W4Efsd',  # Rating container
        ]
        
        print("\nTesting selectors...")
        for selector in selectors_to_test:
            try:
                elements = await page.query_selector_all(selector)
                count = len(elements)
                print(f"{selector}: {count} elements found")
                
                if count > 0 and count < 10:  # Show details for a reasonable number
                    for i, elem in enumerate(elements[:3]):  # Show first 3
                        try:
                            text = await elem.text_content()
                            if text and text.strip():
                                print(f"  {i+1}: {text.strip()[:100]}")
                        except:
                            pass
            except Exception as e:
                print(f"{selector}: Error - {e}")
        
        # Get page title and URL to confirm we're on the right page
        title = await page.title()
        url = page.url
        print(f"\nPage title: {title}")
        print(f"Current URL: {url}")
        
        # Save a screenshot
        await page.screenshot(path="maps_inspection.png")
        print("Screenshot saved as maps_inspection.png")
        
        # Keep browser open for manual inspection
        print("\nBrowser will stay open for 30 seconds for manual inspection...")
        await page.wait_for_timeout(30000)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_google_maps())
