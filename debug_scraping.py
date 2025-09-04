#!/usr/bin/env python3
"""Debug script to test Google Maps scraping manually."""

import asyncio
from playwright.async_api import async_playwright

async def debug_google_maps():
    """Debug Google Maps scraping to see what's happening."""
    print("🔍 Debug: Testing Google Maps scraping...")
    
    playwright = await async_playwright().start()
    
    # Launch browser in non-headless mode so we can see what's happening
    browser = await playwright.chromium.launch(
        headless=False,
        args=[
            '--no-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage'
        ]
    )
    
    context = await browser.new_context(
        viewport={'width': 1366, 'height': 768},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    
    page = await context.new_page()
    
    try:
        # Test the exact URL that would be generated
        query = "plumber near 53.3498,-6.2603"
        maps_url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
        
        print(f"🌐 Navigating to: {maps_url}")
        await page.goto(maps_url, wait_until='networkidle')
        
        # Wait a bit for the page to fully load
        await page.wait_for_timeout(3000)
        
        # Check if we're on a consent page and try to handle it
        if "consent.google.com" in page.url:
            print("🍪 Detected consent page, trying to handle it...")
            
            # Look for consent buttons
            consent_selectors = [
                'button:has-text("Accept all")',
                'button:has-text("I agree")', 
                'button:has-text("Accept")',
                'button:has-text("Reject all")',
                '[data-testid="accept-all"]',
                '.VfPpkd-LgbsSe[jsname="V67aGc"]',
                'button[jsname="V67aGc"]',
                'form[action*="consent"] button',
                'button[type="submit"]',
                'input[type="submit"]'
            ]
            
            for selector in consent_selectors:
                try:
                    buttons = await page.query_selector_all(selector)
                    print(f"  Consent selector '{selector}': Found {len(buttons)} elements")
                    
                    for i, button in enumerate(buttons[:3]):
                        try:
                            text = await button.text_content()
                            is_visible = await button.is_visible()
                            print(f"    Button {i}: '{text}' (visible: {is_visible})")
                        except:
                            pass
                except Exception as e:
                    print(f"  Consent selector '{selector}': Error - {e}")
            
            # Try to click any visible consent button
            print("🖱️  Trying to click consent buttons...")
            consent_clicked = False
            
            for selector in consent_selectors:
                try:
                    consent_button = page.locator(selector).first
                    if await consent_button.is_visible(timeout=1000):
                        print(f"  Clicking button with selector: {selector}")
                        await consent_button.click()
                        await page.wait_for_timeout(3000)
                        consent_clicked = True
                        print(f"  ✅ Clicked consent button, new URL: {page.url}")
                        break
                except Exception as e:
                    print(f"  Failed to click {selector}: {e}")
                    continue
            
            if not consent_clicked:
                print("  ❌ Could not click any consent button")
        
        await page.wait_for_timeout(5000)
        
        print("📸 Taking screenshot for debugging...")
        await page.screenshot(path="debug_maps_screenshot.png")
        
        # Check if we can find any business listings
        print("🔍 Looking for business listings...")
        
        # Try multiple possible selectors that might contain listings
        selectors_to_try = [
            '[data-value="Directions"]',
            'div[jsaction*="pane"]',
            'div[role="main"] div[jsaction]',
            'div[data-value="Directions"]',
            '[data-value="Directions"]',
            'div[aria-label*="Results"]',
            'div[role="article"]',
            'a[data-value="Directions"]'
        ]
        
        for selector in selectors_to_try:
            try:
                elements = await page.query_selector_all(selector)
                print(f"  Selector '{selector}': Found {len(elements)} elements")
                
                if len(elements) > 0:
                    # Try to get some text from the first few elements
                    for i, element in enumerate(elements[:3]):
                        try:
                            text = await element.text_content()
                            if text and len(text.strip()) > 0:
                                print(f"    Element {i}: {text.strip()[:100]}...")
                        except:
                            pass
            except Exception as e:
                print(f"  Selector '{selector}': Error - {e}")
        
        # Check the page title and URL to see if we're on the right page
        title = await page.title()
        current_url = page.url
        print(f"📄 Page title: {title}")
        print(f"🔗 Current URL: {current_url}")
        
        # Wait a bit so we can manually inspect the browser
        print("⏳ Waiting 30 seconds for manual inspection...")
        await page.wait_for_timeout(30000)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        await page.screenshot(path="debug_error_screenshot.png")
    
    finally:
        await context.close()
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(debug_google_maps())
