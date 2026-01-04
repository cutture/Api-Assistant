#!/usr/bin/env python3
"""
Import Kaggle API Dataset to ChromaDB

This script downloads and imports the "Ultimate API Dataset" from Kaggle
into the API Assistant's ChromaDB collection.

Dataset: https://www.kaggle.com/datasets/shivd24coder/ultimate-api-dataset-1000-data-sources

Prerequisites:
1. Install kaggle: pip install kaggle
2. Set up Kaggle API credentials: https://www.kaggle.com/docs/api
   - Go to https://www.kaggle.com/settings/account
   - Click "Create New API Token"
   - Place kaggle.json in ~/.kaggle/
3. Ensure backend is running

Usage:
    python scripts/import_kaggle_dataset.py [--limit N] [--batch-size N]
"""

import argparse
import json
import os
import sys
import zipfile
from pathlib import Path
from typing import List, Dict, Any
import requests
import time

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))


class KaggleDatasetImporter:
    """Import Kaggle API dataset into the API Assistant."""

    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.dataset_name = "shivd24coder/ultimate-api-dataset-1000-data-sources"
        self.download_dir = Path("data/kaggle_import")
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def download_dataset(self) -> Path:
        """Download the Kaggle dataset."""
        print(f"📥 Downloading Kaggle dataset: {self.dataset_name}")

        try:
            import kaggle

            # Download to our temp directory
            kaggle.api.dataset_download_files(
                self.dataset_name,
                path=str(self.download_dir),
                unzip=True
            )

            print(f"✅ Dataset downloaded to: {self.download_dir}")
            return self.download_dir

        except ImportError:
            print("❌ Error: 'kaggle' package not installed.")
            print("   Install it with: pip install kaggle")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error downloading dataset: {e}")
            print("\nMake sure you have:")
            print("1. Kaggle API token in ~/.kaggle/kaggle.json")
            print("2. Run: pip install kaggle")
            sys.exit(1)

    def analyze_dataset(self, dataset_dir: Path) -> List[Path]:
        """Analyze the downloaded dataset and find API spec files."""
        print(f"\n🔍 Analyzing dataset structure...")

        # Find all JSON files (likely API specs)
        json_files = list(dataset_dir.rglob("*.json"))
        yaml_files = list(dataset_dir.rglob("*.yaml")) + list(dataset_dir.rglob("*.yml"))

        all_files = json_files + yaml_files

        print(f"   Found {len(json_files)} JSON files")
        print(f"   Found {len(yaml_files)} YAML files")
        print(f"   Total: {len(all_files)} potential API spec files")

        return all_files

    def validate_api_spec(self, file_path: Path) -> bool:
        """Check if a file is a valid API specification."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

                # Try to parse as JSON
                if file_path.suffix == '.json':
                    data = json.loads(content)

                    # Check for OpenAPI/Swagger
                    if 'openapi' in data or 'swagger' in data:
                        return True

                    # Check for Postman collection
                    if 'info' in data and 'item' in data:
                        return True

                    # Check for GraphQL schema
                    if 'data' in data and '__schema' in data.get('data', {}):
                        return True

                # YAML files
                elif file_path.suffix in ['.yaml', '.yml']:
                    # Basic check for API spec keywords
                    if any(keyword in content for keyword in ['openapi:', 'swagger:', 'paths:', 'info:']):
                        return True

                return False

        except Exception as e:
            print(f"   ⚠️  Could not validate {file_path.name}: {e}")
            return False

    def upload_file(self, file_path: Path) -> Dict[str, Any]:
        """Upload a single file to the API Assistant."""
        try:
            with open(file_path, 'rb') as f:
                files = {'files': (file_path.name, f, 'application/json')}
                data = {'document_mode': 'api_spec'}

                response = requests.post(
                    f"{self.api_url}/documents/upload",
                    files=files,
                    data=data,
                    timeout=60
                )

                if response.status_code in [200, 201]:
                    result = response.json()
                    return {
                        'success': True,
                        'file': file_path.name,
                        'new_documents': result.get('total_new_documents', 0),
                        'skipped': result.get('total_skipped_documents', 0)
                    }
                else:
                    return {
                        'success': False,
                        'file': file_path.name,
                        'error': f"HTTP {response.status_code}: {response.text[:200]}"
                    }

        except Exception as e:
            return {
                'success': False,
                'file': file_path.name,
                'error': str(e)
            }

    def import_dataset(self, limit: int = None, batch_size: int = 10):
        """Import the Kaggle dataset into ChromaDB."""

        # Step 1: Download dataset
        dataset_dir = self.download_dataset()

        # Step 2: Analyze and find API specs
        all_files = self.analyze_dataset(dataset_dir)

        if not all_files:
            print("❌ No API specification files found in the dataset!")
            return

        # Step 3: Validate and filter
        print(f"\n✅ Validating API specifications...")
        valid_files = []
        for file_path in all_files:
            if self.validate_api_spec(file_path):
                valid_files.append(file_path)
                if len(valid_files) % 50 == 0:
                    print(f"   Validated {len(valid_files)} files...")

        print(f"   Found {len(valid_files)} valid API specifications")

        if limit:
            valid_files = valid_files[:limit]
            print(f"   Limiting to first {limit} files")

        # Step 4: Upload to API Assistant
        print(f"\n📤 Uploading to API Assistant...")
        print(f"   Batch size: {batch_size}")
        print(f"   API URL: {self.api_url}")

        results = {
            'total': len(valid_files),
            'success': 0,
            'failed': 0,
            'total_documents': 0,
            'total_skipped': 0,
            'errors': []
        }

        for i, file_path in enumerate(valid_files, 1):
            print(f"\n[{i}/{len(valid_files)}] Uploading: {file_path.name}")

            result = self.upload_file(file_path)

            if result['success']:
                results['success'] += 1
                results['total_documents'] += result.get('new_documents', 0)
                results['total_skipped'] += result.get('skipped', 0)
                print(f"   ✅ Success! Added {result.get('new_documents', 0)} documents")
            else:
                results['failed'] += 1
                results['errors'].append(result)
                print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")

            # Rate limiting - small delay between uploads
            if i % batch_size == 0 and i < len(valid_files):
                print(f"\n   ⏸️  Pausing after {batch_size} uploads...")
                time.sleep(2)

        # Step 5: Summary
        print("\n" + "="*60)
        print("📊 IMPORT SUMMARY")
        print("="*60)
        print(f"Total files processed:    {results['total']}")
        print(f"Successfully uploaded:    {results['success']}")
        print(f"Failed:                   {results['failed']}")
        print(f"New documents added:      {results['total_documents']}")
        print(f"Documents skipped:        {results['total_skipped']}")

        if results['errors']:
            print(f"\n❌ Errors ({len(results['errors'])}):")
            for error in results['errors'][:10]:  # Show first 10 errors
                print(f"   - {error['file']}: {error.get('error', 'Unknown')[:100]}")
            if len(results['errors']) > 10:
                print(f"   ... and {len(results['errors']) - 10} more")

        print("\n✅ Import complete!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Import Kaggle API dataset to ChromaDB")
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of files to import (for testing)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Number of files to upload before pausing (default: 10)'
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
    importer = KaggleDatasetImporter(api_url=args.api_url)
    importer.import_dataset(limit=args.limit, batch_size=args.batch_size)


if __name__ == "__main__":
    main()
