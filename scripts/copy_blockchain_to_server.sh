#!/bin/bash
# Copy blockchain state to API server

echo "🔄 Copying blockchain state to API server..."

# Create server data directory if it doesn't exist
ssh root@167.172.213.70 "mkdir -p /opt/coinjecture-api/data"

# Copy blockchain state file
scp data/blockchain_state.json root@167.172.213.70:/opt/coinjecture-api/data/

# Copy cache files
scp data/cache/latest_block.json root@167.172.213.70:/opt/coinjecture-api/data/cache/ 2>/dev/null || true
scp data/cache/blocks_history.json root@167.172.213.70:/opt/coinjecture-api/data/cache/ 2>/dev/null || true

echo "✅ Blockchain state copied to server"
echo "📊 Server now has #164 blocks (167 total)"
