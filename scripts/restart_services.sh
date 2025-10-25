#!/bin/bash
# Restart COINjecture Services

echo "🔄 Restarting COINjecture services..."

# Stop existing services
echo "⏹️  Stopping existing services..."
pkill -f "faucet_server_cors_fixed.py" || true
pkill -f "node_service.py" || true
pkill -f "ipfs" || true

# Wait a moment
sleep 2

# Start IPFS
echo "🌐 Starting IPFS..."
ipfs daemon --init &
sleep 3

# Start node service
echo "🔗 Starting node service..."
cd /opt/coinjecture
nohup python3 src/node_service.py > logs/node.log 2>&1 &
echo $! > logs/node.pid

# Start API server
echo "🌐 Starting API server..."
nohup python3 src/api/faucet_server_cors_fixed.py > logs/api.log 2>&1 &
echo $! > logs/api.pid

echo "✅ Services restarted successfully"
echo "📊 Service status:"
ps aux | grep -E "(faucet_server|node_service|ipfs)" | grep -v grep
