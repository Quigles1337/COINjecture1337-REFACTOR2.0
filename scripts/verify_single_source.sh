#!/bin/bash
# Verify single source of truth

echo "🔍 Verifying single source of truth..."

# 1. Only one database
echo "Checking databases..."
db_count=$(find /opt -name "*.db" -type f | grep -v backup | wc -l)
if [ $db_count -eq 1 ]; then
    echo "✅ Found $db_count database (expected 1)"
    find /opt -name "*.db" -type f | grep -v backup
else
    echo "❌ Found $db_count databases, expected 1"
    find /opt -name "*.db" -type f | grep -v backup
    exit 1
fi

# 2. Only one API server process
echo "Checking API servers..."
api_count=$(ps aux | grep faucet_server | grep -v grep | wc -l)
if [ $api_count -eq 1 ]; then
    echo "✅ Found $api_count API server (expected 1)"
    ps aux | grep faucet_server | grep -v grep
else
    echo "❌ Found $api_count API servers, expected 1"
    ps aux | grep faucet_server | grep -v grep
    exit 1
fi

# 3. Only one code directory
echo "Checking code installations..."
code_count=$(find /opt -name "faucet_server_cors_fixed.py" | wc -l)
if [ $code_count -eq 1 ]; then
    echo "✅ Found $code_count installation (expected 1)"
    find /opt -name "faucet_server_cors_fixed.py"
else
    echo "❌ Found $code_count installations, expected 1"
    find /opt -name "faucet_server_cors_fixed.py"
    exit 1
fi

# 4. Test API endpoint
echo "Testing API endpoint..."
gas_value=$(curl -s "https://api.coinjecture.com/v1/data/block/1001" | jq -r '.data.gas_used')

if [ "$gas_value" == "null" ] || [ -z "$gas_value" ]; then
    echo "❌ API returning null for gas_used"
    exit 1
else
    echo "✅ API returning gas_used: $gas_value"
fi

echo "🎉 Single source of truth verified successfully!"
