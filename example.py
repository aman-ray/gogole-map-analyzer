#!/usr/bin/env python3
"""
Example script showing how to use tradescout programmatically.
This creates sample data without requiring Playwright for demonstration.
"""

from tradescout.models import Business, SearchConfig
from tradescout.cache import DedupeCache, ResultsCache
from tradescout.exporters import DataExporter, print_summary
from tradescout.tiling import generate_tiles
import tempfile
import os


def create_sample_data():
    """Create some sample businesses for demonstration."""
    sample_businesses = [
        Business(
            place_name="Mike's Plumbing Services",
            category="plumber",
            rating=None,
            review_count=0,
            website=None,
            phone="+353-1-555-0001",
            address_full="15 Main Street, Lucan, Dublin",
            locality="Dublin",
            postal_code="K78 ABC1",
            lat=53.3574,
            lng=-6.4479,
            maps_profile_url="https://maps.google.com/place1"
        ),
        Business(
            place_name="Dublin Electrical Solutions",
            category="electrician", 
            rating=4.0,
            review_count=1,
            website=None,
            phone="+353-1-555-0002",
            address_full="22 Church Road, Clondalkin, Dublin",
            locality="Dublin",
            postal_code="D22 XY56",
            lat=53.3196,
            lng=-6.3960,
            maps_profile_url="https://maps.google.com/place2"
        ),
        Business(
            place_name="Local Handyman Services",
            category="handyman",
            rating=None,
            review_count=1,
            website=None,
            phone="+353-1-555-0003",
            address_full="8 Oak Drive, Palmerstown, Dublin",
            locality="Dublin", 
            postal_code="D20 EF78",
            lat=53.3531,
            lng=-6.3783,
            maps_profile_url="https://maps.google.com/place3"
        ),
        Business(
            place_name="Quick Roof Repairs",
            category="roofer",
            rating=3.5,
            review_count=0,
            website=None,
            phone="+353-1-555-0004",
            address_full="45 Valley Park, Lucan, Dublin",
            locality="Dublin",
            postal_code="K78 GH90",
            lat=53.3623,
            lng=-6.4512,
            maps_profile_url="https://maps.google.com/place4"
        )
    ]
    
    return sample_businesses


def main():
    """Run the example."""
    print("🔧 Tradescout Example - Sample Data Demo")
    print("=" * 50)
    
    # Create configuration
    config = SearchConfig(
        center_lat=53.3498,    # Dublin center
        center_lng=-6.2603,
        radius_km=10,
        max_results=50
    )
    
    print(f"📍 Search center: {config.center_lat:.4f}, {config.center_lng:.4f}")
    print(f"🎯 Search radius: {config.radius_km} km")
    print(f"📂 Categories: {', '.join(config.categories[:5])}...")
    print()
    
    # Generate tiles
    print("🗺️  Generating search tiles...")
    tiles = generate_tiles(
        config.center_lat, config.center_lng, 
        config.radius_km, config.tile_size_km
    )
    print(f"📐 Generated {len(tiles)} tiles")
    print()
    
    # Create sample data
    print("📊 Creating sample business data...")
    sample_businesses = create_sample_data()
    
    # Filter businesses that meet criteria
    valid_businesses = [b for b in sample_businesses if b.meets_criteria()]
    print(f"✅ Found {len(valid_businesses)} businesses meeting criteria")
    print()
    
    # Print summary
    print_summary(valid_businesses)
    
    # Export to files
    with tempfile.TemporaryDirectory() as tmpdir:
        output_prefix = os.path.join(tmpdir, "lucan_sample")
        print(f"💾 Exporting to {output_prefix}.*")
        
        exporter = DataExporter(output_prefix)
        exporter.export_all(valid_businesses)
        
        print("\n📁 Files created:")
        for ext in ['csv', 'jsonl', 'parquet', 'sqlite']:
            filepath = f"{output_prefix}.{ext}"
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                print(f"  • {filepath} ({size} bytes)")
    
    print("\n🎉 Example completed!")
    print("\nTo run real searches (requires Playwright):")
    print("1. Install browser: playwright install chromium")
    print("2. Run search: tradescout --center 'Dublin, Ireland' --radius-km 5 --output real_search")


if __name__ == "__main__":
    main()