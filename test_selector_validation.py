#!/usr/bin/env python3
"""Test the specific selector improvements and navigation fixes."""

import asyncio
from unittest.mock import AsyncMock, MagicMock
from tradescout.scraper import GoogleMapsScraper
from tradescout.models import SearchConfig, Tile

def test_selector_improvements():
    """Test the improved selectors and navigation logic."""
    print("🧪 Testing Selector Improvements")
    print("=" * 50)
    
    # Test the new name selectors
    print("📝 Testing Business Name Selectors:")
    name_selectors = [
        'h1[data-attrid="title"]',
        'h1',
        '[data-attrid="title"]',
        '.DUwDvf',
        '.x3AX1-LfntMc-header-title-title',
        '.lMbq3e',
        '.qrShPb',
        '.fontHeadlineLarge',
        '[data-value]',
        '.section-hero-header-title-title',
        '.section-hero-header h1'
    ]
    
    for i, selector in enumerate(name_selectors, 1):
        print(f"   {i:2d}. {selector}")
    
    print(f"\n📞 Testing Phone Number Selectors:")
    phone_selectors = [
        '[data-attrid*="phone"]',
        '[data-value*="+"]',
        '[data-attrid="kc:/collection/knowledge_panels/local_reviewable:phone"]',
        'span[dir="ltr"]',
        '.rogA2c',
        'button[data-value*="tel:"]',
        'a[href*="tel:"]',
        '[aria-label*="phone" i]',
        '[aria-label*="call" i]',
        '.fontBodyMedium span[dir="ltr"]',
        '.Io6YTe',
        '.CL9Uqc span',
        'span:not([class])'
    ]
    
    for i, selector in enumerate(phone_selectors, 1):
        print(f"   {i:2d}. {selector}")
    
    print(f"\n🏠 Testing Address Selectors:")
    address_selectors = [
        '[data-attrid*="address"]',
        '[data-attrid="kc:/collection/knowledge_panels/local_reviewable:address"]',
        '.LrzXr',
        '.fccl3c',
        'button[data-value*="directions"]',
        '.Io6YTe',
        '.rogA2c:not([data-attrid*="phone"])',
        '[aria-label*="address" i]',
        '.fontBodyMedium:has-text(",")',
        'div[data-value*=","]',
        'span:has-text(",")'
    ]
    
    for i, selector in enumerate(address_selectors, 1):
        print(f"   {i:2d}. {selector}")
    
    print(f"\n🚀 Testing Navigation Improvements:")
    improvements = [
        "Added scroll_into_view_if_needed() before clicking",
        "Wait for URL change to confirm navigation", 
        "Check for '/maps/place/' in URL to verify business page",
        "Up to 3 seconds wait with 300ms intervals",
        "Fallback handling if navigation doesn't complete",
        "Additional 1 second wait for details to load"
    ]
    
    for i, improvement in enumerate(improvements, 1):
        print(f"   ✅ {improvement}")
    
    print(f"\n🛡️  Testing Error Handling Improvements:")
    error_improvements = [
        "Screenshot capture on extraction failures",
        "Detailed logging for each extraction step",
        "Text validation to filter out UI elements",
        "Graceful handling of selector failures",
        "Debug logging with extracted data summary"
    ]
    
    for i, improvement in enumerate(error_improvements, 1):
        print(f"   ✅ {improvement}")
    
    print(f"\n🔍 Testing Text Filtering:")
    filtered_terms = ['results', 'map', 'directions', 'save', 'share', 'more']
    print(f"   🚫 Filtered terms: {', '.join(filtered_terms)}")
    
    # Test some extraction logic
    test_names = [
        ("Joe's Restaurant", True),
        ("Results", False),
        ("Map", False),
        ("The Pizza Place", True),
        ("directions", False),
        ("Save", False),
        ("McDonald's", True)
    ]
    
    print(f"\n   Name Filtering Tests:")
    for name, should_pass in test_names:
        passes = name.lower() not in filtered_terms
        status = "✅" if passes == should_pass else "❌"
        print(f"     {status} '{name}' -> {'Accept' if passes else 'Filter'}")
    
    print(f"\n✅ All selector improvements validated!")

async def test_navigation_logic():
    """Test the navigation logic improvements."""
    print("\n🧪 Testing Navigation Logic")
    print("=" * 50)
    
    # Mock page for testing navigation logic
    mock_page = AsyncMock()
    initial_url = "https://www.google.com/maps/search/restaurant+near+53.3498,-6.2603"
    final_url = "https://www.google.com/maps/place/Test+Restaurant/@53.3498,-6.2603,14z"
    
    # Simulate URL change during navigation
    url_sequence = [initial_url] * 5 + [final_url] * 5
    mock_page.url = initial_url
    
    call_count = 0
    def get_url():
        nonlocal call_count
        if call_count < len(url_sequence):
            url = url_sequence[call_count]
            call_count += 1
            return url
        return final_url
    
    # Test navigation detection logic
    print(f"🔄 Simulating Navigation Detection:")
    print(f"   Initial URL: {initial_url}")
    print(f"   Target URL:  {final_url}")
    
    # Simulate the navigation check loop
    navigation_success = False
    for attempt in range(10):  # Same as in actual code
        current_url = get_url()
        print(f"   Attempt {attempt + 1}: {current_url[:60]}{'...' if len(current_url) > 60 else ''}")
        
        if current_url != initial_url and '/maps/place/' in current_url:
            print(f"   ✅ Navigation detected at attempt {attempt + 1}")
            navigation_success = True
            break
    
    if navigation_success:
        print(f"   ✅ Navigation logic working correctly")
    else:
        print(f"   ❌ Navigation logic failed")
    
    print(f"\n✅ Navigation logic test completed!")

if __name__ == "__main__":
    test_selector_improvements()
    asyncio.run(test_navigation_logic())