"""Utility functions for tradescout."""

import logging
import re
import math
import time
import random
from typing import Tuple, Optional
import phonenumbers
from geopy.geocoders import Nominatim


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate the Haversine distance between two points in kilometers."""
    # Convert to radians
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth's radius in kilometers
    r = 6371
    
    return c * r


def normalize_phone(phone: str, region: str = "IE") -> Optional[str]:
    """Normalize phone number to E.164 format."""
    if not phone:
        return None
    
    try:
        # Clean up the phone number
        phone = re.sub(r'[^\d+]', '', phone)
        
        # Parse the phone number
        parsed = phonenumbers.parse(phone, region)
        
        # Check if it's valid
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        
        return phone  # Return original if parsing fails
    except Exception:
        # Remove all non-digits as fallback
        return re.sub(r'\D', '', phone) if phone else None


def normalize_website(website: str) -> Optional[str]:
    """Normalize website URL or return None if empty."""
    if not website or not website.strip():
        return None
    
    website = website.strip()
    
    # Remove common prefixes that indicate "no website"
    no_website_indicators = [
        "no website", "n/a", "none", "not available", "-", "—"
    ]
    
    if website.lower() in no_website_indicators:
        return None
    
    # Add protocol if missing
    if not website.startswith(('http://', 'https://')):
        website = 'https://' + website
    
    return website


def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """Geocode an address to lat, lng coordinates."""
    try:
        geolocator = Nominatim(user_agent="tradescout")
        location = geolocator.geocode(address)
        logging.info(f"Geocoding {address}: {location}")
        
        if location:
            return (location.latitude, location.longitude)
        
        return None
    except Exception:
        return None


def parse_center_input(center: str) -> Tuple[float, float]:
    """Parse center input as either 'lat,lng' or address."""
    # Try to parse as lat,lng first
    try:
        parts = center.split(',')
        if len(parts) == 2:
            lat = float(parts[0].strip())
            lng = float(parts[1].strip())
            return (lat, lng)
    except ValueError:
        pass
    
    # Try to geocode as address
    coords = geocode_address(center)
    if coords:
        return coords
    
    raise ValueError(f"Could not parse center location: {center}")


def add_jitter(base_delay: float, jitter_ms: int) -> float:
    """Add random jitter to delay."""
    jitter_seconds = random.uniform(0.05, jitter_ms / 1000.0)
    return base_delay + jitter_seconds


def exponential_backoff(attempt: int, base_delay: float = 0.3) -> float:
    """Calculate exponential backoff delay."""
    return base_delay * (2 ** attempt)


def sleep_with_jitter(delay: float, jitter_ms: int = 350):
    """Sleep with random jitter."""
    actual_delay = add_jitter(delay, jitter_ms)
    time.sleep(actual_delay)


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove common HTML entities
    html_entities = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&#39;': "'",
        '&nbsp;': ' '
    }
    
    for entity, replacement in html_entities.items():
        text = text.replace(entity, replacement)
    
    return text


def extract_rating(rating_text: str) -> Optional[float]:
    """Extract rating from text."""
    if not rating_text:
        return None
    
    # Look for patterns like "4.5", "4,5", "4.5 stars", etc.
    pattern = r'(\d+[.,]\d+|\d+)'
    match = re.search(pattern, rating_text)
    
    if match:
        rating_str = match.group(1).replace(',', '.')
        try:
            rating = float(rating_str)
            # Clamp to valid range
            return max(0.0, min(5.0, rating))
        except ValueError:
            pass
    
    return None


def extract_review_count(review_text: str) -> int:
    """Extract review count from text."""
    if not review_text:
        return 0
    
    # Look for patterns like "5 reviews", "(10)", "123 отзывы", etc.
    pattern = r'(\d+)'
    match = re.search(pattern, review_text)
    
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass
    
    return 0


def calculate_zoom_level(tile_size_km: float) -> int:
    """Calculate appropriate Google Maps zoom level based on tile size.
    
    Google Maps zoom levels:
    - 1: World view
    - 5: Continent view
    - 10: City view
    - 15: Streets view
    - 20: Buildings view
    
    For tile-based searching, we want enough detail to see individual businesses
    but not so zoomed in that we miss coverage.
    """
    # Mapping tile size to zoom level
    # Smaller tiles need higher zoom (more detail)
    if tile_size_km <= 0.5:
        return 16  # Very detailed view for very small tiles
    elif tile_size_km <= 1.0:
        return 15  # Street level detail
    elif tile_size_km <= 2.0:
        return 14  # Neighborhood level
    elif tile_size_km <= 3.0:
        return 13  # District level
    elif tile_size_km <= 5.0:
        return 12  # City area level
    else:
        return 11  # Wide area view for large tiles