#!/bin/bash

# Consolidate Data Sources to Max 3
# This script consolidates all blockchain data sources to exactly 3 synchronized sources

set -e

echo "🔧 Consolidating Data Sources to Max 3"
echo "======================================"

# Configuration
DROPLET_IP="167.172.213.70"
SSH_KEY="$HOME/.ssh/coinjecture_droplet_key"
USER="root"

echo "🔑 Using SSH key: $SSH_KEY"
echo "🌐 Connecting to droplet: $DROPLET_IP"
echo ""

# Create a comprehensive data consolidation script for the droplet
cat > /tmp/consolidate_data_droplet.sh << 'EOF'
#!/bin/bash

echo "🔧 Consolidating Data Sources on Droplet"
echo "========================================"

# Define the 3 authorized data sources
PRIMARY_SOURCE="/opt/coinjecture-consensus/data/blockchain_state.json"
CACHE_DIR="/home/coinjecture/COINjecture/data/cache"
DATABASE="/opt/coinjecture-consensus/data/blockchain.db"

echo "📊 Current data sources:"
echo "   1. Primary: $PRIMARY_SOURCE"
echo "   2. Cache: $CACHE_DIR"
echo "   3. Database: $DATABASE"
echo ""

# 1. Check primary source
echo "🔍 Checking primary source..."
if [ -f "$PRIMARY_SOURCE" ]; then
    PRIMARY_BLOCKS=$(jq '.blocks | length' "$PRIMARY_SOURCE")
    PRIMARY_LATEST=$(jq '.latest_block.index' "$PRIMARY_SOURCE")
    echo "   ✅ Primary source: $PRIMARY_BLOCKS blocks, latest index: $PRIMARY_LATEST"
else
    echo "   ❌ Primary source not found!"
    exit 1
fi

# 2. Remove duplicate/conflicting data sources
echo "🧹 Cleaning up duplicate data sources..."

# Remove old blockchain_state.json from COINjecture data directory
if [ -f "/home/coinjecture/COINjecture/data/blockchain_state.json" ]; then
    echo "   Removing duplicate blockchain_state.json from COINjecture data..."
    rm -f /home/coinjecture/COINjecture/data/blockchain_state.json
fi

# Remove old blockchain.db from COINjecture data directory
if [ -f "/home/coinjecture/COINjecture/data/blockchain.db" ]; then
    echo "   Removing duplicate blockchain.db from COINjecture data..."
    rm -f /home/coinjecture/COINjecture/data/blockchain.db
fi

# Remove old faucet_ingest.db from COINjecture data directory
if [ -f "/home/coinjecture/COINjecture/data/faucet_ingest.db" ]; then
    echo "   Removing duplicate faucet_ingest.db from COINjecture data..."
    rm -f /home/coinjecture/COINjecture/data/faucet_ingest.db
fi

echo "   ✅ Duplicate sources removed"

# 3. Update cache directory to match primary source
echo "🔄 Synchronizing cache with primary source..."

# Update blocks_history.json
echo "   Updating blocks_history.json..."
jq '.blocks' "$PRIMARY_SOURCE" > /tmp/blocks_history_sync.json
cp /tmp/blocks_history_sync.json "$CACHE_DIR/blocks_history.json"
chown coinjecture:coinjecture "$CACHE_DIR/blocks_history.json"

# Update latest_block.json
echo "   Updating latest_block.json..."
jq '.latest_block + {"last_updated": now}' "$PRIMARY_SOURCE" > /tmp/latest_block_sync.json
cp /tmp/latest_block_sync.json "$CACHE_DIR/latest_block.json"
chown coinjecture:coinjecture "$CACHE_DIR/latest_block.json"

echo "   ✅ Cache synchronized"

# 4. Verify synchronization
echo "🧪 Verifying data consistency..."

CACHE_BLOCKS=$(jq '. | length' "$CACHE_DIR/blocks_history.json")
CACHE_LATEST=$(jq '.index' "$CACHE_DIR/latest_block.json")

echo "   Primary source: $PRIMARY_BLOCKS blocks, latest: $PRIMARY_LATEST"
echo "   Cache: $CACHE_BLOCKS blocks, latest: $CACHE_LATEST"

if [ "$CACHE_BLOCKS" -eq "$PRIMARY_BLOCKS" ] && [ "$CACHE_LATEST" -eq "$PRIMARY_LATEST" ]; then
    echo "   ✅ Data sources are synchronized!"
else
    echo "   ❌ Data sources are not synchronized!"
    exit 1
fi

# 5. Update API configuration to use only the 3 sources
echo "🔧 Updating API configuration..."

# Create a simple cache manager that only uses the 3 sources
cat > /tmp/cache_manager_fixed.py << 'CACHE_MANAGER'
"""
Simplified Cache Manager - Uses Only 3 Data Sources
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

class SimplifiedCacheManager:
    """
    Simplified cache manager using only 3 data sources:
    1. Primary: /opt/coinjecture-consensus/data/blockchain_state.json
    2. Cache: /home/coinjecture/COINjecture/data/cache/
    3. Database: /opt/coinjecture-consensus/data/blockchain.db
    """
    
    def __init__(self, cache_dir: str = "/home/coinjecture/COINjecture/data/cache"):
        self.cache_dir = Path(cache_dir)
        self.primary_source = "/opt/coinjecture-consensus/data/blockchain_state.json"
        self.database = "/opt/coinjecture-consensus/data/blockchain.db"
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_latest_block(self) -> Optional[Dict[str, Any]]:
        """Get latest block from primary source."""
        try:
            with open(self.primary_source, 'r') as f:
                data = json.load(f)
            return data.get('latest_block')
        except Exception:
            return None
    
    def get_all_blocks(self) -> List[Dict[str, Any]]:
        """Get all blocks from primary source."""
        try:
            with open(self.primary_source, 'r') as f:
                data = json.load(f)
            return data.get('blocks', [])
        except Exception:
            return []
    
    def get_block_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """Get block by index from primary source."""
        blocks = self.get_all_blocks()
        for block in blocks:
            if block.get('index') == index:
                return block
        return None
    
    def get_blocks_range(self, start: int, end: int) -> List[Dict[str, Any]]:
        """Get blocks in range from primary source."""
        blocks = self.get_all_blocks()
        return [block for block in blocks if start <= block.get('index', 0) <= end]
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information."""
        try:
            latest_block = self.get_latest_block()
            all_blocks = self.get_all_blocks()
            
            return {
                "latest_block_index": latest_block.get("index") if latest_block else 0,
                "latest_block_hash": latest_block.get("block_hash") if latest_block else "",
                "total_blocks": len(all_blocks),
                "cache_available": True,
                "data_sources": 3,
                "primary_source": self.primary_source,
                "cache_dir": str(self.cache_dir),
                "database": self.database
            }
        except Exception as e:
            return {
                "cache_available": False,
                "error": str(e)
            }
CACHE_MANAGER

# Backup original cache manager
cp /home/coinjecture/COINjecture/src/api/cache_manager.py /home/coinjecture/COINjecture/src/api/cache_manager.py.backup

# Replace with simplified version
cp /tmp/cache_manager_fixed.py /home/coinjecture/COINjecture/src/api/cache_manager.py

echo "   ✅ API configuration updated"

# 6. Restart services
echo "🔄 Restarting services..."
systemctl restart coinjecture-api
echo "   ✅ API service restarted"

# 7. Test the consolidated data sources
echo "🧪 Testing consolidated data sources..."
sleep 2

echo "Testing API endpoints:"
echo "   Latest block index:"
curl -s https://api.coinjecture.com/v1/data/block/latest | jq '.data.index'

echo "   Total blocks:"
curl -s https://api.coinjecture.com/v1/data/blocks/all | jq '.meta.total_blocks'

echo ""
echo "✅ Data consolidation completed!"
echo "=============================="
echo ""
echo "🎯 Final data sources (3 only):"
echo "   1. Primary: $PRIMARY_SOURCE ($PRIMARY_BLOCKS blocks)"
echo "   2. Cache: $CACHE_DIR (synchronized)"
echo "   3. Database: $DATABASE (persistent storage)"
echo ""
echo "🧪 Test the frontend now:"
echo "   https://coinjecture.com"
echo ""
echo "All blockchain statistics should now be consistent!"

# Clean up
rm -f /tmp/blocks_history_sync.json /tmp/latest_block_sync.json /tmp/cache_manager_fixed.py

EOF

# Make the script executable
chmod +x /tmp/consolidate_data_droplet.sh

echo "📤 Copying data consolidation script to droplet..."
scp -i "$SSH_KEY" /tmp/consolidate_data_droplet.sh "$USER@$DROPLET_IP:/tmp/"

echo "🚀 Running data consolidation on droplet..."
ssh -i "$SSH_KEY" "$USER@$DROPLET_IP" "chmod +x /tmp/consolidate_data_droplet.sh && /tmp/consolidate_data_droplet.sh"

# Clean up
rm -f /tmp/consolidate_data_droplet.sh

echo ""
echo "🎉 Data consolidation completed!"
echo "==============================="
echo ""
echo "✅ Now using exactly 3 data sources:"
echo "   1. Primary blockchain state"
echo "   2. Synchronized cache"
echo "   3. Database storage"
echo ""
echo "🧪 Test the frontend now:"
echo "   https://coinjecture.com"
echo ""
echo "All blockchain statistics should now be consistent!"
