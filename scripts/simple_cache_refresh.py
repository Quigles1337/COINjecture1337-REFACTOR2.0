#!/usr/bin/env python3
"""
Simple Frontend Cache Refresh
Updates frontend cache to show current blockchain state
"""

import os
import sys
import json
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/coinjecture-consensus/logs/simple_cache_refresh.log'),
        logging.StreamHandler()
    ]
)

def refresh_frontend_cache():
    """Refresh frontend cache with latest blockchain data"""
    logging.info("=== Simple Frontend Cache Refresh ===")
    
    try:
        # Read latest block from blockchain state
        with open('/opt/coinjecture-consensus/data/blockchain_state.json', 'r') as f:
            blockchain_data = json.load(f)
        
        blocks = blockchain_data.get('blocks', [])
        if not blocks:
            logging.error("No blocks found in blockchain state")
            return False
        
        latest_block = blocks[-1]
        logging.info(f"Latest block: {latest_block['index']}")
        
        # Update API cache
        api_cache_path = Path('/home/coinjecture/COINjecture/data/cache')
        api_cache_path.mkdir(parents=True, exist_ok=True)
        
        # Update latest_block.json
        latest_block_path = api_cache_path / 'latest_block.json'
        with open(latest_block_path, 'w') as f:
            json.dump(latest_block, f, indent=2)
        
        logging.info(f"Updated latest_block.json with block {latest_block['index']}")
        
        # Update blocks_history.json with last 50 blocks
        blocks_history_path = api_cache_path / 'blocks_history.json'
        recent_blocks = blocks[-50:] if len(blocks) > 50 else blocks
        
        history_data = {"blocks": recent_blocks}
        with open(blocks_history_path, 'w') as f:
            json.dump(history_data, f, indent=2)
        
        logging.info(f"Updated blocks_history.json with {len(recent_blocks)} blocks")
        
        # Restart API service
        logging.info("Restarting API service...")
        subprocess.run(['systemctl', 'restart', 'coinjecture-faucet'], check=True)
        
        # Wait for service to start
        import time
        time.sleep(5)
        
        # Check service status
        result = subprocess.run(['systemctl', 'is-active', 'coinjecture-faucet'], 
                              capture_output=True, text=True)
        
        if result.stdout.strip() == 'active':
            logging.info("✅ API service is running")
        else:
            logging.error("❌ API service failed to start")
            return False
        
        logging.info("=== Frontend Cache Refresh Completed Successfully ===")
        return True
        
    except Exception as e:
        logging.error(f"Error refreshing frontend cache: {e}")
        return False

def main():
    """Main function"""
    try:
        success = refresh_frontend_cache()
        if success:
            print("Frontend cache refreshed successfully")
            sys.exit(0)
        else:
            print("Frontend cache refresh failed")
            sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
