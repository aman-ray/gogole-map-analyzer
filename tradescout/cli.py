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
from .logging_config import setup_logging, info, debug, warning, error


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
@click.option('--log-level', default='INFO', help='Logging level (DEBUG, INFO, WARNING, ERROR)')
@click.option('--log-dir', default='logs', help='Directory for log files')
def main(center, radius_km, categories, max_results, max_runtime_min, 
         concurrency, headless, output, keep_trace, tile_size_km, retry, jitter_ms,
         log_level, log_dir):
    """Google Maps Tradesmen Finder - Find local tradespeople with minimal reviews."""
    
    # Setup logging first
    setup_logging(log_level, log_dir)
    
    print("🔍 Tradescout - Google Maps Tradesmen Finder")
    print("=" * 50)
    info("Starting Tradescout application", print_msg=False)
    
    # Parse center location
    try:
        center_lat, center_lng = parse_center_input(center)
        print(f"📍 Search center: {center_lat:.4f}, {center_lng:.4f}")
        info(f"Search center parsed: {center_lat:.4f}, {center_lng:.4f}", print_msg=False)
    except ValueError as e:
        error_msg = f"Failed to parse center location '{center}': {e}"
        error(error_msg, print_msg=False)
        click.echo(f"Error: {e}", err=True)
        return
    
    # Parse categories
    if categories:
        category_list = [cat.strip() for cat in categories.split(',')]
        info(f"Using custom categories: {category_list}", print_msg=False)
    else:
        category_list = None
        info("Using default categories", print_msg=False)
    
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
    
    info(f"Configuration created - radius: {radius_km}km, max_results: {max_results}, concurrency: {concurrency}", print_msg=False)
    
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
    info("Starting search process", print_msg=False)
    
    # Initialize caches
    cache_dir = Path('.cache')
    dedupe_cache = DedupeCache(cache_dir)
    results_cache = ResultsCache(cache_dir)
    
    cached_count = dedupe_cache.size()
    print(f"💾 Cache initialized with {cached_count} seen businesses")
    info(f"Cache initialized with {cached_count} seen businesses", print_msg=False)
    
    # Generate tiles
    print("🗺️  Generating search tiles...")
    info("Generating search tiles", print_msg=False)
    tiles = generate_tiles(
        config.center_lat, config.center_lng, 
        config.radius_km, config.tile_size_km
    )
    tiles = optimize_tile_coverage(
        tiles, config.center_lat, config.center_lng, config.radius_km
    )
    
    print(f"📐 Generated {len(tiles)} tiles")
    info(f"Generated {len(tiles)} tiles for search area", print_msg=False)
    
    # Create search tasks
    tasks = []
    for tile in tiles:
        for category in config.categories:
            task = search_tile_category_with_retry(
                config, tile, category, dedupe_cache, results_cache
            )
            tasks.append(task)
    
    print(f"🚀 Starting {len(tasks)} search tasks with concurrency={config.concurrency}")
    info(f"Created {len(tasks)} search tasks ({len(tiles)} tiles × {len(config.categories)} categories)", print_msg=False)
    
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
            
            progress_msg = f"📊 Progress: {completed}/{total} tasks completed, {results_cache.size()} businesses found"
            print(progress_msg)
            debug(f"Batch results: {results}", print_msg=False)
            info(f"Progress: {completed}/{total} tasks, {results_cache.size()} businesses found", print_msg=False)
            
            # Check limits
            if results_cache.size() >= config.max_results:
                print("🎯 Maximum results reached!")
                info("Maximum results limit reached", print_msg=False)
                break
            
            elapsed = time.time() - start_time
            if elapsed >= config.max_runtime_min * 60:
                print("⏰ Maximum runtime reached!")
                warning(f"Maximum runtime reached after {elapsed:.1f} seconds", print_msg=False)
                break
    
    except KeyboardInterrupt:
        print("\n⚠️  Search interrupted by user")
        warning("Search interrupted by user", print_msg=False)
    
    # Get final results
    businesses = results_cache.get_results()
    
    # Print summary
    elapsed = time.time() - start_time
    print(f"\n⏱️  Search completed in {elapsed:.1f} seconds")
    info(f"Search completed in {elapsed:.1f} seconds with {len(businesses)} businesses found", print_msg=False)
    print_summary(businesses)
    
    # Export results
    if businesses:
        print("💾 Exporting results...")
        info(f"Starting export of {len(businesses)} businesses", print_msg=False)
        exporter = DataExporter(config.output_prefix)
        exporter.export_all(businesses)
        info("Export completed successfully", print_msg=False)
    else:
        print("❌ No businesses found matching criteria")
        warning("No businesses found matching criteria - possible issues with scraping", print_msg=False)


async def search_tile_category_with_retry(config: SearchConfig, tile, category, 
                                        dedupe_cache, results_cache):
    """Search tile/category with retry logic."""
    for attempt in range(config.retry):
        try:
            debug(f"Searching {category} in tile {tile.center_lat:.4f},{tile.center_lng:.4f} (attempt {attempt + 1})", print_msg=False)
            async with GoogleMapsScraper(config) as scraper:
                return await scraper.search_tile_category(
                    tile, category, dedupe_cache, results_cache
                )
        except Exception as e:
            error_msg = f"Failed to search {category} in tile (attempt {attempt + 1}/{config.retry}): {e}"
            if attempt == config.retry - 1:
                print(f"❌ Failed to search {category} in tile after {config.retry} attempts: {e}")
                error(error_msg, print_msg=False)
                return 0
            
            delay = min(2 ** attempt, 10)  # Exponential backoff, max 10s
            warning_msg = f"Retrying {category} search in {delay}s (attempt {attempt + 1}/{config.retry}): {e}"
            print(f"⚠️  Retrying {category} search in {delay}s (attempt {attempt + 1}/{config.retry})")
            warning(warning_msg, print_msg=False)
            await asyncio.sleep(delay)
    
    return 0


if __name__ == '__main__':
    main()