#!/bin/bash
# Restart API server to pick up new blockchain state

echo "🔄 Restarting API server..."

# Restart the API server
ssh root@167.172.213.70 "systemctl restart coinjecture-api || service coinjecture-api restart || pkill -f 'python.*api'"

# Wait for server to restart
sleep 5

echo "✅ API server restarted"
echo "💡 Server should now show the latest blockchain state"
