#!/usr/bin/env python3
"""
Import Kaggle API CSV Dataset to ChromaDB (Direct Upload)

This script reads the CSV file and uploads data directly to ChromaDB
without creating temporary files (fixes Windows file locking issues).

Usage:
    python scripts/import_kaggle_csv_direct.py [--limit N]
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import requests
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class KaggleCSVDirectImporter:
    """Import Kaggle API CSV dataset directly into ChromaDB."""

    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.csv_path = Path("data/kaggle_import/api_data.csv")

    def read_csv_data(self, limit: int = None) -> List[Dict[str, str]]:
        """Read CSV file and return rows as list of dicts."""
        print(f"📖 Reading CSV file: {self.csv_path}")

        if not self.csv_path.exists():
            print(f"❌ CSV file not found: {self.csv_path}")
            sys.exit(1)

        rows = []
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # Show columns
            columns = reader.fieldnames
            print(f"   Columns: {', '.join(columns)}")

            for i, row in enumerate(reader, 1):
                rows.append(row)
                if limit and i >= limit:
                    break

        print(f"   Loaded {len(rows)} rows")
        return rows

    def upload_documents_direct(self, rows: List[Dict[str, str]]) -> Dict[str, Any]:
        """Upload documents directly to ChromaDB via API."""

        # Convert CSV rows to documents
        documents = []
        for row in rows:
            # Build searchable content from CSV columns
            content_parts = []

            # Map CSV columns (based on your screenshot)
            api_name = row.get('API', '')
            description = row.get('Description', '')
            auth = row.get('Auth', '')
            https = row.get('HTTPS', '')
            cors = row.get('Cors', '')
            link = row.get('Link', '')
            category = row.get('Category', '')

            # Build content
            if api_name:
                content_parts.append(f"API: {api_name}")
            if description:
                content_parts.append(f"Description: {description}")
            if category:
                content_parts.append(f"Category: {category}")
            if link:
                content_parts.append(f"URL: {link}")
            if auth:
                content_parts.append(f"Authentication: {auth}")
            if https:
                content_parts.append(f"HTTPS: {https}")
            if cors:
                content_parts.append(f"CORS: {cors}")

            content = "\n".join(content_parts)

            # Build metadata
            metadata = {
                'api_name': api_name or 'Unknown',
                'description': description,
                'category': category,
                'url': link,
                'auth': auth,
                'https': https,
                'cors': cors,
                'source': 'kaggle_csv',
                'source_file': 'api_data.csv'
            }

            documents.append({
                'id': f"kaggle_api_{len(documents) + 1}",
                'content': content,
                'metadata': metadata
            })

        # Send directly to /documents endpoint
        print(f"\n📤 Uploading {len(documents)} documents to ChromaDB...")

        try:
            response = requests.post(
                f"{self.api_url}/documents",
                json={'documents': documents},
                headers={'Content-Type': 'application/json'},
                timeout=120
            )

            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    'success': True,
                    'new_documents': result.get('new_count', 0),
                    'skipped': result.get('skipped_count', 0),
                    'total': result.get('count', 0)
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text[:500]}"
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def import_csv(self, limit: int = None):
        """Import the CSV data."""

        # Read CSV
        rows = self.read_csv_data(limit)

        if not rows:
            print("❌ No data to import!")
            return

        # Upload directly
        result = self.upload_documents_direct(rows)

        # Show results
        print("\n" + "="*60)
        print("📊 IMPORT SUMMARY")
        print("="*60)
        print(f"CSV rows read:            {len(rows)}")

        if result['success']:
            print(f"✅ Status:                Success")
            print(f"New documents added:      {result.get('new_documents', 0)}")
            print(f"Documents skipped:        {result.get('skipped', 0)}")
        else:
            print(f"❌ Status:                Failed")
            print(f"Error:                    {result.get('error', 'Unknown error')}")

        print("\n✅ Import complete!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Import Kaggle API CSV to ChromaDB (Direct)")
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of CSV rows to import (for testing)'
    )
    parser.add_argument(
        '--api-url',
        default='http://localhost:8000',
        help='API Assistant backend URL (default: http://localhost:8000)'
    )

    args = parser.parse_args()

    # Check if backend is running
    try:
        response = requests.get(f"{args.api_url}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Backend is not responding at {args.api_url}")
            print("   Make sure the backend is running!")
            sys.exit(1)
        print(f"✅ Backend is running at {args.api_url}\n")
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to backend at {args.api_url}")
        print("   Make sure the backend is running: python -m uvicorn src.api.app:app --reload")
        sys.exit(1)

    # Run import
    importer = KaggleCSVDirectImporter(api_url=args.api_url)
    importer.import_csv(limit=args.limit)


if __name__ == "__main__":
    main()
