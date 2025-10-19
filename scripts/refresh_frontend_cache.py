#!/usr/bin/env python3
"""
Refresh Frontend Cache
Updates frontend cache to show current blockchain state
"""

import os
import sys
import json
import requests
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/coinjecture-consensus/logs/frontend_cache_refresh.log'),
        logging.StreamHandler()
    ]
)

class FrontendCacheRefresher:
    def __init__(self):
        self.base_path = Path('/opt/coinjecture-consensus')
        self.blockchain_state_path = self.base_path / 'data' / 'blockchain_state.json'
        self.api_cache_path = Path('/home/coinjecture/COINjecture/data/cache')
        self.api_url = 'http://localhost:5000'
        
    def get_latest_blockchain_data(self):
        """Get latest blockchain data from blockchain_state.json"""
        try:
            with open(self.blockchain_state_path, 'r') as f:
                blockchain_data = json.load(f)
            
            blocks = blockchain_data.get('blocks', [])
            if not blocks:
                logging.error("No blocks found in blockchain state")
                return None
            
            latest_block = blocks[-1]
            logging.info(f"Latest block from blockchain state: {latest_block['index']}")
            return latest_block
            
        except Exception as e:
            logging.error(f"Error reading blockchain state: {e}")
            return None
    
    def update_api_cache(self, latest_block):
        """Update API cache with latest block data"""
        try:
            # Ensure cache directory exists
            self.api_cache_path.mkdir(parents=True, exist_ok=True)
            
            # Update latest_block.json
            latest_block_path = self.api_cache_path / 'latest_block.json'
            with open(latest_block_path, 'w') as f:
                json.dump(latest_block, f, indent=2)
            
            logging.info(f"Updated latest_block.json with block {latest_block['index']}")
            
            # Update blocks_history.json
            blocks_history_path = self.api_cache_path / 'blocks_history.json'
            
            # Read existing history or create new
            if blocks_history_path.exists():
                with open(blocks_history_path, 'r') as f:
                    history_data = json.load(f)
            else:
                history_data = {"blocks": []}
            
            # Add latest block to history (keep last 100 blocks)
            history_data["blocks"].append(latest_block)
            if len(history_data["blocks"]) > 100:
                history_data["blocks"] = history_data["blocks"][-100:]
            
            with open(blocks_history_path, 'w') as f:
                json.dump(history_data, f, indent=2)
            
            logging.info(f"Updated blocks_history.json with block {latest_block['index']}")
            return True
            
        except Exception as e:
            logging.error(f"Error updating API cache: {e}")
            return False
    
    def restart_api_service(self):
        """Restart API service to clear in-memory cache"""
        try:
            import subprocess
            
            # Restart faucet service
            subprocess.run(['systemctl', 'restart', 'coinjecture-faucet'], check=True)
            logging.info("Restarted coinjecture-faucet service")
            
            # Wait for service to start
            import time
            time.sleep(5)
            
            # Check if service is running
            result = subprocess.run(['systemctl', 'is-active', 'coinjecture-faucet'], 
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
    
    def test_api_endpoints(self):
        """Test API endpoints to verify cache refresh"""
        try:
            # Test latest block endpoint
            response = requests.get(f"{self.api_url}/api/latest-block", timeout=10)
            if response.status_code == 200:
                data = response.json()
                logging.info(f"API latest block: {data.get('index', 'unknown')}")
                return True
            else:
                logging.error(f"API endpoint failed: {response.status_code}")
                return False
                
        except Exception as e:
            logging.error(f"Error testing API endpoints: {e}")
            return False
    
    def refresh_frontend_cache(self):
        """Refresh frontend cache with latest blockchain data"""
        logging.info("=== Refreshing Frontend Cache ===")
        
        # Get latest blockchain data
        latest_block = self.get_latest_blockchain_data()
        if not latest_block:
            logging.error("Failed to get latest blockchain data")
            return False
        
        # Update API cache
        if not self.update_api_cache(latest_block):
            logging.error("Failed to update API cache")
            return False
        
        # Restart API service
        if not self.restart_api_service():
            logging.error("Failed to restart API service")
            return False
        
        # Test API endpoints
        if not self.test_api_endpoints():
            logging.error("Failed to test API endpoints")
            return False
        
        logging.info("=== Frontend Cache Refresh Completed Successfully ===")
        return True

def main():
    """Main function"""
    refresher = FrontendCacheRefresher()
    
    try:
        success = refresher.refresh_frontend_cache()
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
