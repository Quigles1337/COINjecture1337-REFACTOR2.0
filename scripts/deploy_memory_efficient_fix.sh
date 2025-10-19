#!/bin/bash

# Deploy Memory-Efficient Consensus Fix
# Applies conjecture about balancing memory and processing

set -e

echo "=== Deploying Memory-Efficient Consensus Fix ==="

# Deploy memory optimization script
echo "Deploying memory optimization script..."
scp -i ~/.ssh/coinjecture_droplet_key scripts/optimize_consensus_memory.py root@167.172.213.70:/opt/coinjecture-consensus/

# Deploy memory-efficient consensus fix
echo "Deploying memory-efficient consensus fix..."
scp -i ~/.ssh/coinjecture_droplet_key scripts/memory_efficient_consensus_fix.py root@167.172.213.70:/opt/coinjecture-consensus/

# Deploy to droplet
echo "Deploying to droplet..."
ssh -i ~/.ssh/coinjecture_droplet_key -o ConnectTimeout=15 -o StrictHostKeyChecking=no root@167.172.213.70 << 'EOF'
echo "=== Applying Memory-Efficient Consensus Fix ==="

# Stop consensus service
echo "Stopping consensus service..."
systemctl stop coinjecture-consensus

# Apply memory optimizations
echo "Applying memory optimizations..."
cd /opt/coinjecture-consensus
chmod +x optimize_consensus_memory.py
python3 optimize_consensus_memory.py

# Apply memory-efficient fix
echo "Applying memory-efficient consensus fix..."
chmod +x memory_efficient_consensus_fix.py
python3 memory_efficient_consensus_fix.py

# Start consensus service
echo "Starting consensus service..."
systemctl start coinjecture-consensus

# Wait for service to start
echo "Waiting for service to start..."
sleep 10

# Check service status
echo "Checking service status..."
systemctl status coinjecture-consensus --no-pager

# Check memory usage
echo "Checking memory usage..."
free -h

# Check if service is running
echo "Checking if service is running..."
if systemctl is-active --quiet coinjecture-consensus; then
    echo "✅ Consensus service is running"
else
    echo "❌ Consensus service is not running"
    exit 1
fi

echo "=== Memory-Efficient Consensus Fix Applied Successfully ==="
EOF

echo "=== Memory-Efficient Consensus Fix Deployed ==="
