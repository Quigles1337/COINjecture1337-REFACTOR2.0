#!/bin/bash

# Fix Cache Synchronization Issues
# This script updates the cache files to match the blockchain state

set -e

echo "🔧 Fixing Cache Synchronization Issues"
echo "======================================"

# Configuration
DROPLET_IP="167.172.213.70"
SSH_KEY="$HOME/.ssh/coinjecture_droplet_key"
USER="root"

echo "🔑 Using SSH key: $SSH_KEY"
echo "🌐 Connecting to droplet: $DROPLET_IP"
echo ""

# Create a comprehensive cache sync script for the droplet
cat > /tmp/fix_cache_sync_droplet.sh << 'EOF'
#!/bin/bash

echo "🔧 Fixing Cache Synchronization on Droplet"
echo "=========================================="

# 1. Check current state
echo "📊 Current blockchain state:"
BLOCKCHAIN_BLOCKS=$(jq '.blocks | length' /opt/coinjecture-consensus/data/blockchain_state.json)
echo "   Blockchain state: $BLOCKCHAIN_BLOCKS blocks"

CACHE_BLOCKS=$(jq '. | length' /home/coinjecture/COINjecture/data/cache/blocks_history.json)
echo "   Cache file: $CACHE_BLOCKS blocks"

echo ""

# 2. Update cache files with current blockchain state
echo "🔄 Updating cache files..."

# Update blocks_history.json with all blocks from blockchain state
echo "📝 Updating blocks_history.json..."
jq '.blocks' /opt/coinjecture-consensus/data/blockchain_state.json > /tmp/blocks_history_updated.json
cp /tmp/blocks_history_updated.json /home/coinjecture/COINjecture/data/cache/blocks_history.json
chown coinjecture:coinjecture /home/coinjecture/COINjecture/data/cache/blocks_history.json

# Update latest_block.json with current latest block
echo "📝 Updating latest_block.json..."
jq '.latest_block' /opt/coinjecture-consensus/data/blockchain_state.json > /tmp/latest_block_updated.json
# Add last_updated timestamp
jq '. + {"last_updated": now}' /tmp/latest_block_updated.json > /home/coinjecture/COINjecture/data/cache/latest_block.json
chown coinjecture:coinjecture /home/coinjecture/COINjecture/data/cache/latest_block.json

echo "✅ Cache files updated"

# 3. Verify the update
echo "🧪 Verifying cache update..."
NEW_CACHE_BLOCKS=$(jq '. | length' /home/coinjecture/COINjecture/data/cache/blocks_history.json)
echo "   Updated cache: $NEW_CACHE_BLOCKS blocks"

if [ "$NEW_CACHE_BLOCKS" -eq "$BLOCKCHAIN_BLOCKS" ]; then
    echo "✅ Cache synchronization successful!"
else
    echo "❌ Cache synchronization failed - block counts don't match"
    exit 1
fi

# 4. Restart the API service to ensure it picks up the new cache
echo "🔄 Restarting API service..."
systemctl restart coinjecture-api
echo "✅ API service restarted"

# 5. Test the API endpoints
echo "🧪 Testing API endpoints..."
sleep 2

echo "Testing /v1/data/block/latest:"
curl -s https://api.coinjecture.com/v1/data/block/latest | jq '.data.index'

echo "Testing /v1/data/blocks/all:"
curl -s https://api.coinjecture.com/v1/data/blocks/all | jq '.meta.total_blocks'

echo ""
echo "✅ Cache synchronization completed!"
echo "=================================="
echo ""
echo "🎯 What was fixed:"
echo "   ✅ Updated blocks_history.json with $BLOCKCHAIN_BLOCKS blocks"
echo "   ✅ Updated latest_block.json with current latest block"
echo "   ✅ Restarted API service"
echo ""
echo "🧪 Test the frontend now:"
echo "   https://coinjecture.com"
echo ""
echo "The blockchain statistics should now be consistent!"

# Clean up
rm -f /tmp/blocks_history_updated.json /tmp/latest_block_updated.json

EOF

# Make the script executable
chmod +x /tmp/fix_cache_sync_droplet.sh

echo "📤 Copying cache sync script to droplet..."
scp -i "$SSH_KEY" /tmp/fix_cache_sync_droplet.sh "$USER@$DROPLET_IP:/tmp/"

echo "🚀 Running cache sync on droplet..."
ssh -i "$SSH_KEY" "$USER@$DROPLET_IP" "chmod +x /tmp/fix_cache_sync_droplet.sh && /tmp/fix_cache_sync_droplet.sh"

# Clean up
rm -f /tmp/fix_cache_sync_droplet.sh

echo ""
echo "🎉 Cache synchronization completed!"
echo "=================================="
echo ""
echo "🧪 Test the frontend now:"
echo "   https://coinjecture.com"
echo ""
echo "The blockchain statistics should now be consistent!"
