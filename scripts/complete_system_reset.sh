#!/bin/bash
# Complete System Reset Script
# Stops all services, deletes all databases, reboots droplet

set -e

DROPLET_USER="root"
DROPLET_HOST="167.172.213.70"
REMOTE_DIR="/opt/coinjecture"

echo "🔄 Starting complete system reset..."

# Stop all services
echo "⏹️  Stopping all services..."
ssh $DROPLET_USER@$DROPLET_HOST "cd $REMOTE_DIR && pkill -f 'consensus\|api\|node\|mining\|faucet' || true"
ssh $DROPLET_USER@$DROPLET_HOST "cd /opt/coinjecture && pkill -f 'consensus\|automatic\|p2p' || true"

# Wait for services to stop
sleep 5

# Delete ALL databases
echo "🗑️  Deleting all databases..."
ssh $DROPLET_USER@$DROPLET_HOST "rm -rf $REMOTE_DIR/data/*.db"
ssh $DROPLET_USER@$DROPLET_HOST "rm -rf $REMOTE_DIR/backups/**/*.db"
ssh $DROPLET_USER@$DROPLET_HOST "rm -rf $REMOTE_DIR/src/data/*.db"
ssh $DROPLET_USER@$DROPLET_HOST "rm -rf /opt/coinjecture/data/*.db"
ssh $DROPLET_USER@$DROPLET_HOST "rm -rf /opt/coinjecture/data/faucet_ingest.db"

# Clear logs
echo "🧹 Clearing logs..."
ssh $DROPLET_USER@$DROPLET_HOST "rm -rf $REMOTE_DIR/logs/*.log"
ssh $DROPLET_USER@$DROPLET_HOST "rm -rf /opt/coinjecture/logs/*.log"

# Create fresh data directory
echo "📁 Creating fresh data directory..."
ssh $DROPLET_USER@$DROPLET_HOST "mkdir -p $REMOTE_DIR/data"
ssh $DROPLET_USER@$DROPLET_HOST "mkdir -p $REMOTE_DIR/logs"

# Reboot droplet
echo "🔄 Rebooting droplet..."
ssh $DROPLET_USER@$DROPLET_HOST "reboot"

echo "⏳ Waiting for droplet to come back online..."
sleep 60

# Wait for SSH to be available
echo "🔍 Checking if droplet is back online..."
for i in {1..30}; do
    if ssh -o ConnectTimeout=5 $DROPLET_USER@$DROPLET_HOST "echo 'Droplet is online'" 2>/dev/null; then
        echo "✅ Droplet is back online"
        break
    else
        echo "⏳ Still waiting... ($i/30)"
        sleep 10
    fi
done

echo "✅ Complete system reset finished"
echo "📊 System status:"
ssh $DROPLET_USER@$DROPLET_HOST "df -h /opt && ls -la $REMOTE_DIR/data/"
