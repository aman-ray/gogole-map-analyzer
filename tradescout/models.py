"""Data models for tradescout."""

from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime
import hashlib
import re


@dataclass
class Business:
    """Data model for a business listing."""
    place_name: str
    category: str
    rating: Optional[float]
    review_count: int
    website: Optional[str]
    phone: str
    address_full: Optional[str]
    locality: Optional[str]
    postal_code: Optional[str]
    lat: Optional[float]
    lng: Optional[float]
    maps_profile_url: Optional[str]
    source: str = "maps_ui"
    scraped_at: Optional[str] = None
    notes: Optional[str] = None
    dedupe_key: Optional[str] = None

    def __post_init__(self):
        """Set scraped_at and dedupe_key after initialization."""
        if self.scraped_at is None:
            self.scraped_at = datetime.utcnow().isoformat() + "Z"
        
        if self.dedupe_key is None:
            self.dedupe_key = self._generate_dedupe_key()

    def _generate_dedupe_key(self) -> str:
        """Generate deduplication key."""
        # Normalize place name
        place_norm = re.sub(r'[^\w\s]', '', self.place_name.lower()).strip()
        place_norm = re.sub(r'\s+', ' ', place_norm)
        
        # Normalize phone (remove all non-digits)
        phone_norm = re.sub(r'\D', '', self.phone) if self.phone else ''
        
        # Primary key: place_name + phone
        if place_norm and phone_norm:
            key_string = f"{place_norm}|{phone_norm}"
        else:
            # Fallback: place_name + rounded coordinates
            lat_rounded = round(self.lat, 5) if self.lat else 0
            lng_rounded = round(self.lng, 5) if self.lng else 0
            key_string = f"{place_norm}|{lat_rounded}|{lng_rounded}"
        
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()

    def meets_criteria(self) -> bool:
        """Check if business meets inclusion criteria."""
        # Must have phone
        if not self.phone or not self.phone.strip():
            return False
        
        # Review count <= 1
        if self.review_count > 1:
            return False
        
        # Website must be empty/absent
        if self.website and self.website.strip():
            return False
        
        return True

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SearchConfig:
    """Configuration for search parameters."""
    center_lat: float
    center_lng: float
    radius_km: float = 10
    categories: list = None
    max_results: int = 500
    max_runtime_min: int = 20
    concurrency: int = 2
    headless: bool = True
    output_prefix: str = "out"
    keep_trace: bool = False
    tile_size_km: float = 2.5
    retry: int = 3
    jitter_ms: int = 350

    def __post_init__(self):
        """Set default categories if not provided."""
        if self.categories is None:
            self.categories = [
                "plumber", "electrician", "carpenter", "roofer", "painter",
                "tiler", "locksmith", "plasterer", "handyman", "heating engineer",
                "glazier", "pest control", "landscaper", "gardener", "chimney sweep"
            ]


@dataclass
class Tile:
    """Geographic tile for search grid."""
    center_lat: float
    center_lng: float
    size_km: float
    
    @property
    def bounds(self):
        """Get tile bounds (min_lat, max_lat, min_lng, max_lng)."""
        # Approximate conversion: 1 degree ≈ 111 km
        lat_offset = (self.size_km / 2) / 111
        lng_offset = (self.size_km / 2) / (111 * abs(self.center_lat / 90))
        
        return (
            self.center_lat - lat_offset,  # min_lat
            self.center_lat + lat_offset,  # max_lat
            self.center_lng - lng_offset,  # min_lng
            self.center_lng + lng_offset   # max_lng
        )