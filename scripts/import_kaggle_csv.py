#!/usr/bin/env python3
"""
Import Kaggle API CSV Dataset to ChromaDB

This script reads the CSV file from the Kaggle "Ultimate API Dataset" and
converts each row into a searchable document in ChromaDB.

Usage:
    python scripts/import_kaggle_csv.py [--limit N] [--batch-size N]
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import requests

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))


class KaggleCSVImporter:
    """Import Kaggle API CSV dataset into the API Assistant."""

    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.csv_path = Path("data/kaggle_import/api_data.csv")

    def analyze_csv(self) -> Dict[str, Any]:
        """Analyze the CSV structure."""
        print(f"🔍 Analyzing CSV file: {self.csv_path}")

        if not self.csv_path.exists():
            print(f"❌ CSV file not found: {self.csv_path}")
            print("   Please run the Kaggle download first.")
            sys.exit(1)

        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            columns = reader.fieldnames

            # Read first few rows to understand structure
            sample_rows = []
            for i, row in enumerate(reader):
                sample_rows.append(row)
                if i >= 2:  # Get 3 sample rows
                    break

        print(f"   Columns found: {', '.join(columns)}")
        print(f"   Sample row fields: {list(sample_rows[0].keys())[:5]}...")

        # Count total rows
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            total_rows = sum(1 for _ in f) - 1  # Subtract header

        print(f"   Total API records: {total_rows}")

        return {
            'columns': columns,
            'sample_rows': sample_rows,
            'total_rows': total_rows
        }

    def convert_csv_row_to_document(self, row: Dict[str, str]) -> Dict[str, Any]:
        """
        Convert a CSV row to a document format suitable for upload.

        Adapts based on the actual CSV structure.
        Common columns might include: API Name, Description, Category, URL, etc.
        """
        # Build metadata from CSV columns
        metadata = {}
        content_parts = []

        # Common column mappings (adjust based on actual CSV structure)
        column_mappings = {
            'api_name': ['API Name', 'Name', 'api_name', 'title', 'Title'],
            'description': ['Description', 'description', 'desc', 'summary', 'Summary'],
            'category': ['Category', 'category', 'type', 'Type'],
            'url': ['URL', 'url', 'endpoint', 'Endpoint', 'base_url'],
            'method': ['Method', 'method', 'HTTP Method'],
            'authentication': ['Authentication', 'Auth', 'auth_type'],
        }

        # Extract data based on column mappings
        for field, possible_columns in column_mappings.items():
            for col in possible_columns:
                if col in row and row[col]:
                    metadata[field] = row[col]
                    break

        # Build content from all available fields
        for key, value in row.items():
            if value and value.strip():
                content_parts.append(f"{key}: {value}")

        # Create searchable content
        content = "\n".join(content_parts)

        # Set source metadata
        metadata['source'] = 'kaggle_csv'
        metadata['source_file'] = 'api_data.csv'

        return {
            'content': content,
            'metadata': metadata
        }

    def create_temp_json(self, documents: List[Dict[str, Any]], batch_num: int) -> Path:
        """Create a temporary JSON file for upload."""
        temp_dir = Path("data/temp_upload")
        temp_dir.mkdir(parents=True, exist_ok=True)

        temp_file = temp_dir / f"kaggle_batch_{batch_num}.json"

        # Create a simple JSON structure
        data = {
            "source": "kaggle_api_dataset",
            "documents": documents
        }

        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        return temp_file

    def upload_batch(self, documents: List[Dict[str, Any]], batch_num: int) -> Dict[str, Any]:
        """Upload a batch of documents."""
        try:
            # Create temporary JSON file
            temp_file = self.create_temp_json(documents, batch_num)

            # Upload via API
            with open(temp_file, 'rb') as f:
                files = {'files': (temp_file.name, f, 'application/json')}
                data = {'document_mode': 'general_document'}

                response = requests.post(
                    f"{self.api_url}/documents/upload",
                    files=files,
                    data=data,
                    timeout=60
                )

                if response.status_code in [200, 201]:
                    result = response.json()
                    # Clean up temp file
                    temp_file.unlink()
                    return {
                        'success': True,
                        'batch': batch_num,
                        'new_documents': result.get('total_new_documents', 0),
                        'skipped': result.get('total_skipped_documents', 0)
                    }
                else:
                    return {
                        'success': False,
                        'batch': batch_num,
                        'error': f"HTTP {response.status_code}: {response.text[:200]}"
                    }

        except Exception as e:
            return {
                'success': False,
                'batch': batch_num,
                'error': str(e)
            }

    def import_csv(self, limit: int = None, batch_size: int = 100):
        """Import the CSV data into ChromaDB."""

        # Analyze CSV structure
        info = self.analyze_csv()

        print(f"\n📊 CSV Structure:")
        print(f"   Columns: {len(info['columns'])}")
        print(f"   Total records: {info['total_rows']}")

        if limit:
            total_to_import = min(limit, info['total_rows'])
            print(f"   Limiting to: {total_to_import} records")
        else:
            total_to_import = info['total_rows']

        # Read and process CSV
        print(f"\n📤 Starting import...")
        print(f"   Batch size: {batch_size} rows per upload")
        print(f"   API URL: {self.api_url}\n")

        results = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'total_documents': 0,
            'total_skipped': 0,
            'errors': []
        }

        batch = []
        batch_num = 1
        row_count = 0

        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                row_count += 1

                if limit and row_count > limit:
                    break

                # Convert row to document
                doc = self.convert_csv_row_to_document(row)
                batch.append(doc)

                # Upload when batch is full
                if len(batch) >= batch_size:
                    print(f"[Batch {batch_num}] Processing rows {row_count - len(batch) + 1} - {row_count}...")

                    result = self.upload_batch(batch, batch_num)

                    if result['success']:
                        results['success'] += 1
                        results['total_documents'] += result.get('new_documents', 0)
                        results['total_skipped'] += result.get('skipped', 0)
                        print(f"   ✅ Success! Added {result.get('new_documents', 0)} documents")
                    else:
                        results['failed'] += 1
                        results['errors'].append(result)
                        print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")

                    batch = []
                    batch_num += 1
                    results['total'] += 1

        # Upload remaining batch
        if batch:
            print(f"[Batch {batch_num}] Processing final {len(batch)} rows...")
            result = self.upload_batch(batch, batch_num)

            if result['success']:
                results['success'] += 1
                results['total_documents'] += result.get('new_documents', 0)
                results['total_skipped'] += result.get('skipped', 0)
                print(f"   ✅ Success! Added {result.get('new_documents', 0)} documents")
            else:
                results['failed'] += 1
                results['errors'].append(result)
                print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")

            results['total'] += 1

        # Summary
        print("\n" + "="*60)
        print("📊 IMPORT SUMMARY")
        print("="*60)
        print(f"CSV rows processed:       {row_count}")
        print(f"Batches uploaded:         {results['total']}")
        print(f"Successful batches:       {results['success']}")
        print(f"Failed batches:           {results['failed']}")
        print(f"New documents added:      {results['total_documents']}")
        print(f"Documents skipped:        {results['total_skipped']}")

        if results['errors']:
            print(f"\n❌ Errors ({len(results['errors'])}):")
            for error in results['errors'][:5]:
                print(f"   - Batch {error.get('batch', '?')}: {error.get('error', 'Unknown')[:100]}")
            if len(results['errors']) > 5:
                print(f"   ... and {len(results['errors']) - 5} more")

        print("\n✅ Import complete!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Import Kaggle API CSV to ChromaDB")
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of CSV rows to import (for testing)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Number of rows per batch upload (default: 100)'
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
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to backend at {args.api_url}")
        print("   Make sure the backend is running: python -m uvicorn src.api.app:app --reload")
        sys.exit(1)

    # Run import
    importer = KaggleCSVImporter(api_url=args.api_url)
    importer.import_csv(limit=args.limit, batch_size=args.batch_size)


if __name__ == "__main__":
    main()
