#!/bin/bash
# ChromaDB Backup Script
# Usage: ./backup-chroma.sh [backup-destination]

set -e

# Configuration
BACKUP_DIR=${1:-/backups/chroma}
CHROMA_DATA=${CHROMA_DATA_DIR:-/app/data/chroma_db}
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/chroma_backup_${DATE}.tar.gz"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

# Cloud storage configuration (optional)
S3_BUCKET=${S3_BACKUP_BUCKET:-""}
GCS_BUCKET=${GCS_BACKUP_BUCKET:-""}
AZURE_CONTAINER=${AZURE_BACKUP_CONTAINER:-""}

echo "🗄️  ChromaDB Backup Script"
echo "   Source: $CHROMA_DATA"
echo "   Destination: $BACKUP_FILE"
echo "   Retention: $RETENTION_DAYS days"
echo ""

# Check if source exists
if [ ! -d "$CHROMA_DATA" ]; then
    echo "❌ Error: ChromaDB data directory not found: $CHROMA_DATA"
    exit 1
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Step 1: Create backup
echo "📦 Creating backup..."
tar -czf "$BACKUP_FILE" -C "$(dirname "$CHROMA_DATA")" "$(basename "$CHROMA_DATA")"

# Check if backup was created successfully
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Error: Backup file was not created"
    exit 1
fi

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "✅ Backup created: $BACKUP_FILE ($BACKUP_SIZE)"

# Step 2: Upload to cloud storage (if configured)
if [ -n "$S3_BUCKET" ]; then
    echo "☁️  Uploading to S3: s3://$S3_BUCKET/chroma/"
    aws s3 cp "$BACKUP_FILE" "s3://$S3_BUCKET/chroma/" --storage-class STANDARD_IA
    echo "✅ Uploaded to S3"
fi

if [ -n "$GCS_BUCKET" ]; then
    echo "☁️  Uploading to GCS: gs://$GCS_BUCKET/chroma/"
    gsutil cp "$BACKUP_FILE" "gs://$GCS_BUCKET/chroma/"
    echo "✅ Uploaded to GCS"
fi

if [ -n "$AZURE_CONTAINER" ]; then
    echo "☁️  Uploading to Azure Blob Storage: $AZURE_CONTAINER/chroma/"
    az storage blob upload \
        --container-name "$AZURE_CONTAINER" \
        --name "chroma/$(basename "$BACKUP_FILE")" \
        --file "$BACKUP_FILE"
    echo "✅ Uploaded to Azure"
fi

# Step 3: Clean up old backups
echo "🧹 Cleaning up old backups (older than $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "chroma_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

# Count remaining backups
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "chroma_backup_*.tar.gz" | wc -l)
echo "📊 Total backups retained: $BACKUP_COUNT"

# Step 4: Verify backup integrity
echo "🔍 Verifying backup integrity..."
if tar -tzf "$BACKUP_FILE" > /dev/null 2>&1; then
    echo "✅ Backup integrity verified"
else
    echo "❌ Error: Backup file is corrupted!"
    exit 1
fi

echo ""
echo "🎉 Backup completed successfully!"
echo ""
echo "📋 Backup details:"
echo "   File: $BACKUP_FILE"
echo "   Size: $BACKUP_SIZE"
echo "   Date: $DATE"
echo ""
echo "💡 To restore from this backup:"
echo "   ./restore-chroma.sh $BACKUP_FILE"
