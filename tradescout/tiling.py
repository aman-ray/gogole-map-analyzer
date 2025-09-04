"""Geographic tiling system for search coverage."""

import math
from typing import List
from .models import Tile
from .utils import haversine_distance


def generate_tiles(center_lat: float, center_lng: float, radius_km: float, tile_size_km: float) -> List[Tile]:
    """Generate a grid of tiles covering the specified radius."""
    tiles = []
    
    # Calculate how many tiles we need in each direction
    # Add some overlap to ensure complete coverage
    tiles_per_radius = math.ceil(radius_km / tile_size_km) + 1
    
    # Convert tile size to approximate degrees
    lat_step = tile_size_km / 111.0  # 1 degree ≈ 111 km
    lng_step = tile_size_km / (111.0 * math.cos(math.radians(center_lat)))
    
    # Generate grid
    for lat_offset in range(-tiles_per_radius, tiles_per_radius + 1):
        for lng_offset in range(-tiles_per_radius, tiles_per_radius + 1):
            tile_lat = center_lat + (lat_offset * lat_step)
            tile_lng = center_lng + (lng_offset * lng_step)
            
            # Check if tile center is within the search radius
            distance = haversine_distance(center_lat, center_lng, tile_lat, tile_lng)
            
            # Include tiles that are within radius or overlap with the search area
            if distance <= radius_km + (tile_size_km / 2):
                tile = Tile(
                    center_lat=tile_lat,
                    center_lng=tile_lng,
                    size_km=tile_size_km
                )
                tiles.append(tile)
    
    return tiles


def optimize_tile_coverage(tiles: List[Tile], center_lat: float, center_lng: float, radius_km: float) -> List[Tile]:
    """Optimize tile coverage by removing unnecessary tiles and sorting by distance."""
    # Filter tiles that contribute to coverage
    valid_tiles = []
    
    for tile in tiles:
        # Check if any corner of the tile is within the search radius
        corners = get_tile_corners(tile)
        
        for corner_lat, corner_lng in corners:
            distance = haversine_distance(center_lat, center_lng, corner_lat, corner_lng)
            if distance <= radius_km:
                valid_tiles.append(tile)
                break
    
    # Sort by distance from center for efficient searching
    valid_tiles.sort(key=lambda t: haversine_distance(center_lat, center_lng, t.center_lat, t.center_lng))
    
    return valid_tiles


def get_tile_corners(tile: Tile) -> List[tuple]:
    """Get the four corners of a tile."""
    min_lat, max_lat, min_lng, max_lng = tile.bounds
    
    return [
        (min_lat, min_lng),  # Bottom-left
        (min_lat, max_lng),  # Bottom-right
        (max_lat, min_lng),  # Top-left
        (max_lat, max_lng),  # Top-right
    ]


def point_in_radius(lat: float, lng: float, center_lat: float, center_lng: float, radius_km: float) -> bool:
    """Check if a point is within the specified radius."""
    distance = haversine_distance(center_lat, center_lng, lat, lng)
    return distance <= radius_km


def estimate_search_area(radius_km: float) -> float:
    """Estimate the search area in square kilometers."""
    return math.pi * (radius_km ** 2)


def estimate_tile_count(radius_km: float, tile_size_km: float) -> int:
    """Estimate the number of tiles needed for coverage."""
    area = estimate_search_area(radius_km)
    tile_area = tile_size_km ** 2
    
    # Add some buffer for overlap and irregular shapes
    return math.ceil(area / tile_area * 1.5)