"""Playwright-based Google Maps scraper."""

import asyncio
import time
import re
from typing import List, Optional, Tuple
try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
except ImportError:
    # Import warning will be logged instead of printed
    from .logging_config import warning
    warning("Playwright not available. Install with: playwright install chromium", print_msg=True)
    # Define minimal stubs for testing
    class Page: pass
    class Browser: pass
    class BrowserContext: pass
    def async_playwright(): pass
from .models import Business, Tile, SearchConfig
from .utils import (
    normalize_phone, normalize_website, clean_text, 
    extract_rating, extract_review_count, sleep_with_jitter,
    exponential_backoff, haversine_distance, calculate_zoom_level
)
from .cache import DedupeCache, ResultsCache
from .logging_config import get_logger, debug, info, warning, error


class GoogleMapsScraper:
    """Scrapes Google Maps for business listings."""
    
    def __init__(self, config: SearchConfig):
        self.config = config
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.start_time = time.time()
        self.logger = get_logger('scraper')
    
    async def __aenter__(self):
        """Async context manager entry."""
        debug("Initializing browser for scraping", print_msg=False)
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
        
        debug(f"Browser initialized (headless: {self.config.headless})", print_msg=False)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        debug("Closing browser", print_msg=False)
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
    
    async def search_tile_category(self, tile: Tile, category: str, 
                                 dedupe_cache: DedupeCache, results_cache: ResultsCache) -> int:
        """Search a specific tile for a category."""
        query = f"{category} near {tile.center_lat},{tile.center_lng}"
        debug(f"Starting search for '{query}'", print_msg=False)
        
        page = await self.context.new_page()
        found_count = 0
        
        try:
            # Navigate to Google Maps - using original URL format for now
            maps_url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
            debug(f"Navigating to: {maps_url}", print_msg=False)
            await page.goto(maps_url, wait_until='networkidle')
            
            # Handle cookie consent if present
            await self._handle_consent_dialog(page)
            
            # Wait for results to load
            await page.wait_for_timeout(2000)
            
            # Scroll and collect listings
            debug("Collecting listings from page", print_msg=False)
            listings = await self._scroll_and_collect_listings(page)
            info(f"Found {len(listings)} listings for {category} in tile", print_msg=False)
            
            # Process each listing
            for listing_data in listings[:60]:  # Per-tile limit
                if self._should_stop():
                    debug("Stopping due to time limit", print_msg=False)
                    break
                
                try:
                    business = await self._extract_business_data(
                        page, listing_data, category, tile
                    )
                    
                    if business and self._is_in_radius(business):
                        if results_cache.add_business(business, dedupe_cache):
                            found_count += 1
                            print(f"Found: {business.place_name} ({business.category})")
                            info(f"Added business: {business.place_name} - {business.phone}", print_msg=False)
                        else:
                            debug(f"Duplicate business filtered: {business.place_name}", print_msg=False)
                        
                        if results_cache.size() >= self.config.max_results:
                            debug("Reached maximum results limit", print_msg=False)
                            break
                
                except Exception as e:
                    error_msg = f"Error processing listing: {e}"
                    debug(error_msg, print_msg=False)
                    continue
                
                # Add jitter between listings
                sleep_with_jitter(0.1, self.config.jitter_ms)
        
        except Exception as e:
            error_msg = f"Error searching {category} in tile: {e}"
            error(error_msg, print_msg=False)
        
        finally:
            await page.close()
        
        debug(f"Search completed for {category} in tile: {found_count} businesses found", print_msg=False)
        return found_count
    
    async def _handle_consent_dialog(self, page: Page):
        """Handle cookie consent dialogs."""
        # Check if we're on a consent page
        if "consent.google.com" in page.url:
            debug("Detected Google consent page", print_msg=False)
            
            consent_selectors = [
                'button:has-text("Accept all")',
                'button:has-text("I agree")',
                'button:has-text("Accept")',
                'form[action*="consent"] button:has-text("Accept all")',
                '[data-testid="accept-all"]',
                '.VfPpkd-LgbsSe[jsname="V67aGc"]'  # Google's accept button
            ]
            
            for selector in consent_selectors:
                try:
                    consent_button = page.locator(selector).first
                    if await consent_button.is_visible(timeout=3000):
                        debug(f"Clicking consent button: {selector}", print_msg=False)
                        await consent_button.click()
                        await page.wait_for_timeout(2000)
                        debug(f"Consent handled, new URL: {page.url}", print_msg=False)
                        return True
                except Exception as e:
                    debug(f"Failed to click consent button {selector}: {e}", print_msg=False)
                    continue
            
            debug("Could not handle consent dialog", print_msg=False)
            return False
        
        return True  # No consent page detected
    
    async def _scroll_and_collect_listings(self, page: Page) -> List[str]:
        """Scroll through the listings panel and collect all listing selectors."""
        listings = []
        
        # Updated selectors for current Google Maps interface
        listing_selectors = [
            'a[href*="/maps/place/"]',
            '.hfpxzc',
            '.lI9IFe',
            '[data-result-index]',  # Keep as fallback
            '.Nv2PK',
            '[jsaction*="mouseover:pane"]',
            '.bfdHYd'
        ]
        
        for selector in listing_selectors:
            try:
                await page.wait_for_selector(selector, timeout=5000)
                debug(f"Found listings with selector: {selector}", print_msg=False)
                break
            except:
                continue
        else:
            warning("Could not find listings panel", print_msg=False)
            return []
        
        # Use the first working selector for collecting listings
        working_selector = None
        for selector in listing_selectors:
            try:
                current_listings = await page.query_selector_all(selector)
                if len(current_listings) > 0:
                    working_selector = selector
                    debug(f"Using selector: {selector} ({len(current_listings)} listings)", print_msg=False)
                    break
            except:
                continue
        
        if not working_selector:
            warning("No working listing selector found", print_msg=False)
            return []
        
        # Scroll and collect
        last_count = 0
        scroll_attempts = 0
        max_scrolls = 10
        
        while scroll_attempts < max_scrolls:
            # Get current listings using the working selector
            current_listings = await page.query_selector_all(working_selector)
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
        
        # Return all found listings with the working selector
        final_listings = await page.query_selector_all(working_selector)
        debug(f"Final count: {len(final_listings)} listings", print_msg=False)
        
        # Return tuple of (selector, index) for each listing
        return [(working_selector, i) for i in range(len(final_listings))]
    
    async def _extract_business_data(self, page: Page, listing_data: tuple, 
                                   category: str, tile: Tile) -> Optional[Business]:
        """Extract business data from a listing."""
        try:
            selector, index = listing_data
            listings = await page.query_selector_all(selector)
            
            if index >= len(listings):
                debug(f"Listing index {index} out of range", print_msg=False)
                return None
            
            listing_element = listings[index]
            
            # Get initial URL for comparison
            initial_url = page.url
            debug(f"Clicking listing {index}, initial URL: {initial_url}", print_msg=False)
            
            # Click on the listing to get details - improved navigation
            try:
                # Try different click approaches for better reliability
                await listing_element.scroll_into_view_if_needed()
                await listing_element.click(timeout=5000)
                
                # Wait for navigation to business detail page
                # Check if URL changed indicating navigation to business page
                for attempt in range(10):  # Up to 3 seconds
                    await page.wait_for_timeout(300)
                    current_url = page.url
                    if current_url != initial_url and '/maps/place/' in current_url:
                        debug(f"Navigation successful to: {current_url}", print_msg=False)
                        break
                else:
                    debug(f"Navigation may not have completed, URL: {page.url}", print_msg=False)
                
                # Additional wait for business details to load
                await page.wait_for_timeout(1000)
                
            except Exception as click_error:
                debug(f"Error clicking listing: {click_error}", print_msg=False)
                return None
            
            # Extract basic info with improved selectors
            name = await self._extract_business_name(page)
            if not name:
                debug("Could not extract business name with any selector", print_msg=False)
            
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
            
            # Debug: Log what we found
            debug(f"Extracted data - Name: {name}, Phone: {phone}, Address: {address}", print_msg=False)
            
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
                
                debug(f"Successfully created business: {business.place_name}", print_msg=False)
                return business
            else:
                debug(f"Missing required fields - Name: {name}, Phone: {phone}", print_msg=False)
        
        except Exception as e:
            error(f"Error extracting business data: {e}", print_msg=False)
            # Optional: Save screenshot for debugging on failures
            try:
                screenshot_path = f"/tmp/extraction_error_{int(time.time())}.png"
                await page.screenshot(path=screenshot_path)
                debug(f"Saved error screenshot: {screenshot_path}", print_msg=False)
            except:
                pass  # Don't fail the whole extraction if screenshot fails
        
        return None
    
    async def _extract_business_name(self, page: Page) -> Optional[str]:
        """Extract business name with improved selectors for current Google Maps."""
        # Updated selectors based on current Google Maps interface (2024)
        name_selectors = [
            # Primary selectors for business name
            'h1[data-attrid="title"]',  # Most common current selector
            'h1',  # Fallback h1
            '[data-attrid="title"]',  # Data attribute selector
            
            # Alternative selectors for different business page layouts
            '.DUwDvf',  # Business name class
            '.x3AX1-LfntMc-header-title-title',  # Header title
            '.lMbq3e',  # Alternative name class
            '.qrShPb',  # Another business name selector
            '.fontHeadlineLarge',  # Typography-based selector
            
            # Fallback selectors
            '[data-value]',  # Generic data-value selector
            '.section-hero-header-title-title',  # Section header
            '.section-hero-header h1'  # Hero section title
        ]
        
        for selector in name_selectors:
            try:
                element = page.locator(selector).first
                if await element.is_visible(timeout=1000):
                    text = await element.inner_text()
                    if text and text.strip() and len(text.strip()) > 1:
                        # Filter out common non-business text
                        text = text.strip()
                        if text.lower() not in ['results', 'map', 'directions', 'save', 'share', 'more']:
                            debug(f"Found business name '{text}' with selector: {selector}", print_msg=False)
                            return text
            except Exception as e:
                debug(f"Name selector {selector} failed: {e}", print_msg=False)
                continue
        
        debug("Could not extract business name with any selector", print_msg=False)
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
        """Extract phone number from the page with improved selectors."""
        # Updated phone selectors for current Google Maps interface
        phone_selectors = [
            # Primary phone selectors
            '[data-attrid*="phone"]',  # Data attribute for phone
            '[data-value*="+"]',  # Data value with phone number
            '[data-attrid="kc:/collection/knowledge_panels/local_reviewable:phone"]',  # Specific phone attribute
            
            # Alternative phone selectors
            'span[dir="ltr"]',  # LTR direction span (often used for phone numbers)
            '.rogA2c',  # Phone number class
            
            # New selectors for 2024 Google Maps
            'button[data-value*="tel:"]',  # Tel protocol button
            'a[href*="tel:"]',  # Tel protocol link
            '[aria-label*="phone" i]',  # Aria label with phone
            '[aria-label*="call" i]',  # Aria label with call
            
            # Generic selectors that might contain phone numbers
            '.fontBodyMedium span[dir="ltr"]',  # Body text with phone
            '.Io6YTe',  # Contact information class
            '.CL9Uqc span',  # Contact span
            
            # Fallback - look for any text that looks like a phone number
            'span:not([class])',  # Generic spans
        ]
        
        for selector in phone_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    text = await element.inner_text()
                    if text and re.search(r'[\d\+\(\)\-\s]{7,}', text):
                        # Additional validation for phone number format
                        cleaned_phone = re.sub(r'[^\d\+\(\)\-\s]', '', text.strip())
                        if len(re.sub(r'\D', '', cleaned_phone)) >= 7:  # At least 7 digits
                            debug(f"Found phone '{text.strip()}' with selector: {selector}", print_msg=False)
                            return text.strip()
            except Exception as e:
                debug(f"Phone selector {selector} failed: {e}", print_msg=False)
                continue
        
        debug("Could not extract phone number with any selector", print_msg=False)
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
        """Extract address from the page with improved selectors."""
        # Updated address selectors for current Google Maps interface
        address_selectors = [
            # Primary address selectors
            '[data-attrid*="address"]',  # Data attribute for address
            '[data-attrid="kc:/collection/knowledge_panels/local_reviewable:address"]',  # Specific address attribute
            
            # Alternative address selectors
            '.LrzXr',  # Address class
            '.fccl3c',  # Alternative address class
            
            # New selectors for 2024 Google Maps
            'button[data-value*="directions"]',  # Directions button often contains address
            '.Io6YTe',  # Contact information section
            '.rogA2c:not([data-attrid*="phone"])',  # Contact class excluding phone
            
            # Generic address pattern selectors
            '[aria-label*="address" i]',  # Aria label with address
            '.fontBodyMedium:has-text(",")',  # Text with comma (address format)
            
            # Fallback selectors
            'div[data-value*=","]',  # Data value with comma
            'span:has-text(",")',  # Span containing comma-separated text
        ]
        
        for selector in address_selectors:
            try:
                address = await self._extract_text(page, selector)
                if address and ',' in address and len(address) > 10:  # Basic address validation
                    debug(f"Found address '{address}' with selector: {selector}", print_msg=False)
                    return address
            except Exception as e:
                debug(f"Address selector {selector} failed: {e}", print_msg=False)
                continue
        
        debug("Could not extract address with any selector", print_msg=False)
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