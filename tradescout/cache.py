"""Caching and deduplication system."""

import json
import os
from pathlib import Path
from typing import Set, Optional
from .models import Business


class DedupeCache:
    """Cache for tracking seen businesses to avoid duplicates."""
    
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "seen.jsonl"
        self._seen_keys: Set[str] = set()
        self._load_cache()
    
    def _load_cache(self):
        """Load existing cache from disk."""
        if not self.cache_file.exists():
            return
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        if 'dedupe_key' in data:
                            self._seen_keys.add(data['dedupe_key'])
        except Exception as e:
            print(f"Warning: Could not load cache: {e}")
    
    def is_seen(self, business: Business) -> bool:
        """Check if business has been seen before."""
        return business.dedupe_key in self._seen_keys
    
    def add(self, business: Business):
        """Add business to cache."""
        if business.dedupe_key not in self._seen_keys:
            self._seen_keys.add(business.dedupe_key)
            self._append_to_cache(business)
    
    def _append_to_cache(self, business: Business):
        """Append business to cache file."""
        try:
            with open(self.cache_file, 'a', encoding='utf-8') as f:
                cache_entry = {
                    'dedupe_key': business.dedupe_key,
                    'place_name': business.place_name,
                    'phone': business.phone,
                    'scraped_at': business.scraped_at
                }
                f.write(json.dumps(cache_entry) + '\n')
        except Exception as e:
            print(f"Warning: Could not write to cache: {e}")
    
    def clear(self):
        """Clear the cache."""
        self._seen_keys.clear()
        if self.cache_file.exists():
            self.cache_file.unlink()
    
    def size(self) -> int:
        """Get the number of cached entries."""
        return len(self._seen_keys)


class ResultsCache:
    """Cache for storing search results."""
    
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.results: list[Business] = []
    
    def add_business(self, business: Business, dedupe_cache: DedupeCache) -> bool:
        """Add business to results if not duplicate."""
        if not business.meets_criteria():
            return False
        
        if dedupe_cache.is_seen(business):
            return False
        
        dedupe_cache.add(business)
        self.results.append(business)
        return True
    
    def get_results(self) -> list[Business]:
        """Get all cached results."""
        return self.results.copy()
    
    def size(self) -> int:
        """Get the number of results."""
        return len(self.results)
    
    def clear(self):
        """Clear the results cache."""
        self.results.clear()
    
    def save_checkpoint(self, filename: Optional[str] = None):
        """Save current results to a checkpoint file."""
        if filename is None:
            filename = "checkpoint.jsonl"
        
        checkpoint_file = self.cache_dir / filename
        
        try:
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                for business in self.results:
                    f.write(json.dumps(business.to_dict()) + '\n')
        except Exception as e:
            print(f"Warning: Could not save checkpoint: {e}")
    
    def load_checkpoint(self, filename: Optional[str] = None) -> int:
        """Load results from a checkpoint file."""
        if filename is None:
            filename = "checkpoint.jsonl"
        
        checkpoint_file = self.cache_dir / filename
        
        if not checkpoint_file.exists():
            return 0
        
        loaded_count = 0
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        # Reconstruct Business object
                        business = Business(**data)
                        self.results.append(business)
                        loaded_count += 1
        except Exception as e:
            print(f"Warning: Could not load checkpoint: {e}")
        
        return loaded_count