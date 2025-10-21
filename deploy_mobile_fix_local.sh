#!/bin/bash
# Deploy mobile consensus sync fix to remote server

echo "🚀 Deploying mobile consensus sync fix to remote server..."

# Server details
SERVER_HOST="167.172.213.70"
SERVER_USER="coinjecture"
SERVER_PATH="/home/coinjecture/COINjecture"

# Create deployment package
echo "📦 Creating deployment package..."
mkdir -p /tmp/coinjecture_deploy
cp src/api/faucet_server.py /tmp/coinjecture_deploy/

# Create deployment script for server
cat > /tmp/coinjecture_deploy/deploy_on_server.sh << 'EOF'
#!/bin/bash
echo "🔧 Applying mobile consensus sync fix on server..."

# Backup current file
cp src/api/faucet_server.py src/api/faucet_server.py.backup
echo "✅ Backed up current faucet_server.py"

# Replace with updated file
cp faucet_server.py src/api/faucet_server.py
echo "✅ Updated faucet_server.py with mobile consensus sync fix"

# Restart API server
echo "🔄 Restarting API server..."
sudo systemctl restart coinjecture-api || echo "⚠️  systemctl restart failed, trying manual restart..."

# Try alternative restart method
pkill -f "python.*faucet_server.py" || echo "No existing process found"
cd /home/coinjecture/COINjecture
nohup python3 src/api/faucet_server.py > logs/api_server.log 2>&1 &
echo $! > logs/api_server.pid

echo "✅ API server restarted"
echo "🎉 Mobile consensus sync fix deployed successfully!"
echo "📱 Mobile mining should now properly sync to consensus engine"
EOF

chmod +x /tmp/coinjecture_deploy/deploy_on_server.sh

echo "📋 Deployment instructions:"
echo "1. Copy deployment package to server:"
echo "   scp -r /tmp/coinjecture_deploy/ $SERVER_USER@$SERVER_HOST:/tmp/"
echo ""
echo "2. SSH to server and run deployment:"
echo "   ssh $SERVER_USER@$SERVER_HOST"
echo "   cd /tmp/coinjecture_deploy"
echo "   ./deploy_on_server.sh"
echo ""
echo "🔧 The fix removes duplicate /v1/ingest/block endpoint that was causing mobile submissions to hit wrong endpoint"
echo "📱 Mobile mining will now properly sync to consensus engine"
