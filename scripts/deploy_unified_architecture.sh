#!/bin/bash
# Deploy Unified Architecture
# Complete deployment of unified consensus service with metrics engine integration

set -e

DROPLET_USER="root"
DROPLET_HOST="167.172.213.70"
REMOTE_DIR="/opt/coinjecture"
LOCAL_PROJECT_DIR="/Users/sarahmarin/Downloads/COINjecture-main 4"

echo "🚀 Starting unified architecture deployment..."

# Wait for droplet to be ready (after reboot)
echo "⏳ Waiting for droplet to be ready..."
sleep 30

# Check if droplet is accessible
echo "🔍 Checking droplet connectivity..."
if ! ssh -o ConnectTimeout=10 $DROPLET_USER@$DROPLET_HOST "echo 'Droplet is ready'" 2>/dev/null; then
    echo "❌ Droplet is not accessible, waiting longer..."
    sleep 30
fi

# Upload updated files
echo "📤 Uploading updated files..."

# Core files
scp "$LOCAL_PROJECT_DIR/src/metrics_engine.py" "$DROPLET_USER@$DROPLET_HOST:$REMOTE_DIR/src/"
scp "$LOCAL_PROJECT_DIR/src/consensus.py" "$DROPLET_USER@$DROPLET_HOST:$REMOTE_DIR/src/"
scp "$LOCAL_PROJECT_DIR/src/unified_consensus_service.py" "$DROPLET_USER@$DROPLET_HOST:$REMOTE_DIR/src/"
scp "$LOCAL_PROJECT_DIR/src/network_sync_service.py" "$DROPLET_USER@$DROPLET_HOST:$REMOTE_DIR/src/"

# API files
scp "$LOCAL_PROJECT_DIR/src/api/blockchain_storage.py" "$DROPLET_USER@$DROPLET_HOST:$REMOTE_DIR/src/api/"
scp "$LOCAL_PROJECT_DIR/src/api/faucet_server_cors_fixed.py" "$DROPLET_USER@$DROPLET_HOST:$REMOTE_DIR/src/api/"

# Scripts
scp "$LOCAL_PROJECT_DIR/scripts/initialize_genesis_proper.py" "$DROPLET_USER@$DROPLET_HOST:$REMOTE_DIR/scripts/"

echo "✅ Files uploaded successfully"

# Initialize genesis block
echo "🏗️  Initializing genesis block..."
ssh $DROPLET_USER@$DROPLET_HOST "cd $REMOTE_DIR && python3 scripts/initialize_genesis_proper.py"

# Start unified consensus service
echo "🔄 Starting unified consensus service..."
ssh $DROPLET_USER@$DROPLET_HOST "cd $REMOTE_DIR && nohup python3 src/unified_consensus_service.py > logs/consensus.log 2>&1 & echo \$! > logs/consensus.pid"

# Start network sync service
echo "🌐 Starting network sync service..."
ssh $DROPLET_USER@$DROPLET_HOST "cd $REMOTE_DIR && nohup python3 src/network_sync_service.py > logs/sync.log 2>&1 & echo \$! > logs/sync.pid"

# Wait for services to start
sleep 10

# Start API server
echo "🌐 Starting API server..."
ssh $DROPLET_USER@$DROPLET_HOST "cd $REMOTE_DIR && nohup python3 src/api/faucet_server_cors_fixed.py > logs/api.log 2>&1 & echo \$! > logs/api.pid"

# Wait for API to start
sleep 10

# Verify services are running
echo "🔍 Verifying services..."
ssh $DROPLET_USER@$DROPLET_HOST "cd $REMOTE_DIR && ps aux | grep -E '(unified_consensus|network_sync|faucet_server)' | grep -v grep"

# Test API endpoint
echo "🧪 Testing API endpoint..."
sleep 5
if curl -s "https://api.coinjecture.com/health" > /dev/null; then
    echo "✅ API is responding"
else
    echo "⚠️  API not responding yet, checking logs..."
    ssh $DROPLET_USER@$DROPLET_HOST "cd $REMOTE_DIR && tail -10 logs/api.log"
fi

# Check database status
echo "📊 Checking database status..."
ssh $DROPLET_USER@$DROPLET_HOST "cd $REMOTE_DIR && ls -la data/ && sqlite3 data/blockchain.db 'SELECT COUNT(*) as block_count FROM blocks;'"

echo "✅ Unified architecture deployment completed"
echo "📋 Services running:"
echo "   - Unified Consensus Service"
echo "   - Network Sync Service" 
echo "   - API Server"
echo "🌐 API: https://api.coinjecture.com"
echo "🌐 Frontend: https://coinjecture.com"
