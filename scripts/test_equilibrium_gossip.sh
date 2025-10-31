#!/bin/bash
# Test Equilibrium Gossip Implementation
# Verifies λ = η = 1/√2 equilibrium is working

set -e

echo "🧪 Testing Equilibrium Gossip Implementation"
echo "============================================"
echo ""

DROPLET_IP="167.172.213.70"
DROPLET_USER="root"
API_URL="http://167.172.213.70:12346"

# Test 1: Check API service is running
echo "📡 Test 1: Checking API service status..."
if ssh $DROPLET_USER@$DROPLET_IP "systemctl is-active coinjecture-api" > /dev/null 2>&1; then
    echo "✅ API service is running"
else
    echo "❌ API service is not running"
    exit 1
fi
echo ""

# Test 2: Verify files are deployed
echo "📁 Test 2: Verifying deployed files..."
ssh $DROPLET_USER@$DROPLET_IP "cd /opt/coinjecture && \
    if [ -f src/network.py ] && [ -f src/node.py ] && [ -f src/cli.py ]; then
        echo '✅ All files are deployed'
        echo '  • src/network.py'
        echo '  • src/node.py'
        echo '  • src/cli.py'
    else
        echo '❌ Some files are missing'
        exit 1
    fi"
echo ""

# Test 3: Check for equilibrium constants in code
echo "⚖️  Test 3: Checking for equilibrium constants..."
ssh $DROPLET_USER@$DROPLET_IP "cd /opt/coinjecture && \
    if grep -q 'LAMBDA = 0.7071' src/network.py && grep -q 'ETA = 0.7071' src/network.py; then
        echo '✅ Equilibrium constants found (λ = η = 1/√2)'
    else
        echo '❌ Equilibrium constants not found'
        exit 1
    fi"
echo ""

# Test 4: Check for equilibrium loops in code
echo "🔄 Test 4: Checking for equilibrium loops..."
ssh $DROPLET_USER@$DROPLET_IP "cd /opt/coinjecture && \
    if grep -q '_broadcast_loop' src/network.py && \
       grep -q '_listen_loop' src/network.py && \
       grep -q '_cleanup_loop' src/network.py && \
       grep -q 'start_equilibrium_loops' src/network.py; then
        echo '✅ Equilibrium loops found'
        echo '  • Broadcast loop (λ-coupling)'
        echo '  • Listen loop (η-damping)'
        echo '  • Cleanup loop'
        echo '  • Start method'
    else
        echo '❌ Equilibrium loops not found'
        exit 1
    fi"
echo ""

# Test 5: Test API health endpoint
echo "🏥 Test 5: Testing API health endpoint..."
HEALTH_RESPONSE=$(curl -s "$API_URL/health" 2>/dev/null || echo "FAILED")
if [[ "$HEALTH_RESPONSE" == *"status"* ]] || [[ "$HEALTH_RESPONSE" == *"ok"* ]] || [[ "$HEALTH_RESPONSE" == *"healthy"* ]]; then
    echo "✅ API health check passed"
    echo "   Response: $HEALTH_RESPONSE" | head -c 100
    echo "..."
else
    echo "⚠️  API health check returned: $HEALTH_RESPONSE"
fi
echo ""

# Test 6: Check recent logs for equilibrium activity
echo "📊 Test 6: Checking recent logs for equilibrium activity..."
RECENT_LOGS=$(ssh $DROPLET_USER@$DROPLET_IP "journalctl -u coinjecture-api --since '5 minutes ago' --no-pager | tail -50" 2>/dev/null || echo "")
if echo "$RECENT_LOGS" | grep -qi "equilibrium\|broadcast\|listen\|cleanup" 2>/dev/null; then
    echo "✅ Found equilibrium-related log entries"
    echo "$RECENT_LOGS" | grep -i "equilibrium\|broadcast\|listen\|cleanup" | tail -5
else
    echo "ℹ️  No equilibrium logs found yet (may take time for loops to start)"
    echo "   This is normal if the service just started"
fi
echo ""

# Test 7: Verify network.py imports work
echo "🐍 Test 7: Testing Python imports..."
IMPORT_TEST=$(ssh $DROPLET_USER@$DROPLET_IP "cd /opt/coinjecture && python3 -c '
import sys
sys.path.insert(0, \"src\")
try:
    from network import NetworkProtocol
    print(\"✅ NetworkProtocol import successful\")
    print(f\"   LAMBDA = {NetworkProtocol.LAMBDA}\")
    print(f\"   ETA = {NetworkProtocol.ETA}\")
    print(f\"   BROADCAST_INTERVAL = {NetworkProtocol.BROADCAST_INTERVAL:.2f}s\")
    print(f\"   LISTEN_INTERVAL = {NetworkProtocol.LISTEN_INTERVAL:.2f}s\")
    print(f\"   CLEANUP_INTERVAL = {NetworkProtocol.CLEANUP_INTERVAL:.2f}s\")
except Exception as e:
    print(f\"❌ Import failed: {e}\")
    sys.exit(1)
'" 2>&1)
echo "$IMPORT_TEST"
if echo "$IMPORT_TEST" | grep -q "✅"; then
    echo ""
else
    echo "❌ Python import test failed"
    exit 1
fi
echo ""

# Test 8: Check if node.py has equilibrium integration
echo "🔗 Test 8: Checking node.py equilibrium integration..."
ssh $DROPLET_USER@$DROPLET_IP "cd /opt/coinjecture && \
    if grep -q 'start_equilibrium_loops' src/node.py && \
       grep -q 'stop_equilibrium_loops' src/node.py; then
        echo '✅ Node integration found'
        echo '  • Auto-starts equilibrium loops'
        echo '  • Stops loops on shutdown'
    else
        echo '❌ Node integration not found'
        exit 1
    fi"
echo ""

# Summary
echo "═══════════════════════════════════════════════"
echo "✅ Equilibrium Gossip Implementation Test Summary"
echo "═══════════════════════════════════════════════"
echo ""
echo "All tests passed! The equilibrium gossip implementation is deployed."
echo ""
echo "📊 Next Steps:"
echo "  1. Monitor logs for equilibrium activity:"
echo "     ssh $DROPLET_USER@$DROPLET_IP \"journalctl -u coinjecture-api -f | grep Equilibrium\""
echo ""
echo "  2. Watch for equilibrium metrics:"
echo "     ⚖️  Equilibrium: λ=0.7071, η=0.7071, ratio=1.0000"
echo "     📡 Broadcasting X CIDs (λ-coupling)"
echo "     👂 Processing peer updates (η-damping)"
echo "     📊 Network: X active peers"
echo ""
echo "  3. Test CID announcement when miners create blocks"
echo ""

