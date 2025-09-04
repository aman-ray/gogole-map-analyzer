#!/usr/bin/env python3
"""Test script to verify max-review-count functionality works."""

from tradescout.models import Business, SearchConfig
from tradescout.cache import DedupeCache, ResultsCache
import tempfile
from pathlib import Path

def test_review_count_filtering():
    """Test that the max review count filtering works correctly."""
    print("🧪 Testing max review count filtering...")
    
    # Create test businesses with different review counts
    businesses = [
        Business(
            place_name="No Review Business",
            category="plumber",
            rating=None,
            review_count=0,
            website=None,
            phone="01234567890",
            address_full="123 Test St",
            locality="Dublin",
            postal_code="D01",
            lat=53.3498,
            lng=-6.2603,
            maps_profile_url="https://maps.google.com/test1"
        ),
        Business(
            place_name="One Review Business", 
            category="plumber",
            rating=5.0,
            review_count=1,
            website=None,
            phone="01234567891",
            address_full="124 Test St",
            locality="Dublin",
            postal_code="D01",
            lat=53.3498,
            lng=-6.2603,
            maps_profile_url="https://maps.google.com/test2"
        ),
        Business(
            place_name="Five Review Business",
            category="plumber", 
            rating=4.2,
            review_count=5,
            website=None,
            phone="01234567892",
            address_full="125 Test St",
            locality="Dublin",
            postal_code="D01",
            lat=53.3498,
            lng=-6.2603,
            maps_profile_url="https://maps.google.com/test3"
        ),
        Business(
            place_name="Ten Review Business",
            category="plumber",
            rating=4.5,
            review_count=10,
            website=None,
            phone="01234567893",
            address_full="126 Test St",
            locality="Dublin",
            postal_code="D01",
            lat=53.3498,
            lng=-6.2603,
            maps_profile_url="https://maps.google.com/test4"
        ),
        Business(
            place_name="Too Many Reviews Business",
            category="plumber",
            rating=4.8,
            review_count=15,
            website=None,
            phone="01234567894",
            address_full="127 Test St",
            locality="Dublin",
            postal_code="D01",
            lat=53.3498,
            lng=-6.2603,
            maps_profile_url="https://maps.google.com/test5"
        )
    ]
    
    # Test with default max_review_count = 1
    print("\n📊 Testing with max_review_count = 1:")
    config_1 = SearchConfig(
        center_lat=53.3498,
        center_lng=-6.2603,
        max_review_count=1
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        dedupe_cache = DedupeCache(tmpdir)
        results_cache = ResultsCache(tmpdir, config_1)
        
        for business in businesses:
            added = results_cache.add_business(business, dedupe_cache)
            max_reviews = config_1.max_review_count
            meets = business.meets_criteria(max_reviews)
            print(f"  {business.place_name} ({business.review_count} reviews): meets_criteria({max_reviews}) = {meets}, added = {added}")
        
        print(f"  Total businesses added: {results_cache.size()}")
    
    # Test with max_review_count = 5
    print("\n📊 Testing with max_review_count = 5:")
    config_5 = SearchConfig(
        center_lat=53.3498,
        center_lng=-6.2603,
        max_review_count=5
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        dedupe_cache = DedupeCache(tmpdir)
        results_cache = ResultsCache(tmpdir, config_5)
        
        for business in businesses:
            added = results_cache.add_business(business, dedupe_cache)
            max_reviews = config_5.max_review_count
            meets = business.meets_criteria(max_reviews)
            print(f"  {business.place_name} ({business.review_count} reviews): meets_criteria({max_reviews}) = {meets}, added = {added}")
        
        print(f"  Total businesses added: {results_cache.size()}")
    
    # Test with max_review_count = 10
    print("\n📊 Testing with max_review_count = 10:")
    config_10 = SearchConfig(
        center_lat=53.3498,
        center_lng=-6.2603,
        max_review_count=10
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        dedupe_cache = DedupeCache(tmpdir)
        results_cache = ResultsCache(tmpdir, config_10)
        
        for business in businesses:
            added = results_cache.add_business(business, dedupe_cache)
            max_reviews = config_10.max_review_count
            meets = business.meets_criteria(max_reviews)
            print(f"  {business.place_name} ({business.review_count} reviews): meets_criteria({max_reviews}) = {meets}, added = {added}")
        
        print(f"  Total businesses added: {results_cache.size()}")
    
    print("\n✅ Max review count filtering test completed!")

if __name__ == "__main__":
    test_review_count_filtering()
