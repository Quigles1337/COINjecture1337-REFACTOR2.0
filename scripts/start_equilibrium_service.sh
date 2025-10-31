#!/bin/bash
# Start Equilibrium Service
# Standalone service for equilibrium gossip loops

cd /opt/coinjecture || exit 1

echo "⚖️  Starting Equilibrium Service..."
echo ""

# Check if already running
if pgrep -f "equilibrium_service.py" > /dev/null; then
    echo "⚠️  Equilibrium service already running"
    exit 0
fi

# Start service
nohup python3 src/api/equilibrium_service.py > logs/equilibrium.log 2>&1 &
PID=$!
echo $PID > logs/equilibrium.pid

echo "✅ Equilibrium service started (PID: $PID)"
echo ""
echo "Monitor logs:"
echo "  tail -f logs/equilibrium.log"
echo ""
echo "Check status:"
echo "  pgrep -f equilibrium_service.py"
echo ""

