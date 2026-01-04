# Importing Kaggle API Dataset

This guide explains how to import the "Ultimate API Dataset (1000+ Data Sources)" from Kaggle into your API Assistant's ChromaDB collection.

**Dataset**: [shivd24coder/ultimate-api-dataset-1000-data-sources](https://www.kaggle.com/datasets/shivd24coder/ultimate-api-dataset-1000-data-sources)

## Why Import This Dataset?

- **Testing**: Large collection of real API specifications for testing search, chat, and diagram features
- **Diversity**: 1000+ different API sources covering various domains
- **Quality**: Real-world OpenAPI/Swagger specifications
- **Scale**: Test performance with a substantial document collection

## Prerequisites

### 1. Kaggle API Setup

First, you need to set up Kaggle API credentials:

1. **Create a Kaggle Account** (if you don't have one):
   - Go to https://www.kaggle.com and sign up

2. **Get Your API Token**:
   - Go to https://www.kaggle.com/settings/account
   - Scroll to "API" section
   - Click "Create New API Token"
   - This downloads `kaggle.json` file

3. **Place the Token**:
   ```bash
   # On Linux/Mac
   mkdir -p ~/.kaggle
   mv ~/Downloads/kaggle.json ~/.kaggle/
   chmod 600 ~/.kaggle/kaggle.json

   # On Windows
   # Place kaggle.json in C:\Users\<YourUsername>\.kaggle\
   ```

4. **Install Kaggle Package**:
   ```bash
   pip install kaggle
   ```

### 2. Backend Running

Make sure your API Assistant backend is running:

```bash
python -m uvicorn src.api.app:app --reload
```

## Usage

### Basic Import (All Files)

Import the entire dataset:

```bash
python scripts/import_kaggle_dataset.py
```

This will:
1. Download the dataset from Kaggle (~50-100MB)
2. Analyze and validate API specifications
3. Upload them to your ChromaDB collection
4. Show progress and summary

### Test Import (Limited Files)

For testing, import only first 10 files:

```bash
python scripts/import_kaggle_dataset.py --limit 10
```

### Custom Batch Size

Control upload speed with batch size:

```bash
python scripts/import_kaggle_dataset.py --batch-size 5
```

Smaller batch size = slower but safer (reduces API load)

### Custom API URL

If your backend is on a different port/host:

```bash
python scripts/import_kaggle_dataset.py --api-url http://localhost:8080
```

### Combined Options

```bash
python scripts/import_kaggle_dataset.py --limit 50 --batch-size 10 --api-url http://localhost:8000
```

## What the Script Does

### Step 1: Download Dataset

Downloads the Kaggle dataset to `data/kaggle_import/`:

```
📥 Downloading Kaggle dataset: shivd24coder/ultimate-api-dataset-1000-data-sources
✅ Dataset downloaded to: data/kaggle_import
```

### Step 2: Analyze Files

Scans for API specification files (JSON, YAML):

```
🔍 Analyzing dataset structure...
   Found 1247 JSON files
   Found 183 YAML files
   Total: 1430 potential API spec files
```

### Step 3: Validate Specifications

Checks each file for valid API spec format:

```
✅ Validating API specifications...
   Validated 50 files...
   Validated 100 files...
   Found 982 valid API specifications
```

Validates for:
- OpenAPI 3.x specifications (`openapi: "3.0.0"`)
- Swagger 2.x specifications (`swagger: "2.0"`)
- Postman collections
- GraphQL schemas

### Step 4: Upload to ChromaDB

Uploads each valid spec via the `/documents/upload` endpoint:

```
📤 Uploading to API Assistant...
   Batch size: 10
   API URL: http://localhost:8000

[1/982] Uploading: stripe-api.json
   ✅ Success! Added 47 documents

[2/982] Uploading: github-api.json
   ✅ Success! Added 124 documents
```

### Step 5: Summary

Shows final statistics:

```
============================================================
📊 IMPORT SUMMARY
============================================================
Total files processed:    982
Successfully uploaded:    975
Failed:                   7
New documents added:      45,382
Documents skipped:        1,245
```

## Expected Results

After import:

- **Document Count**: 40,000-50,000+ chunks (depending on API complexity)
- **Collection Size**: ~500MB-1GB in ChromaDB
- **Search Coverage**: Wide variety of API domains and endpoints
- **Time**: ~30-60 minutes for full import (depends on CPU/disk)

## Verifying Import

### 1. Check Document Count

Go to **Home** page and check:
- "Documents Indexed" should show increased count
- "Collection Statistics" updates

### 2. Test Search

Go to **Search** page and try:
- `authentication` - Should find auth-related endpoints
- `payment` - Should find payment APIs (Stripe, PayPal, etc.)
- `POST /users` - Should find user creation endpoints
- `GitHub` - Should find GitHub API endpoints

### 3. Browse Documents

Go to **Documents Library**:
- Click "Load Documents"
- You should see many new API specifications
- Check different sources (openapi, postman, etc.)

### 4. Test Chat

Go to **Chat** and ask:
- "Show me payment APIs"
- "How do I authenticate with GitHub API?"
- "What POST endpoints are available?"

## Troubleshooting

### Error: "kaggle: command not found"

```bash
pip install kaggle
```

### Error: "Could not find kaggle.json"

Make sure `~/.kaggle/kaggle.json` exists:

```bash
ls -la ~/.kaggle/kaggle.json
```

### Error: "Cannot connect to backend"

Start the backend:

```bash
python -m uvicorn src.api.app:app --reload
```

### Error: "401 Unauthorized" from Kaggle

Your API token might be invalid:
1. Delete `~/.kaggle/kaggle.json`
2. Go to https://www.kaggle.com/settings/account
3. Create a new API token
4. Replace the file

### Import is Very Slow

- Use `--limit 100` to test with fewer files first
- Check your disk space (need ~1GB free)
- Reduce `--batch-size` if experiencing errors

### Some Files Fail to Upload

This is normal! Not all files might be valid:
- Some might be too large
- Some might have parsing issues
- Check the error summary at the end
- Usually 90%+ success rate is good

## Advanced: Manual Dataset Exploration

To manually explore the dataset before importing:

```bash
# Download only (don't import)
kaggle datasets download -d shivd24coder/ultimate-api-dataset-1000-data-sources

# Unzip
unzip ultimate-api-dataset-1000-data-sources.zip -d kaggle_data/

# Explore structure
cd kaggle_data/
ls -lh
```

Then you can:
- Manually inspect files
- Select specific APIs
- Upload via UI (Documents page → Upload)

## Dataset Structure

The Kaggle dataset typically contains:

```
ultimate-api-dataset-1000-data-sources/
├── openapi/
│   ├── stripe.json
│   ├── github.json
│   ├── twilio.json
│   └── ...
├── swagger/
│   ├── petstore.yaml
│   ├── ...
├── postman/
│   ├── collections/
│   └── ...
└── README.md
```

## Performance Tips

### For Large Imports

- **Increase batch pauses**: `--batch-size 5` for slower, safer uploads
- **Monitor memory**: Watch backend memory usage (`htop` or Task Manager)
- **Check logs**: Backend logs show detailed import progress

### For Testing

- **Small test first**: `--limit 10` to verify everything works
- **Then medium**: `--limit 100` to check performance
- **Finally full**: Remove `--limit` for complete import

## Cleanup

To remove the downloaded dataset files:

```bash
rm -rf data/kaggle_import/
```

This doesn't affect your ChromaDB - only removes the downloaded source files.

## Next Steps

After importing:

1. **Test Search Performance**: Try complex queries
2. **Generate Diagrams**: Use imported APIs for diagram testing
3. **Test Chat**: Ask questions about the imported APIs
4. **Optimize**: Adjust min_score threshold based on new data

## Support

If you encounter issues:

1. Check the error summary in import output
2. Verify backend logs for detailed errors
3. Try with `--limit 10` first to isolate issues
4. Check GitHub issues for known problems

## See Also

- [Search Guide](./SEARCH_GUIDE.md) - Understanding search with large collections
- [API Documentation](../README.md) - Main project documentation
- [Kaggle Dataset](https://www.kaggle.com/datasets/shivd24coder/ultimate-api-dataset-1000-data-sources) - Original dataset source
