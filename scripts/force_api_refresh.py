#!/usr/bin/env python3
"""
Force API Refresh
Forces the API service to refresh its internal cache by triggering a cache refresh
"""

import os
import sys
import json
import subprocess
import time
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/coinjecture-consensus/logs/force_api_refresh.log'),
        logging.StreamHandler()
    ]
)

class APIForcer:
    def __init__(self):
        self.blockchain_state_path = Path('/opt/coinjecture-consensus/data/blockchain_state.json')
        self.api_cache_path = Path('/home/coinjecture/COINjecture/data/cache')
        
    def force_api_refresh(self):
        """Force API to refresh its cache"""
        logging.info("=== Force API Refresh ===")
        
        try:
            # Get current blockchain state
            with open(self.blockchain_state_path, 'r') as f:
                blockchain_data = json.load(f)
            
            latest_block = blockchain_data.get('latest_block', {})
            logging.info(f"Blockchain state latest block: {latest_block.get('index', 'unknown')}")
            
            # Update cache files to match blockchain state
            self.api_cache_path.mkdir(parents=True, exist_ok=True)
            
            # Update latest_block.json
            latest_block_path = self.api_cache_path / 'latest_block.json'
            with open(latest_block_path, 'w') as f:
                json.dump(latest_block, f, indent=2)
            
            logging.info(f"Updated latest_block.json with block {latest_block.get('index', 'unknown')}")
            
            # Update blocks_history.json
            blocks = blockchain_data.get('blocks', [])
            recent_blocks = blocks[-100:] if len(blocks) > 100 else blocks
            
            history_data = {"blocks": recent_blocks}
            blocks_history_path = self.api_cache_path / 'blocks_history.json'
            with open(blocks_history_path, 'w') as f:
                json.dump(history_data, f, indent=2)
            
            logging.info(f"Updated blocks_history.json with {len(recent_blocks)} blocks")
            
            # Force restart API service to clear internal cache
            logging.info("Restarting API service to clear internal cache...")
            subprocess.run(['systemctl', 'restart', 'coinjecture-api'], check=True)
            
            # Wait for service to start
            time.sleep(5)
            
            # Check service status
            result = subprocess.run(['systemctl', 'is-active', 'coinjecture-api'], 
                                  capture_output=True, text=True)
            
            if result.stdout.strip() != 'active':
                logging.error("API service failed to start")
                return False
            
            logging.info("✅ API service restarted successfully")
            
            # Test API endpoint
            import requests
            response = requests.get('http://localhost:5000/v1/data/block/latest', timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                block_data = data.get('data', {})
                api_block_index = block_data.get('index', 'unknown')
                logging.info(f"API now returns block: {api_block_index}")
                
                # Check if it matches blockchain state
                blockchain_block_index = latest_block.get('index', 'unknown')
                if str(api_block_index) == str(blockchain_block_index):
                    logging.info(f"✅ API cache refreshed successfully! API now shows block {api_block_index}")
                    return True
                else:
                    logging.warning(f"⚠️ API shows block {api_block_index}, blockchain state shows {blockchain_block_index}")
                    return False
            else:
                logging.error(f"API endpoint failed: {response.status_code}")
                return False
                
        except Exception as e:
            logging.error(f"Error forcing API refresh: {e}")
            return False

def main():
    """Main function"""
    forcer = APIForcer()
    
    try:
        success = forcer.force_api_refresh()
        if success:
            print("API refresh successful")
            sys.exit(0)
        else:
            print("API refresh failed")
            sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
