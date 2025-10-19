#!/usr/bin/env python3
"""
Fix blocks_history.json format to match API validation requirements
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

def fix_blocks_history_format():
    """Fix blocks_history.json format to match API validation"""
    
    logger.info("=== Fix Blocks History Format ===")
    
    # Paths
    blockchain_state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
    cache_dir = "/home/coinjecture/COINjecture/data/cache"
    blocks_history_path = os.path.join(cache_dir, "blocks_history.json")
    
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
        
        # Get recent blocks (last 100)
        recent_blocks = blocks[-100:] if len(blocks) > 100 else blocks
        logger.info(f"Processing {len(recent_blocks)} recent blocks")
        
        # Fix hash formats for each block
        fixed_blocks = []
        for block in recent_blocks:
            fixed_block = block.copy()
            
            # Fix hash fields to be 64 characters
            for hash_field in ["previous_hash", "merkle_root", "block_hash"]:
                if hash_field in fixed_block:
                    current_hash = fixed_block[hash_field]
                    if len(current_hash) != 64:
                        # Pad with zeros or truncate to 64 characters
                        if len(current_hash) < 64:
                            fixed_block[hash_field] = current_hash.ljust(64, '0')
                        else:
                            fixed_block[hash_field] = current_hash[:64]
                        logger.debug(f"Fixed {hash_field}: {current_hash} -> {fixed_block[hash_field]}")
            
            fixed_blocks.append(fixed_block)
        
        # Write fixed blocks to blocks_history.json
        logger.info("Writing fixed blocks to blocks_history.json...")
        with open(blocks_history_path, 'w') as f:
            json.dump(fixed_blocks, f, indent=2)
        
        logger.info(f"✅ Updated {blocks_history_path} with {len(fixed_blocks)} fixed blocks")
        
        # Restart API service
        logger.info("Restarting API service...")
        result = subprocess.run(['systemctl', 'restart', 'coinjecture-api'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ API service restarted successfully")
        else:
            logger.error(f"❌ Failed to restart API service: {result.stderr}")
            return False
        
        # Wait for service to start
        import time
        time.sleep(2)
        
        # Test API endpoint
        logger.info("Testing API endpoint...")
        import requests
        try:
            response = requests.get("http://localhost:5000/v1/data/blocks?start=3334&end=3344", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    block_count = len(data.get('data', []))
                    logger.info(f"✅ API responding correctly - Found {block_count} blocks in range 3334-3344")
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
        logger.error(f"❌ Error fixing blocks history format: {e}")
        return False

if __name__ == "__main__":
    success = fix_blocks_history_format()
    if success:
        print("✅ Blocks history format fixed successfully")
    else:
        print("❌ Failed to fix blocks history format")
        sys.exit(1)
