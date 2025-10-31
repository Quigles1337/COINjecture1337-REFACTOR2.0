#!/bin/bash
# Complete Equilibrium Deployment
# Starts equilibrium service and restarts API to connect it

set -e

echo "⚖️  Complete Equilibrium Deployment"
echo "===================================="
echo ""

DROPLET_IP="167.172.213.70"
DROPLET_USER="root"
REMOTE_DIR="/opt/coinjecture"

# Step 1: Start equilibrium service
echo "1️⃣  Starting equilibrium service..."
ssh $DROPLET_USER@$DROPLET_IP "cd $REMOTE_DIR && bash scripts/start_equilibrium_service.sh"
sleep 3

# Step 2: Restart API service to connect
echo ""
echo "2️⃣  Restarting API service..."
ssh $DROPLET_USER@$DROPLET_IP "systemctl restart coinjecture-api"
sleep 3

# Step 3: Verify both services
echo ""
echo "3️⃣  Verifying services..."
echo ""

echo "Equilibrium Service:"
if ssh $DROPLET_USER@$DROPLET_IP "pgrep -f equilibrium_service.py > /dev/null"; then
    PID=$(ssh $DROPLET_USER@$DROPLET_IP "pgrep -f equilibrium_service.py")
    echo "   ✅ Running (PID: $PID)"
else
    echo "   ❌ Not running"
fi

echo "API Service:"
if ssh $DROPLET_USER@$DROPLET_IP "systemctl is-active coinjecture-api > /dev/null"; then
    echo "   ✅ Running"
else
    echo "   ❌ Not running"
fi

echo ""
echo "4️⃣  Recent Logs:"
echo ""
echo "Equilibrium logs (last 5 lines):"
ssh $DROPLET_USER@$DROPLET_IP "tail -5 $REMOTE_DIR/logs/equilibrium.log 2>/dev/null || echo 'Logs not available yet'"
echo ""
echo "API equilibrium logs (last 10 minutes):"
ssh $DROPLET_USER@$DROPLET_IP "journalctl -u coinjecture-api --since '10 minutes ago' --no-pager 2>/dev/null | grep -i equilibrium | tail -3 || echo 'No equilibrium logs in API yet (may take time for blocks to be submitted)'"

echo ""
echo "═══════════════════════════════════════════════"
echo "✅ Deployment Complete"
echo "═══════════════════════════════════════════════"
echo ""
echo "📊 Monitor Equilibrium:"
echo "   ssh $DROPLET_USER@$DROPLET_IP \"tail -f $REMOTE_DIR/logs/equilibrium.log\""
echo ""
echo "📈 Watch for equilibrium updates:"
echo "   Look for: ⚖️  Equilibrium: λ=0.7071, η=0.7130, ratio=1.0000"
echo ""

