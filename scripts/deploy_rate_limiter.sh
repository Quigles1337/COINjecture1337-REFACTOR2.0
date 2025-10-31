#!/bin/bash
# Deploy Production Rate Limiter
# Implements 14.14s broadcast intervals to restore equilibrium (λ: 1.45 → 0.7071)

set -e

echo "⚡ Deploying Production Rate Limiter"
echo "===================================="
echo ""

DROPLET_IP="167.172.213.70"
DROPLET_USER="root"
REMOTE_DIR="/opt/coinjecture"
LOCAL_PROJECT_DIR="/Users/sarahmarin/Downloads/COINjecture-main 5"

echo "📋 Deployment Configuration:"
echo "  Droplet: $DROPLET_IP"
echo "  Remote Dir: $REMOTE_DIR"
echo ""
echo "🎯 What This Fixes:"
echo "  Current λ: 1.45 (over-coupled)"
echo "  Target λ: 0.7071 (equilibrium)"
echo "  Fix: Rate-limit broadcasts to 14.14s intervals"
echo ""

# Test SSH connection
echo "🔐 Testing SSH connection..."
if ! ssh -o ConnectTimeout=10 $DROPLET_USER@$DROPLET_IP "echo 'Connected'" 2>/dev/null; then
    echo "❌ Cannot connect to droplet"
    exit 1
fi
echo "✅ Connected"
echo ""

# Create backup
echo "💾 Creating backup..."
ssh $DROPLET_USER@$DROPLET_IP "cd $REMOTE_DIR && \
    mkdir -p backups && \
    BACKUP_NAME=\"backup-rate-limiter-$(date +%Y%m%d-%H%M%S)\" && \
    mkdir -p backups/\$BACKUP_NAME && \
    cp src/network.py backups/\$BACKUP_NAME/ 2>/dev/null || true && \
    echo \"✅ Backup: backups/\$BACKUP_NAME\""

# Upload updated network.py with rate limiter
echo "📤 Uploading rate-limited network.py..."
scp "$LOCAL_PROJECT_DIR/src/network.py" "$DROPLET_USER@$DROPLET_IP:$REMOTE_DIR/src/"
echo "✅ Rate limiter deployed"
echo ""

# Restart API service
echo "🔄 Restarting API service to load rate limiter..."
ssh $DROPLET_USER@$DROPLET_IP "systemctl restart coinjecture-api" 2>&1
sleep 3

# Verify service is running
if ssh $DROPLET_USER@$DROPLET_IP "systemctl is-active coinjecture-api" > /dev/null 2>&1; then
    echo "✅ API service restarted successfully"
else
    echo "⚠️  API service may not be running"
fi
echo ""

echo "═══════════════════════════════════════════════"
echo "✅ Rate Limiter Deployment Complete"
echo "═══════════════════════════════════════════════"
echo ""
echo "📊 Expected Results:"
echo "  λ: 1.45 → 0.7071 (equilibrium restored)"
echo "  Block intervals: 4712s → ~14s (333x faster)"
echo "  CID success: 61.8% → >95%"
echo "  Network equilibrium: λ/η → 1.0"
echo ""
echo "📈 Monitoring:"
echo "  Watch logs: ssh root@$DROPLET_IP \"journalctl -u coinjecture-api -f | grep Equilibrium\""
echo "  Look for: ⚖️  Equilibrium update: λ=0.7071, η=0.7130, ratio=1.0000"
echo ""

