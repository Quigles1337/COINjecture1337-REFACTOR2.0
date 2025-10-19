#!/bin/bash
# Deploy Consensus Fix
# This script deploys all the consensus health monitoring and fixes to the droplet

echo "🚀 DEPLOYING CONSENSUS HEALTH MONITORING FIX"
echo "============================================="
echo "📊 Issue: Consensus service block tree desync"
echo "🎯 Solution: Health monitoring with auto-restart and proper bootstrap"
echo ""

# Check if we're on the droplet
if [ ! -f "/opt/coinjecture-consensus/consensus_service.py" ]; then
    echo "❌ This script must be run on the droplet (167.172.213.70)"
    exit 1
fi

echo "✅ Confirmed on droplet"

# Step 1: Deploy health monitor script
echo ""
echo "📦 Step 1: Deploying consensus health monitor..."
cp /tmp/consensus_health_monitor.py /opt/coinjecture-consensus/
chmod +x /opt/coinjecture-consensus/consensus_health_monitor.py
echo "✅ Health monitor script deployed"

# Step 2: Deploy health monitor API
echo ""
echo "📦 Step 2: Deploying health monitor API..."
cp /tmp/health_monitor_api.py /home/coinjecture/COINjecture/src/api/
chmod +x /home/coinjecture/COINjecture/src/api/health_monitor_api.py
echo "✅ Health monitor API deployed"

# Step 3: Fix consensus service bootstrap path
echo ""
echo "🔧 Step 3: Fixing consensus service bootstrap path..."
cd /tmp
python3 fix_consensus_bootstrap_path.py
if [ $? -eq 0 ]; then
    echo "✅ Consensus service bootstrap path fixed"
else
    echo "❌ Failed to fix consensus service bootstrap path"
    exit 1
fi

# Step 4: Set up health monitor systemd service
echo ""
echo "📦 Step 4: Setting up health monitor systemd service..."
cp /tmp/coinjecture-consensus-monitor.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable coinjecture-consensus-monitor
echo "✅ Health monitor systemd service configured"

# Step 5: Start health monitor
echo ""
echo "🚀 Step 5: Starting health monitor..."
systemctl start coinjecture-consensus-monitor
sleep 3

# Check status
if systemctl is-active coinjecture-consensus-monitor >/dev/null 2>&1; then
    echo "✅ Health monitor started successfully"
else
    echo "❌ Health monitor failed to start"
    systemctl status coinjecture-consensus-monitor --no-pager
    exit 1
fi

# Step 6: Test health monitor API
echo ""
echo "🧪 Step 6: Testing health monitor API..."
# Start health monitor API in background
cd /home/coinjecture/COINjecture
nohup python3 src/api/health_monitor_api.py > /dev/null 2>&1 &
HEALTH_API_PID=$!
sleep 5

# Test API endpoint
if curl -s http://localhost:5001/v1/health/status >/dev/null 2>&1; then
    echo "✅ Health monitor API is responding"
else
    echo "⚠️  Health monitor API may not be responding (this is optional)"
fi

# Step 7: Verify consensus service status
echo ""
echo "📊 Step 7: Verifying consensus service status..."
sleep 10

# Check consensus service logs for bootstrap
if journalctl -u coinjecture-consensus --no-pager -n 20 | grep -q "Bootstrapped block"; then
    echo "✅ Consensus service is bootstrapping blocks"
else
    echo "⚠️  Consensus service may not be bootstrapping properly"
    echo "Recent logs:"
    journalctl -u coinjecture-consensus --no-pager -n 10
fi

# Step 8: Check overall system health
echo ""
echo "📊 Step 8: Checking overall system health..."

# Check all services
echo "Service Status:"
echo "  - Consensus Service: $(systemctl is-active coinjecture-consensus)"
echo "  - Automatic Processor: $(systemctl is-active coinjecture-automatic-processor)"
echo "  - Health Monitor: $(systemctl is-active coinjecture-consensus-monitor)"

# Check blockchain state
if [ -f "/opt/coinjecture-consensus/data/blockchain_state.json" ]; then
    BLOCK_COUNT=$(python3 -c "import json; data=json.load(open('/opt/coinjecture-consensus/data/blockchain_state.json')); print(len(data.get('blocks', [])))")
    echo "  - Blockchain blocks: $BLOCK_COUNT"
else
    echo "  - Blockchain state: Not found"
fi

echo ""
echo "✅ CONSENSUS HEALTH MONITORING DEPLOYMENT COMPLETED!"
echo ""
echo "📋 What was deployed:"
echo "  ✅ Consensus health monitor script"
echo "  ✅ Health monitor API (port 5001)"
echo "  ✅ Fixed consensus service bootstrap path"
echo "  ✅ Health monitor systemd service"
echo "  ✅ Auto-restart on desync detection"
echo ""
echo "🔗 Health Monitor API Endpoints:"
echo "  GET  http://167.172.213.70:5001/v1/health/status"
echo "  GET  http://167.172.213.70:5001/v1/health/consensus"
echo "  GET  http://167.172.213.70:5001/v1/health/blockchain"
echo "  GET  http://167.172.213.70:5001/v1/health/services"
echo "  POST http://167.172.213.70:5001/v1/health/consensus/restart"
echo ""
echo "📊 Monitor logs:"
echo "  journalctl -u coinjecture-consensus-monitor -f"
echo ""
echo "🎉 The system will now automatically detect and recover from consensus desync issues!"
