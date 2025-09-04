"""Export functionality for multiple output formats."""

import json
import sqlite3
from pathlib import Path
from typing import List
import pandas as pd
from .models import Business
from .logging_config import get_logger, debug, info, warning, error


class DataExporter:
    """Handles exporting data to multiple formats."""
    
    def __init__(self, output_prefix: str):
        self.output_prefix = output_prefix
        self.output_dir = Path(output_prefix).parent
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger('exporter')
    
    def export_all(self, businesses: List[Business]):
        """Export to all supported formats."""
        if not businesses:
            print("No businesses to export.")
            warning("Export attempted with empty business list", print_msg=False)
            return
        
        print(f"Exporting {len(businesses)} businesses...")
        info(f"Starting export of {len(businesses)} businesses to {self.output_prefix}", print_msg=False)
        
        self.export_csv(businesses)
        self.export_parquet(businesses)
        self.export_jsonl(businesses)
        self.export_sqlite(businesses)
        
        print("Export completed.")
        info("All exports completed successfully", print_msg=False)
    
    def export_csv(self, businesses: List[Business]):
        """Export to CSV format."""
        try:
            df = self._to_dataframe(businesses)
            csv_path = f"{self.output_prefix}.csv"
            df.to_csv(csv_path, index=False, encoding='utf-8')
            print(f"CSV exported to: {csv_path}")
            debug(f"CSV export successful: {csv_path} ({len(businesses)} records)", print_msg=False)
        except Exception as e:
            error_msg = f"Error exporting CSV: {e}"
            print(error_msg)
            error(error_msg, print_msg=False)
    
    def export_parquet(self, businesses: List[Business]):
        """Export to Parquet format."""
        try:
            df = self._to_dataframe(businesses)
            parquet_path = f"{self.output_prefix}.parquet"
            df.to_parquet(parquet_path, index=False)
            print(f"Parquet exported to: {parquet_path}")
            debug(f"Parquet export successful: {parquet_path} ({len(businesses)} records)", print_msg=False)
        except Exception as e:
            error_msg = f"Error exporting Parquet: {e}"
            print(error_msg)
            error(error_msg, print_msg=False)
    
    def export_jsonl(self, businesses: List[Business]):
        """Export to JSONL format."""
        try:
            jsonl_path = f"{self.output_prefix}.jsonl"
            with open(jsonl_path, 'w', encoding='utf-8') as f:
                for business in businesses:
                    f.write(json.dumps(business.to_dict()) + '\n')
            print(f"JSONL exported to: {jsonl_path}")
            debug(f"JSONL export successful: {jsonl_path} ({len(businesses)} records)", print_msg=False)
        except Exception as e:
            error_msg = f"Error exporting JSONL: {e}"
            print(error_msg)
            error(error_msg, print_msg=False)
    
    def export_sqlite(self, businesses: List[Business]):
        """Export to SQLite format."""
        try:
            sqlite_path = f"{self.output_prefix}.sqlite"
            
            with sqlite3.connect(sqlite_path) as conn:
                self._create_sqlite_schema(conn)
                
                # Insert businesses
                for business in businesses:
                    self._insert_business(conn, business)
                
                conn.commit()
            
            print(f"SQLite exported to: {sqlite_path}")
            debug(f"SQLite export successful: {sqlite_path} ({len(businesses)} records)", print_msg=False)
        except Exception as e:
            error_msg = f"Error exporting SQLite: {e}"
            print(error_msg)
            error(error_msg, print_msg=False)
    
    def _to_dataframe(self, businesses: List[Business]) -> pd.DataFrame:
        """Convert businesses to pandas DataFrame."""
        data = [business.to_dict() for business in businesses]
        return pd.DataFrame(data)
    
    def _create_sqlite_schema(self, conn: sqlite3.Connection):
        """Create SQLite schema."""
        schema = """
        CREATE TABLE IF NOT EXISTS businesses (
            id INTEGER PRIMARY KEY,
            place_name TEXT NOT NULL,
            category TEXT NOT NULL,
            rating REAL,
            review_count INTEGER NOT NULL,
            website TEXT,
            phone TEXT NOT NULL,
            address_full TEXT,
            locality TEXT,
            postal_code TEXT,
            lat REAL,
            lng REAL,
            maps_profile_url TEXT,
            source TEXT NOT NULL,
            scraped_at TEXT NOT NULL,
            notes TEXT,
            dedupe_key TEXT NOT NULL UNIQUE
        );
        
        CREATE INDEX IF NOT EXISTS idx_businesses_phone ON businesses(phone);
        CREATE INDEX IF NOT EXISTS idx_businesses_review ON businesses(review_count);
        CREATE INDEX IF NOT EXISTS idx_businesses_category ON businesses(category);
        """
        
        conn.executescript(schema)
    
    def _insert_business(self, conn: sqlite3.Connection, business: Business):
        """Insert a business into SQLite database."""
        sql = """
        INSERT OR REPLACE INTO businesses (
            place_name, category, rating, review_count, website, phone,
            address_full, locality, postal_code, lat, lng, maps_profile_url,
            source, scraped_at, notes, dedupe_key
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        values = (
            business.place_name,
            business.category,
            business.rating,
            business.review_count,
            business.website,
            business.phone,
            business.address_full,
            business.locality,
            business.postal_code,
            business.lat,
            business.lng,
            business.maps_profile_url,
            business.source,
            business.scraped_at,
            business.notes,
            business.dedupe_key
        )
        
        conn.execute(sql, values)


def print_summary(businesses: List[Business]):
    """Print a summary of the exported data."""
    if not businesses:
        print("No businesses found.")
        return
    
    print(f"\n=== EXPORT SUMMARY ===")
    print(f"Total businesses: {len(businesses)}")
    
    # Count by category
    category_counts = {}
    for business in businesses:
        category_counts[business.category] = category_counts.get(business.category, 0) + 1
    
    print(f"\nBy category:")
    for category, count in sorted(category_counts.items()):
        print(f"  {category}: {count}")
    
    # Review distribution
    review_counts = {}
    for business in businesses:
        review_counts[business.review_count] = review_counts.get(business.review_count, 0) + 1
    
    print(f"\nBy review count:")
    for review_count, count in sorted(review_counts.items()):
        print(f"  {review_count} reviews: {count}")
    
    # Average rating
    ratings = [b.rating for b in businesses if b.rating is not None]
    if ratings:
        avg_rating = sum(ratings) / len(ratings)
        print(f"\nAverage rating: {avg_rating:.2f}")
    
    print(f"======================\n")