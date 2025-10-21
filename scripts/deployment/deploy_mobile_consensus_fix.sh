#!/bin/bash
# Deploy mobile consensus sync fix to server

echo "🚀 Deploying mobile consensus sync fix..."

# Server details
SERVER_HOST="167.172.213.70"
SERVER_USER="coinjecture"
SERVER_PATH="/home/coinjecture/COINjecture"

echo "📋 Manual deployment instructions:"
echo "1. SSH to the server: ssh $SERVER_USER@$SERVER_HOST"
echo "2. Navigate to: cd $SERVER_PATH"
echo "3. Backup current file: cp src/api/faucet_server.py src/api/faucet_server.py.backup"
echo "4. Replace with updated file from this repository"
echo "5. Restart API server: sudo systemctl restart coinjecture-api"
echo ""
echo "🔧 The fix removes duplicate /v1/ingest/block endpoint that was causing mobile submissions to hit wrong endpoint"
echo "📱 Mobile mining will now properly sync to consensus engine"
echo ""
echo "📄 Updated file: src/api/faucet_server.py"
echo "   - Changed duplicate endpoint from /v1/ingest/block to /v1/ingest/block/cli"
echo "   - Mobile version now hits correct endpoint for BlockEvent processing"
echo "   - Consensus service can properly process mobile mining submissions"
