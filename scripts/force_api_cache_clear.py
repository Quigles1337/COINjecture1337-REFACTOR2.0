#!/usr/bin/env python3
"""
Force clear API cache and restart service
"""

import os
import sys
import json
import subprocess
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def force_api_cache_clear():
    """Force clear API cache and restart service"""
    
    logger.info("=== Force API Cache Clear ===")
    
    # Paths
    blockchain_state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
    cache_dir = "/home/coinjecture/COINjecture/data/cache"
    
    try:
        # Read blockchain state
        logger.info("Reading blockchain state...")
        with open(blockchain_state_path, 'r') as f:
            blockchain_data = json.load(f)
        
        blocks = blockchain_data.get('blocks', [])
        logger.info(f"Found {len(blocks)} blocks in blockchain state")
        
        if not blocks:
            logger.error("No blocks found in blockchain state")
            return False
        
        # Get latest block
        latest_block = blocks[-1]
        logger.info(f"Latest block: {latest_block.get('index', 'unknown')}")
        
        # Update cache files
        logger.info("Updating cache files...")
        
        # Update latest_block.json
        latest_block_path = os.path.join(cache_dir, "latest_block.json")
        with open(latest_block_path, 'w') as f:
            json.dump(latest_block, f, indent=2)
        logger.info(f"Updated {latest_block_path}")
        
        # Update blocks_history.json with recent blocks (as direct array, not wrapped)
        recent_blocks = blocks[-50:] if len(blocks) > 50 else blocks
        blocks_history_path = os.path.join(cache_dir, "blocks_history.json")
        with open(blocks_history_path, 'w') as f:
            json.dump(recent_blocks, f, indent=2)
        logger.info(f"Updated {blocks_history_path} with {len(recent_blocks)} blocks")
        
        # Restart API service
        logger.info("Restarting API service...")
        result = subprocess.run(['systemctl', 'restart', 'coinjecture-api'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ API service restarted successfully")
        else:
            logger.error(f"❌ Failed to restart API service: {result.stderr}")
            return False
        
        # Wait a moment for service to start
        import time
        time.sleep(2)
        
        # Test API endpoint
        logger.info("Testing API endpoint...")
        import requests
        try:
            response = requests.get("http://localhost:5000/v1/data/block/latest", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    logger.info(f"✅ API responding correctly - Latest block: {data['data'].get('index', 'unknown')}")
                    return True
                else:
                    logger.error(f"❌ API returned error: {data}")
                    return False
            else:
                logger.error(f"❌ API returned status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Error testing API: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error in force API cache clear: {e}")
        return False

if __name__ == "__main__":
    success = force_api_cache_clear()
    if success:
        print("✅ API cache cleared and service restarted successfully")
    else:
        print("❌ Failed to clear API cache")
        sys.exit(1)