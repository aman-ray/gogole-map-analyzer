#!/usr/bin/env python3
"""Enhanced test for business extraction with improved selectors."""

import asyncio
from playwright.async_api import async_playwright

async def test_improved_business_extraction():
    """Test improved business extraction with better navigation and selectors."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Navigate to Google Maps
        query = "restaurant near 53.3498,-6.2603"
        maps_url = f"https://www.google.com/maps/search/{query}"
        
        print(f"🌐 Navigating to: {maps_url}")
        await page.goto(maps_url)
        await page.wait_for_timeout(3000)
        
        # Handle consent if needed
        if "consent.google.com" in page.url:
            print("🍪 Handling consent...")
            try:
                consent_button = page.locator('button:has-text("Accept all")').first
                await consent_button.click()
                await page.wait_for_timeout(3000)
                print("✅ Consent handled")
            except Exception as e:
                print(f"❌ Consent error: {e}")
        
        # Wait for listings to load
        await page.wait_for_timeout(5000)
        
        # Find listings
        selector = 'a[href*="/maps/place/"]'
        listings = await page.query_selector_all(selector)
        print(f"📍 Found {len(listings)} listings")
        
        if listings:
            # Try clicking the first listing with improved navigation
            try:
                initial_url = page.url
                print(f"🖱️  Clicking first listing... (initial URL: {initial_url})")
                
                # Improved clicking with scroll and wait
                await listings[0].scroll_into_view_if_needed()
                await listings[0].click()
                
                # Wait for navigation to business detail page
                navigation_success = False
                for attempt in range(10):  # Up to 3 seconds
                    await page.wait_for_timeout(300)
                    current_url = page.url
                    if current_url != initial_url and '/maps/place/' in current_url:
                        print(f"✅ Navigation successful to: {current_url}")
                        navigation_success = True
                        break
                
                if not navigation_success:
                    print(f"⚠️  Navigation may not have completed, URL: {page.url}")
                
                # Wait for details to load
                await page.wait_for_timeout(1000)
                
                # Test improved name extraction selectors
                name_selectors = [
                    'h1[data-attrid="title"]',
                    'h1',
                    '[data-attrid="title"]',
                    '.DUwDvf',
                    '.x3AX1-LfntMc-header-title-title',
                    '.lMbq3e',
                    '.qrShPb',
                    '.fontHeadlineLarge'
                ]
                
                name = None
                for name_sel in name_selectors:
                    try:
                        name_elem = await page.query_selector(name_sel)
                        if name_elem:
                            text = await name_elem.text_content()
                            if text and text.strip() and len(text.strip()) > 1:
                                text = text.strip()
                                if text.lower() not in ['results', 'map', 'directions', 'save', 'share', 'more']:
                                    print(f"✅ Found name with {name_sel}: '{text}'")
                                    name = text
                                    break
                    except Exception as e:
                        print(f"⚠️  Name selector {name_sel} failed: {e}")
                
                if not name:
                    print("❌ Could not extract business name with improved selectors")
                
                # Test improved phone extraction
                phone_selectors = [
                    '[data-attrid*="phone"]',
                    '[data-value*="+"]',
                    'span[dir="ltr"]',
                    'button[data-value*="tel:"]',
                    'a[href*="tel:"]',
                    '[aria-label*="phone" i]',
                    '.rogA2c'
                ]
                
                phone = None
                for phone_sel in phone_selectors:
                    try:
                        phone_elem = await page.query_selector(phone_sel)
                        if phone_elem:
                            text = await phone_elem.text_content()
                            if text and '+' in text or any(c.isdigit() for c in text):
                                print(f"✅ Found phone with {phone_sel}: '{text.strip()}'")
                                phone = text.strip()
                                break
                    except Exception as e:
                        print(f"⚠️  Phone selector {phone_sel} failed: {e}")
                
                if not phone:
                    print("❌ Could not extract phone number with improved selectors")
                
                # Save screenshot for verification
                await page.screenshot(path="improved_extraction_test.png")
                print("📸 Saved improved_extraction_test.png")
                
                # Summary
                print(f"\n📊 Extraction Results:")
                print(f"   Name: {name}")
                print(f"   Phone: {phone}")
                print(f"   URL: {page.url}")
                
            except Exception as e:
                print(f"❌ Error in improved extraction: {e}")
        
        await browser.close()

if __name__ == "__main__":
    print("🧪 Testing Improved Business Extraction")
    print("=" * 50)
    asyncio.run(test_improved_business_extraction())