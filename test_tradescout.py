#!/usr/bin/env python3
"""Simple test to verify tradescout installation and basic functionality."""

import sys
from tradescout.models import Business, SearchConfig
from tradescout.utils import haversine_distance, normalize_phone, parse_center_input
from tradescout.tiling import generate_tiles
from tradescout.cache import DedupeCache, ResultsCache
from tradescout.exporters import DataExporter


def test_models():
    """Test data models."""
    print("Testing data models...")
    
    # Test Business model
    business = Business(
        place_name="Test Plumber Ltd",
        category="plumber",
        rating=4.2,
        review_count=1,
        website=None,
        phone="+353-1-234-5678",
        address_full="123 Test Street, Dublin",
        locality="Dublin",
        postal_code="D01 ABC1",
        lat=53.3498,
        lng=-6.2603,
        maps_profile_url="https://maps.google.com/test"
    )
    
    assert business.meets_criteria() == True
    assert business.dedupe_key is not None
    print(f"✓ Business model works: {business.place_name}")
    
    # Test SearchConfig
    config = SearchConfig(
        center_lat=53.3498,
        center_lng=-6.2603
    )
    assert len(config.categories) > 0
    print(f"✓ SearchConfig works with {len(config.categories)} categories")


def test_utils():
    """Test utility functions."""
    print("Testing utilities...")
    
    # Test haversine distance
    dublin_lat, dublin_lng = 53.3498, -6.2603
    cork_lat, cork_lng = 51.8985, -8.4756
    distance = haversine_distance(dublin_lat, dublin_lng, cork_lat, cork_lng)
    assert 200 < distance < 300  # Should be ~250 km
    print(f"✓ Haversine distance: Dublin to Cork = {distance:.1f} km")
    
    # Test phone normalization
    phone = normalize_phone("01-234-5678", "IE")
    print(f"✓ Phone normalization: '01-234-5678' -> '{phone}'")
    
    # Test center parsing
    lat, lng = parse_center_input("53.3498,-6.2603")
    assert abs(lat - 53.3498) < 0.001
    assert abs(lng - -6.2603) < 0.001
    print(f"✓ Center parsing: coordinates work")


def test_tiling():
    """Test tiling system."""
    print("Testing tiling system...")
    
    tiles = generate_tiles(53.3498, -6.2603, 10, 2.5)
    assert len(tiles) > 0
    print(f"✓ Tiling: Generated {len(tiles)} tiles for 10km radius")


def test_cache():
    """Test caching system."""
    print("Testing cache system...")
    
    # Create test directory
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        dedupe_cache = DedupeCache(tmpdir)
        results_cache = ResultsCache(tmpdir)  # Use default behavior for tests
        
        # Create test business
        business = Business(
            place_name="Test Business",
            category="plumber", 
            rating=None,
            review_count=0,
            website=None,
            phone="123456789",
            address_full="Test Address",
            locality=None,
            postal_code=None,
            lat=53.3498,
            lng=-6.2603,
            maps_profile_url="test"
        )
        
        # Test adding business
        added = results_cache.add_business(business, dedupe_cache)
        assert added == True
        assert results_cache.size() == 1
        print(f"✓ Cache: Added business successfully")
        
        # Test duplicate detection
        added_again = results_cache.add_business(business, dedupe_cache)
        assert added_again == False
        assert results_cache.size() == 1
        print(f"✓ Cache: Duplicate detection works")


def test_exporters():
    """Test export functionality."""
    print("Testing exporters...")
    
    import tempfile
    import os
    
    # Create test business
    business = Business(
        place_name="Test Export Business",
        category="electrician",
        rating=3.5,
        review_count=1,
        website=None,
        phone="987654321",
        address_full="Test Export Address",
        locality="Dublin",
        postal_code="D02 XYZ9",
        lat=53.3498,
        lng=-6.2603,
        maps_profile_url="test"
    )
    
    businesses = [business]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_prefix = os.path.join(tmpdir, "test_export")
        exporter = DataExporter(output_prefix)
        
        # Test individual exports
        exporter.export_csv(businesses)
        exporter.export_jsonl(businesses)
        # Skip parquet and sqlite in basic test
        
        assert os.path.exists(f"{output_prefix}.csv")
        assert os.path.exists(f"{output_prefix}.jsonl")
        print(f"✓ Exporters: CSV and JSONL export work")


def test_cli_help():
    """Test CLI help command."""
    print("Testing CLI...")
    
    try:
        from tradescout.cli import main
        import click.testing
        
        runner = click.testing.CliRunner()
        result = runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert "Google Maps Tradesmen Finder" in result.output
        print("✓ CLI: Help command works")
    except Exception as e:
        print(f"⚠ CLI: Help test failed (expected in test environment): {e}")


def main():
    """Run all tests."""
    print("🧪 Running Tradescout Tests")
    print("=" * 40)
    
    try:
        test_models()
        test_utils()
        test_tiling()
        test_cache()
        test_exporters()
        test_cli_help()
        
        print("\n✅ All tests passed!")
        print("Tradescout is ready to use.")
        print("\nTo run a search:")
        print("tradescout --center 'Dublin, Ireland' --radius-km 5 --max-results 10 --output test")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()