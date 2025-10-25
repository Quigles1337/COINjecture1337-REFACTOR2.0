#!/bin/bash
# Kill ALL old API servers and services

echo "🔪 Killing ALL old services..."

# Kill all faucet servers
echo "Killing faucet servers..."
pkill -9 -f faucet_server

# Kill all consensus services
echo "Killing consensus services..."
pkill -9 -f consensus_service
pkill -9 -f p2p_consensus
pkill -9 -f automatic_block

# Kill all node services
echo "Killing node services..."
pkill -9 -f node_service
pkill -9 -f mining_engine

# Kill all Python processes that might be running old code
echo "Killing all Python processes..."
pkill -9 -f "python.*faucet"
pkill -9 -f "python.*consensus"
pkill -9 -f "python.*mining"

# Wait for processes to die
sleep 3

# Verify all killed
echo "🔍 Verifying all services killed..."
remaining=$(ps aux | grep -E '(faucet|consensus|node|mining)' | grep -v grep | wc -l)

if [ $remaining -eq 0 ]; then
    echo "✅ All old services killed successfully"
else
    echo "⚠️  $remaining processes still running:"
    ps aux | grep -E '(faucet|consensus|node|mining)' | grep -v grep
fi
