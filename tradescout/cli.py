"""Command-line interface for tradescout."""

import asyncio
import click
import time
from pathlib import Path
from typing import List
from .models import SearchConfig
from .utils import parse_center_input
from .tiling import generate_tiles, optimize_tile_coverage
from .scraper import GoogleMapsScraper
from .cache import DedupeCache, ResultsCache
from .exporters import DataExporter, print_summary


@click.command()
@click.option('--center', required=True, help='Center location (lat,lng or address)')
@click.option('--radius-km', default=10, help='Search radius in kilometers')
@click.option('--categories', default=None, help='Comma-separated categories')
@click.option('--max-results', default=500, help='Maximum number of results')
@click.option('--max-runtime-min', default=20, help='Maximum runtime in minutes')
@click.option('--concurrency', default=2, help='Number of concurrent browsers')
@click.option('--headless/--no-headless', default=True, help='Run browser in headless mode')
@click.option('--output', default='out', help='Output file prefix')
@click.option('--keep-trace/--no-keep-trace', default=False, help='Keep browser traces')
@click.option('--tile-size-km', default=2.5, help='Tile size in kilometers')
@click.option('--retry', default=3, help='Number of retries')
@click.option('--jitter-ms', default=350, help='Random jitter in milliseconds')
def main(center, radius_km, categories, max_results, max_runtime_min, 
         concurrency, headless, output, keep_trace, tile_size_km, retry, jitter_ms):
    """Google Maps Tradesmen Finder - Find local tradespeople with minimal reviews."""
    
    print("🔍 Tradescout - Google Maps Tradesmen Finder")
    print("=" * 50)
    
    # Parse center location
    try:
        center_lat, center_lng = parse_center_input(center)
        print(f"📍 Search center: {center_lat:.4f}, {center_lng:.4f}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return
    
    # Parse categories
    if categories:
        category_list = [cat.strip() for cat in categories.split(',')]
    else:
        category_list = None
    
    # Create configuration
    config = SearchConfig(
        center_lat=center_lat,
        center_lng=center_lng,
        radius_km=radius_km,
        categories=category_list,
        max_results=max_results,
        max_runtime_min=max_runtime_min,
        concurrency=concurrency,
        headless=headless,
        output_prefix=output,
        keep_trace=keep_trace,
        tile_size_km=tile_size_km,
        retry=retry,
        jitter_ms=jitter_ms
    )
    
    print(f"🎯 Search radius: {radius_km} km")
    print(f"📂 Categories: {', '.join(config.categories)}")
    print(f"🎚️  Max results: {max_results}")
    print(f"⏱️  Max runtime: {max_runtime_min} minutes")
    print(f"🌐 Headless mode: {headless}")
    print()
    
    # Run the search
    asyncio.run(run_search(config))


async def run_search(config: SearchConfig):
    """Run the search process."""
    start_time = time.time()
    
    # Initialize caches
    cache_dir = Path('.cache')
    dedupe_cache = DedupeCache(cache_dir)
    results_cache = ResultsCache(cache_dir)
    
    print(f"💾 Cache initialized with {dedupe_cache.size()} seen businesses")
    
    # Generate tiles
    print("🗺️  Generating search tiles...")
    tiles = generate_tiles(
        config.center_lat, config.center_lng, 
        config.radius_km, config.tile_size_km
    )
    tiles = optimize_tile_coverage(
        tiles, config.center_lat, config.center_lng, config.radius_km
    )
    
    print(f"📐 Generated {len(tiles)} tiles")
    
    # Create search tasks
    tasks = []
    for tile in tiles:
        for category in config.categories:
            task = search_tile_category_with_retry(
                config, tile, category, dedupe_cache, results_cache
            )
            tasks.append(task)
    
    print(f"🚀 Starting {len(tasks)} search tasks with concurrency={config.concurrency}")
    
    # Run searches with limited concurrency
    semaphore = asyncio.Semaphore(config.concurrency)
    
    async def limited_task(task):
        async with semaphore:
            return await task
    
    # Execute tasks
    try:
        completed = 0
        total = len(tasks)
        
        for i in range(0, total, config.concurrency):
            batch = tasks[i:i + config.concurrency]
            batch_tasks = [limited_task(task) for task in batch]
            
            results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            completed += len(batch)
            found_count = sum(r for r in results if isinstance(r, int))
            
            print(f"📊 Progress: {completed}/{total} tasks completed, "
                  f"{results_cache.size()} businesses found")
            
            # Check limits
            if results_cache.size() >= config.max_results:
                print("🎯 Maximum results reached!")
                break
            
            elapsed = time.time() - start_time
            if elapsed >= config.max_runtime_min * 60:
                print("⏰ Maximum runtime reached!")
                break
    
    except KeyboardInterrupt:
        print("\n⚠️  Search interrupted by user")
    
    # Get final results
    businesses = results_cache.get_results()
    
    # Print summary
    elapsed = time.time() - start_time
    print(f"\n⏱️  Search completed in {elapsed:.1f} seconds")
    print_summary(businesses)
    
    # Export results
    if businesses:
        print("💾 Exporting results...")
        exporter = DataExporter(config.output_prefix)
        exporter.export_all(businesses)
    else:
        print("❌ No businesses found matching criteria")


async def search_tile_category_with_retry(config: SearchConfig, tile, category, 
                                        dedupe_cache, results_cache):
    """Search tile/category with retry logic."""
    for attempt in range(config.retry):
        try:
            async with GoogleMapsScraper(config) as scraper:
                return await scraper.search_tile_category(
                    tile, category, dedupe_cache, results_cache
                )
        except Exception as e:
            if attempt == config.retry - 1:
                print(f"❌ Failed to search {category} in tile after {config.retry} attempts: {e}")
                return 0
            
            delay = min(2 ** attempt, 10)  # Exponential backoff, max 10s
            print(f"⚠️  Retrying {category} search in {delay}s (attempt {attempt + 1}/{config.retry})")
            await asyncio.sleep(delay)
    
    return 0


if __name__ == '__main__':
    main()