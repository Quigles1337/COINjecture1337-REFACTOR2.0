#!/usr/bin/env python3
"""
Update API Cache
This script updates the API cache with the correct blockchain state.
"""

import json
import os

def update_api_cache():
    """Update the API cache with the correct blockchain state."""
    
    # Read the updated blockchain state
    blockchain_state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
    cache_path = "/home/coinjecture/COINjecture/data/cache/latest_block.json"
    
    if not os.path.exists(blockchain_state_path):
        print(f"❌ Blockchain state not found: {blockchain_state_path}")
        return False
    
    try:
        with open(blockchain_state_path, 'r') as f:
            blockchain_state = json.load(f)
        
        # Get the latest block
        latest_block = blockchain_state['latest_block']
        
        # Update the cache file
        with open(cache_path, 'w') as f:
            json.dump(latest_block, f, indent=2)
        
        print(f"✅ Updated cache with block {latest_block['index']}")
        print(f"   Hash: {latest_block['block_hash']}")
        print(f"   Work score: {latest_block['cumulative_work_score']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating cache: {e}")
        return False

def main():
    """Main function."""
    print("🔄 Updating API cache...")
    
    if update_api_cache():
        print("✅ API cache updated successfully!")
        return 0
    else:
        print("❌ Failed to update API cache")
        return 1

if __name__ == "__main__":
    exit(main())
