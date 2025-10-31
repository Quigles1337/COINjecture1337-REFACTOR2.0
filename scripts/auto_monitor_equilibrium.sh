#!/bin/bash
# Auto-Monitor Equilibrium Status
# Continuously checks readiness and alerts when ready

DROPLET_IP="167.172.213.70"
DROPLET_USER="root"
CHECK_INTERVAL=300  # 5 minutes

echo "⚖️  Auto-Monitoring Equilibrium Status"
echo "========================================"
echo "Checking every $CHECK_INTERVAL seconds..."
echo "Press Ctrl+C to stop"
echo ""

while true; do
    echo ""
    echo "--- $(date '+%Y-%m-%d %H:%M:%S') ---"
    
    ssh $DROPLET_USER@$DROPLET_IP "cd /opt/coinjecture && python3 scripts/check_regeneration_readiness.py --db data/blockchain.db 2>&1 | tail -15"
    
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo ""
        echo "🎉 READY TO REGENERATE!"
        echo ""
        echo "Run regeneration:"
        echo "  ssh $DROPLET_USER@$DROPLET_IP \"cd /opt/coinjecture && python3 scripts/catalog_and_regenerate_cids.py --regenerate --max-blocks 100\""
        echo ""
        break
    else
        echo ""
        echo "⏳ Not ready yet. Checking again in $CHECK_INTERVAL seconds..."
        sleep $CHECK_INTERVAL
    fi
done

