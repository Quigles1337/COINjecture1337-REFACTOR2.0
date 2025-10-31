#!/bin/bash
# Deploy Equilibrium Gossip Implementation to Droplet
# Implements λ = η = 1/√2 equilibrium through timed gossip intervals

set -e

echo "⚖️  Deploying Equilibrium Gossip Implementation"
echo "=============================================="

# Configuration
DROPLET_IP="167.172.213.70"
DROPLET_USER="root"
REMOTE_DIR="/opt/coinjecture"
LOCAL_PROJECT_DIR="/Users/sarahmarin/Downloads/COINjecture-main 5"

echo "📋 Deployment Configuration:"
echo "  Droplet: $DROPLET_IP"
echo "  User: $DROPLET_USER"
echo "  Remote Dir: $REMOTE_DIR"
echo "  Local Dir: $LOCAL_PROJECT_DIR"
echo ""

# Test SSH connection
echo "🔐 Testing SSH connection..."
if ! ssh -o ConnectTimeout=10 $DROPLET_USER@$DROPLET_IP "echo 'SSH connection successful'" 2>/dev/null; then
    echo "❌ Cannot connect to droplet via SSH"
    exit 1
fi
echo "✅ SSH connection successful"
echo ""

# Create backup
echo "💾 Creating backup on droplet..."
ssh $DROPLET_USER@$DROPLET_IP "
    cd $REMOTE_DIR
    if [ -d src/network.py ]; then
        mkdir -p backups
        BACKUP_NAME=\"backup-equilibrium-$(date +%Y%m%d-%H%M%S)\"
        mkdir -p backups/\$BACKUP_NAME
        cp -r src/network.py backups/\$BACKUP_NAME/ 2>/dev/null || true
        cp -r src/node.py backups/\$BACKUP_NAME/ 2>/dev/null || true
        cp -r src/cli.py backups/\$BACKUP_NAME/ 2>/dev/null || true
        echo \"✅ Backup created: backups/\$BACKUP_NAME\"
    fi
"
echo ""

# Upload updated files
echo "📤 Uploading equilibrium implementation files..."

# Core network files
echo "  → Uploading src/network.py (equilibrium loops)..."
scp "$LOCAL_PROJECT_DIR/src/network.py" "$DROPLET_USER@$DROPLET_IP:$REMOTE_DIR/src/"

echo "  → Uploading src/node.py (equilibrium integration)..."
scp "$LOCAL_PROJECT_DIR/src/node.py" "$DROPLET_USER@$DROPLET_IP:$REMOTE_DIR/src/"

echo "  → Uploading src/cli.py (CID queue logging)..."
scp "$LOCAL_PROJECT_DIR/src/cli.py" "$DROPLET_USER@$DROPLET_IP:$REMOTE_DIR/src/"

echo "  → Uploading EQUILIBRIUM_GOSSIP_IMPLEMENTATION.md (documentation)..."
scp "$LOCAL_PROJECT_DIR/EQUILIBRIUM_GOSSIP_IMPLEMENTATION.md" "$DROPLET_USER@$DROPLET_IP:$REMOTE_DIR/"

echo ""
echo "✅ Files uploaded successfully"
echo ""

# Restart services that use network protocol
echo "🔄 Checking services..."
ssh $DROPLET_USER@$DROPLET_IP "
    cd $REMOTE_DIR
    
    # Check if API server is running
    if pgrep -f 'faucet_server_cors_fixed.py' > /dev/null; then
        echo '📡 API server is running - will restart to load new network code'
        pkill -f 'faucet_server_cors_fixed.py' || true
        sleep 2
        echo '✅ API server stopped'
    fi
    
    # Check if consensus service is running
    if pgrep -f 'consensus_service' > /dev/null; then
        echo '⚖️  Consensus service is running - will restart to load new network code'
        pkill -f 'consensus_service' || true
        sleep 2
        echo '✅ Consensus service stopped'
    fi
    
    # Note: Services will be restarted by systemd or other process managers
    echo 'ℹ️  Services will use new equilibrium gossip code on next restart'
"

echo ""
echo "✅ Equilibrium Gossip Implementation deployed!"
echo ""
echo "📊 What was deployed:"
echo "  • λ = η = 1/√2 equilibrium constants"
echo "  • Broadcast loop: 14.14s intervals (λ-coupling)"
echo "  • Listen loop: 14.14s intervals (η-damping)"
echo "  • Cleanup loop: 70.7s intervals (network maintenance)"
echo "  • announce_proof() method for CID queuing"
echo ""
echo "🎯 Next steps:"
echo "  1. Services will automatically use new code on restart"
echo "  2. Watch logs for equilibrium metrics:"
echo "     journalctl -u coinjecture-* -f | grep 'Equilibrium'"
echo "  3. Look for:"
echo "     ⚖️  Equilibrium: λ=0.7071, η=0.7071, ratio=1.0000"
echo "     📡 Broadcasting X CIDs (λ-coupling)"
echo "     👂 Processing peer updates (η-damping)"
echo ""

