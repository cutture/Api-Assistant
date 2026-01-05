#!/bin/bash
# ChromaDB Restore Script
# Usage: ./restore-chroma.sh <backup-file>

set -e

# Configuration
BACKUP_FILE=$1
CHROMA_DATA=${CHROMA_DATA_DIR:-/app/data/chroma_db}
RESTORE_DIR=$(dirname "$CHROMA_DATA")

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup-file>"
    echo ""
    echo "Example:"
    echo "  $0 /backups/chroma/chroma_backup_20250127_120000.tar.gz"
    echo ""
    echo "Available backups:"
    find /backups/chroma -name "chroma_backup_*.tar.gz" -type f 2>/dev/null | sort -r | head -10
    exit 1
fi

echo "🔄 ChromaDB Restore Script"
echo "   Backup file: $BACKUP_FILE"
echo "   Restore to: $CHROMA_DATA"
echo ""

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Verify backup integrity
echo "🔍 Verifying backup integrity..."
if ! tar -tzf "$BACKUP_FILE" > /dev/null 2>&1; then
    echo "❌ Error: Backup file is corrupted!"
    exit 1
fi
echo "✅ Backup integrity verified"

# Warning and confirmation
echo ""
echo "⚠️  WARNING: This will REPLACE the current ChromaDB data!"
echo "   Current data directory: $CHROMA_DATA"
echo ""
echo "   Type 'yes' to continue or anything else to cancel:"
read -r CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Restore cancelled"
    exit 0
fi

# Step 1: Stop application (if running in Docker)
if docker ps --format '{{.Names}}' | grep -q "api-assistant"; then
    echo "🛑 Stopping application..."
    docker-compose down
    SHOULD_RESTART=true
else
    SHOULD_RESTART=false
fi

# Step 2: Backup current data (just in case)
if [ -d "$CHROMA_DATA" ]; then
    BACKUP_CURRENT="${CHROMA_DATA}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "💾 Backing up current data to: $BACKUP_CURRENT"
    mv "$CHROMA_DATA" "$BACKUP_CURRENT"
fi

# Step 3: Restore from backup
echo "📦 Restoring from backup..."
tar -xzf "$BACKUP_FILE" -C "$RESTORE_DIR"

# Verify restoration
if [ -d "$CHROMA_DATA" ]; then
    echo "✅ Data restored successfully"

    # Fix permissions (if running as non-root)
    if [ "$(id -u)" != "0" ]; then
        sudo chown -R $(id -u):$(id -g) "$CHROMA_DATA"
    fi
else
    echo "❌ Error: Restoration failed!"

    # Restore from backup
    if [ -d "$BACKUP_CURRENT" ]; then
        echo "🔄 Restoring original data..."
        mv "$BACKUP_CURRENT" "$CHROMA_DATA"
    fi
    exit 1
fi

# Step 4: Restart application (if it was running)
if [ "$SHOULD_RESTART" = true ]; then
    echo "🚀 Restarting application..."
    docker-compose -f docker-compose.prod.yml up -d

    # Wait for health check
    echo "⏳ Waiting for application to start..."
    sleep 10

    # Check health
    if curl -f http://localhost:8501/_stcore/health > /dev/null 2>&1; then
        echo "✅ Application is healthy"
    else
        echo "⚠️  Warning: Application may not be healthy yet"
        echo "   Check with: docker logs api-assistant"
    fi
fi

echo ""
echo "🎉 Restore completed successfully!"
echo ""
echo "📊 Restored data:"
du -sh "$CHROMA_DATA"
echo ""
echo "💡 Original data (if any) backed up to:"
echo "   $BACKUP_CURRENT"
echo "   You can delete this after verifying the restore."
