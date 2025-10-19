#!/usr/bin/env python3
"""
Force API Cache Clear
Clears API service internal cache to show updated blockchain data
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
        logging.FileHandler('/opt/coinjecture-consensus/logs/force_api_cache_clear.log'),
        logging.StreamHandler()
    ]
)

class APICacheClearer:
    def __init__(self):
        self.api_cache_path = Path('/home/coinjecture/COINjecture/data/cache')
        self.blockchain_state_path = Path('/opt/coinjecture-consensus/data/blockchain_state.json')
        
    def get_latest_blockchain_data(self):
        """Get latest blockchain data"""
        try:
            with open(self.blockchain_state_path, 'r') as f:
                blockchain_data = json.load(f)
            
            blocks = blockchain_data.get('blocks', [])
            if not blocks:
                logging.error("No blocks found in blockchain state")
                return None
            
            latest_block = blocks[-1]
            logging.info(f"Latest blockchain block: {latest_block['index']}")
            return latest_block
            
        except Exception as e:
            logging.error(f"Error reading blockchain state: {e}")
            return None
    
    def update_cache_files(self, latest_block):
        """Update cache files with latest block data"""
        try:
            # Ensure cache directory exists
            self.api_cache_path.mkdir(parents=True, exist_ok=True)
            
            # Update latest_block.json
            latest_block_path = self.api_cache_path / 'latest_block.json'
            with open(latest_block_path, 'w') as f:
                json.dump(latest_block, f, indent=2)
            
            logging.info(f"Updated latest_block.json with block {latest_block['index']}")
            
            # Update blocks_history.json with last 100 blocks
            with open(self.blockchain_state_path, 'r') as f:
                blockchain_data = json.load(f)
            
            blocks = blockchain_data.get('blocks', [])
            recent_blocks = blocks[-100:] if len(blocks) > 100 else blocks
            
            history_data = {"blocks": recent_blocks}
            blocks_history_path = self.api_cache_path / 'blocks_history.json'
            with open(blocks_history_path, 'w') as f:
                json.dump(history_data, f, indent=2)
            
            logging.info(f"Updated blocks_history.json with {len(recent_blocks)} blocks")
            return True
            
        except Exception as e:
            logging.error(f"Error updating cache files: {e}")
            return False
    
    def force_restart_api_service(self):
        """Force restart API service to clear internal cache"""
        try:
            logging.info("Stopping API service...")
            subprocess.run(['systemctl', 'stop', 'coinjecture-api'], check=True)
            
            # Wait for service to fully stop
            time.sleep(3)
            
            # Clear any temporary files or cache
            temp_cache_path = Path('/home/coinjecture/COINjecture/data/temp')
            if temp_cache_path.exists():
                import shutil
                shutil.rmtree(temp_cache_path)
                logging.info("Cleared temporary cache files")
            
            logging.info("Starting API service...")
            subprocess.run(['systemctl', 'start', 'coinjecture-api'], check=True)
            
            # Wait for service to start
            time.sleep(5)
            
            # Check service status
            result = subprocess.run(['systemctl', 'is-active', 'coinjecture-api'], 
                                  capture_output=True, text=True)
            
            if result.stdout.strip() == 'active':
                logging.info("✅ API service is running")
                return True
            else:
                logging.error("❌ API service failed to start")
                return False
                
        except Exception as e:
            logging.error(f"Error restarting API service: {e}")
            return False
    
    def test_api_endpoint(self):
        """Test API endpoint to verify cache clear"""
        try:
            import requests
            
            # Test the API endpoint
            response = requests.get('http://localhost:5000/v1/data/block/latest', timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                block_data = data.get('data', {})
                block_index = block_data.get('index', 'unknown')
                logging.info(f"API now returns block: {block_index}")
                return block_index
            else:
                logging.error(f"API endpoint failed: {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"Error testing API endpoint: {e}")
            return None
    
    def force_clear_api_cache(self):
        """Force clear API cache and verify"""
        logging.info("=== Force API Cache Clear ===")
        
        # Get latest blockchain data
        latest_block = self.get_latest_blockchain_data()
        if not latest_block:
            logging.error("Failed to get latest blockchain data")
            return False
        
        # Update cache files
        if not self.update_cache_files(latest_block):
            logging.error("Failed to update cache files")
            return False
        
        # Force restart API service
        if not self.force_restart_api_service():
            logging.error("Failed to restart API service")
            return False
        
        # Test API endpoint
        api_block = self.test_api_endpoint()
        if not api_block:
            logging.error("Failed to test API endpoint")
            return False
        
        # Verify the API is now serving updated data
        if str(api_block) == str(latest_block['index']):
            logging.info(f"✅ API cache cleared successfully! API now shows block {api_block}")
            return True
        else:
            logging.warning(f"⚠️ API shows block {api_block}, expected {latest_block['index']}")
            return False

def main():
    """Main function"""
    clearer = APICacheClearer()
    
    try:
        success = clearer.force_clear_api_cache()
        if success:
            print("API cache cleared successfully")
            sys.exit(0)
        else:
            print("API cache clear failed")
            sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
