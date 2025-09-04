#!/usr/bin/env python3
"""Test consent handling specifically."""

import asyncio
from playwright.async_api import async_playwright

async def test_consent_handling():
    """Test different methods of handling Google consent."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Navigate to Google Maps with a search
        query = "restaurant near 53.3498,-6.2603"
        maps_url = f"https://www.google.com/maps/search/{query}"
        
        print(f"Navigating to: {maps_url}")
        await page.goto(maps_url)
        
        # Wait for page to load
        await page.wait_for_timeout(3000)
        
        print(f"Current URL: {page.url}")
        print(f"Page title: {await page.title()}")
        
        # Check if we're on consent page
        if "consent.google.com" in page.url:
            print("✓ Detected consent page")
            
            # Save screenshot before consent
            await page.screenshot(path="consent_before.png")
            print("Saved consent_before.png")
            
            # Test different consent selectors
            consent_selectors = [
                'button:has-text("Accept all")',
                'button:has-text("I agree")', 
                'button:has-text("Accept")',
                'form[action*="consent"] button',
                '[data-testid="accept-all"]',
                '.VfPpkd-LgbsSe',
                'input[type="submit"]',
                'button[type="submit"]',
                'div[role="button"]',
                'button',
                'form button'
            ]
            
            consent_handled = False
            for selector in consent_selectors:
                try:
                    print(f"Testing selector: {selector}")
                    elements = await page.query_selector_all(selector)
                    print(f"  Found {len(elements)} elements")
                    
                    if elements:
                        for i, elem in enumerate(elements):
                            try:
                                text = await elem.text_content()
                                is_visible = await elem.is_visible()
                                print(f"    Element {i+1}: visible={is_visible}, text='{text.strip() if text else 'No text'}'")
                                
                                # Try clicking if it looks like an accept button
                                if is_visible and text and any(word in text.lower() for word in ['accept', 'agree', 'continue']):
                                    print(f"    Attempting to click: {text.strip()}")
                                    await elem.click()
                                    await page.wait_for_timeout(3000)
                                    
                                    new_url = page.url
                                    print(f"    After click, URL: {new_url}")
                                    
                                    if "consent.google.com" not in new_url:
                                        print("    ✓ Consent handled successfully!")
                                        consent_handled = True
                                        break
                                    else:
                                        print("    Still on consent page")
                            except Exception as e:
                                print(f"    Error with element {i+1}: {e}")
                        
                        if consent_handled:
                            break
                            
                except Exception as e:
                    print(f"  Error testing selector {selector}: {e}")
            
            if consent_handled:
                # Save screenshot after consent
                await page.screenshot(path="consent_after.png")
                print("Saved consent_after.png")
                
                # Wait for maps to load
                await page.wait_for_timeout(5000)
                
                # Check for listings now
                print("\nChecking for listings after consent...")
                listing_selectors = [
                    '[data-result-index]',
                    'a[href*="/maps/place/"]', 
                    '.hfpxzc',
                    'div[role="article"]',
                    '.lI9IFe'
                ]
                
                for selector in listing_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        print(f"{selector}: {len(elements)} elements found")
                    except Exception as e:
                        print(f"{selector}: Error - {e}")
                
                # Save final screenshot
                await page.screenshot(path="maps_with_listings.png") 
                print("Saved maps_with_listings.png")
            else:
                print("✗ Could not handle consent")
        else:
            print("No consent page detected")
        
        # Keep browser open for inspection
        print("\nKeeping browser open for 20 seconds...")
        await page.wait_for_timeout(20000)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_consent_handling())
