"""Playwright-based Google Maps scraper."""

import asyncio
import time
import re
from typing import List, Optional, Tuple
try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
except ImportError:
    print("Warning: Playwright not available. Install with: playwright install chromium")
    # Define minimal stubs for testing
    class Page: pass
    class Browser: pass
    class BrowserContext: pass
    def async_playwright(): pass
from .models import Business, Tile, SearchConfig
from .utils import (
    normalize_phone, normalize_website, clean_text, 
    extract_rating, extract_review_count, sleep_with_jitter,
    exponential_backoff, haversine_distance
)
from .cache import DedupeCache, ResultsCache


class GoogleMapsScraper:
    """Scrapes Google Maps for business listings."""
    
    def __init__(self, config: SearchConfig):
        self.config = config
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.start_time = time.time()
    
    async def __aenter__(self):
        """Async context manager entry."""
        playwright = await async_playwright().start()
        
        # Launch browser
        self.browser = await playwright.chromium.launch(
            headless=self.config.headless,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage'
            ]
        )
        
        # Create context with realistic settings
        self.context = await self.browser.new_context(
            viewport={'width': 1366, 'height': 768},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
    
    async def search_tile_category(self, tile: Tile, category: str, 
                                 dedupe_cache: DedupeCache, results_cache: ResultsCache) -> int:
        """Search a specific tile for a category."""
        query = f"{category} near {tile.center_lat},{tile.center_lng}"
        
        page = await self.context.new_page()
        found_count = 0
        
        try:
            # Navigate to Google Maps
            maps_url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
            await page.goto(maps_url, wait_until='networkidle')
            
            # Handle cookie consent if present
            await self._handle_consent_dialog(page)
            
            # Wait for results to load
            await page.wait_for_timeout(2000)
            
            # Scroll and collect listings
            listings = await self._scroll_and_collect_listings(page)
            
            # Process each listing
            for listing_selector in listings[:60]:  # Per-tile limit
                if self._should_stop():
                    break
                
                try:
                    business = await self._extract_business_data(
                        page, listing_selector, category, tile
                    )
                    
                    if business and self._is_in_radius(business):
                        if results_cache.add_business(business, dedupe_cache):
                            found_count += 1
                            print(f"Found: {business.place_name} ({business.category})")
                        
                        if results_cache.size() >= self.config.max_results:
                            break
                
                except Exception as e:
                    print(f"Error processing listing: {e}")
                    continue
                
                # Add jitter between listings
                sleep_with_jitter(0.1, self.config.jitter_ms)
        
        except Exception as e:
            print(f"Error searching {category} in tile: {e}")
        
        finally:
            await page.close()
        
        return found_count
    
    async def _handle_consent_dialog(self, page: Page):
        """Handle cookie consent dialogs."""
        consent_selectors = [
            'button:has-text("Accept all")',
            'button:has-text("I agree")',
            'button:has-text("Accept")',
            '[data-testid="accept-all"]',
            '.VfPpkd-LgbsSe[jsname="V67aGc"]'  # Google's accept button
        ]
        
        for selector in consent_selectors:
            try:
                consent_button = page.locator(selector).first
                if await consent_button.is_visible(timeout=2000):
                    await consent_button.click()
                    await page.wait_for_timeout(1000)
                    break
            except:
                continue
    
    async def _scroll_and_collect_listings(self, page: Page) -> List[str]:
        """Scroll through the listings panel and collect all listing selectors."""
        listings = []
        
        # Common selectors for listings
        listing_selectors = [
            '[data-result-index]',
            '.Nv2PK',
            '[jsaction*="mouseover:pane"]',
            '.bfdHYd'
        ]
        
        for selector in listing_selectors:
            try:
                await page.wait_for_selector(selector, timeout=5000)
                break
            except:
                continue
        else:
            print("Could not find listings panel")
            return []
        
        # Scroll and collect
        last_count = 0
        scroll_attempts = 0
        max_scrolls = 10
        
        while scroll_attempts < max_scrolls:
            # Get current listings
            current_listings = await page.query_selector_all(listing_selectors[0])
            current_count = len(current_listings)
            
            if current_count > last_count:
                last_count = current_count
                scroll_attempts = 0
            else:
                scroll_attempts += 1
            
            # Scroll down in the listings panel
            try:
                await page.evaluate("""
                    const panel = document.querySelector('[role="main"]') || 
                                 document.querySelector('.siAUzd') ||
                                 document.querySelector('.m6QErb');
                    if (panel) {
                        panel.scrollTop += 500;
                    }
                """)
                await page.wait_for_timeout(1000)
            except:
                break
        
        # Return all found listings
        final_listings = await page.query_selector_all(listing_selectors[0])
        return [f'[data-result-index="{i}"]' for i in range(len(final_listings))]
    
    async def _extract_business_data(self, page: Page, listing_selector: str, 
                                   category: str, tile: Tile) -> Optional[Business]:
        """Extract business data from a listing."""
        try:
            listing = page.locator(listing_selector).first
            
            # Click on the listing to get details
            await listing.click()
            await page.wait_for_timeout(1500)
            
            # Extract basic info
            name = await self._extract_text(page, '[data-attrid="title"]')
            if not name:
                name = await self._extract_text(page, 'h1')
            
            # Extract rating and reviews
            rating_text = await self._extract_text(page, '[data-attrid="kc:/collection/knowledge_panels/local_reviewable:star_score"]')
            rating = extract_rating(rating_text)
            
            review_text = await self._extract_text(page, '[data-attrid="kc:/collection/knowledge_panels/local_reviewable:review_count"]')
            review_count = extract_review_count(review_text)
            
            # Extract phone
            phone = await self._extract_phone(page)
            
            # Extract website
            website = await self._extract_website(page)
            
            # Extract address
            address = await self._extract_address(page)
            
            # Extract coordinates from URL or page
            lat, lng = await self._extract_coordinates(page)
            
            # Get Maps profile URL
            maps_url = page.url
            
            if name and phone:  # Minimum required fields
                business = Business(
                    place_name=clean_text(name),
                    category=category,
                    rating=rating,
                    review_count=review_count,
                    website=normalize_website(website),
                    phone=normalize_phone(phone),
                    address_full=clean_text(address),
                    locality=None,  # Could extract from address
                    postal_code=None,  # Could extract from address
                    lat=lat,
                    lng=lng,
                    maps_profile_url=maps_url
                )
                
                return business
        
        except Exception as e:
            print(f"Error extracting business data: {e}")
        
        return None
    
    async def _extract_text(self, page: Page, selector: str) -> Optional[str]:
        """Extract text from a selector."""
        try:
            element = page.locator(selector).first
            if await element.is_visible(timeout=1000):
                return await element.inner_text()
        except:
            pass
        return None
    
    async def _extract_phone(self, page: Page) -> Optional[str]:
        """Extract phone number from the page."""
        phone_selectors = [
            '[data-attrid*="phone"]',
            '[data-value*="+"]',
            'span[dir="ltr"]',
            '.rogA2c'
        ]
        
        for selector in phone_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    text = await element.inner_text()
                    if text and re.search(r'[\d\+\(\)\-\s]{7,}', text):
                        return text.strip()
            except:
                continue
        
        return None
    
    async def _extract_website(self, page: Page) -> Optional[str]:
        """Extract website URL from the page."""
        website_selectors = [
            '[data-attrid*="website"] a',
            'a[href^="http"]:not([href*="google"])',
            '.CL9Uqc a'
        ]
        
        for selector in website_selectors:
            try:
                element = page.locator(selector).first
                if await element.is_visible(timeout=1000):
                    href = await element.get_attribute('href')
                    if href and not 'google' in href:
                        return href
            except:
                continue
        
        return None
    
    async def _extract_address(self, page: Page) -> Optional[str]:
        """Extract address from the page."""
        address_selectors = [
            '[data-attrid*="address"]',
            '.LrzXr',
            '.fccl3c'
        ]
        
        for selector in address_selectors:
            address = await self._extract_text(page, selector)
            if address:
                return address
        
        return None
    
    async def _extract_coordinates(self, page: Page) -> Tuple[Optional[float], Optional[float]]:
        """Extract coordinates from the page or URL."""
        try:
            # Try to extract from URL
            url = page.url
            coord_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
            if coord_match:
                lat = float(coord_match.group(1))
                lng = float(coord_match.group(2))
                return (lat, lng)
            
            # Could try other methods here (page content, etc.)
            
        except:
            pass
        
        return (None, None)
    
    def _is_in_radius(self, business: Business) -> bool:
        """Check if business is within the search radius."""
        if not business.lat or not business.lng:
            return True  # Include if we can't determine location
        
        distance = haversine_distance(
            self.config.center_lat, self.config.center_lng,
            business.lat, business.lng
        )
        
        return distance <= self.config.radius_km
    
    def _should_stop(self) -> bool:
        """Check if we should stop scraping."""
        elapsed_time = time.time() - self.start_time
        max_time = self.config.max_runtime_min * 60
        
        return elapsed_time >= max_time