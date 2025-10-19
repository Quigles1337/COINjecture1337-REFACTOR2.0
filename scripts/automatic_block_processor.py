#!/usr/bin/env python3
"""
Automatic Block Processor
This script continuously processes new peer-mined blocks and adds them to the blockchain.
"""

import os
import sys
import json
import time
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/coinjecture-consensus/logs/automatic_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('automatic-block-processor')

class AutomaticBlockProcessor:
    """Automatically processes new peer-mined blocks."""
    
    def __init__(self):
        self.db_path = "/home/coinjecture/COINjecture/data/faucet_ingest.db"
        self.state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
        self.cache_path = "/home/coinjecture/COINjecture/data/cache/latest_block.json"
        self.processed_events = set()
        self.load_processed_events()
    
    def load_processed_events(self):
        """Load previously processed events to avoid duplicates."""
        try:
            if os.path.exists(self.state_path):
                with open(self.state_path, 'r') as f:
                    state = json.load(f)
                    # Get all processed event IDs from blocks
                    for block in state.get('blocks', []):
                        if 'event_id' in block:
                            self.processed_events.add(block['event_id'])
                logger.info(f"📊 Loaded {len(self.processed_events)} previously processed events")
        except Exception as e:
            logger.error(f"❌ Error loading processed events: {e}")
    
    def get_current_blockchain_state(self):
        """Get current blockchain state."""
        if os.path.exists(self.state_path):
            with open(self.state_path, 'r') as f:
                return json.load(f)
        return {"blocks": [], "latest_block": None}
    
    def get_new_block_events(self):
        """Get new block events from the database."""
        if not os.path.exists(self.db_path):
            logger.error(f"❌ Database not found: {self.db_path}")
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get recent block events that haven't been processed
            cursor.execute("""
                SELECT event_id, block_hash, miner_address, work_score, ts, cid, capacity
                FROM block_events 
                WHERE event_id NOT IN ({})
                ORDER BY ts ASC 
                LIMIT 20
            """.format(','.join('?' * len(self.processed_events))), list(self.processed_events))
            
            events = cursor.fetchall()
            conn.close()
            
            logger.info(f"📊 Found {len(events)} new block events")
            return events
            
        except Exception as e:
            logger.error(f"❌ Error reading database: {e}")
            return []
    
    def create_block_from_event(self, event, current_blocks):
        """Create a block from an event with correct indexing."""
        event_id, block_hash, miner_address, work_score, ts, cid, capacity = event
        
        # Get next index
        if current_blocks:
            next_index = max(block["index"] for block in current_blocks) + 1
            previous_hash = current_blocks[-1]["block_hash"]
        else:
            next_index = 0
            previous_hash = "0" * 64
        
        # Create block
        block = {
            "index": next_index,
            "timestamp": ts,
            "previous_hash": previous_hash,
            "merkle_root": "0" * 64,
            "mining_capacity": capacity,
            "cumulative_work_score": work_score,
            "block_hash": block_hash,
            "offchain_cid": cid,
            "miner_address": miner_address,
            "event_id": event_id
        }
        
        return block
    
    def update_blockchain_state(self, new_blocks):
        """Update the blockchain state with new blocks."""
        try:
            # Get current state
            state = self.get_current_blockchain_state()
            current_blocks = state.get("blocks", [])
            
            # Add new blocks
            for block in new_blocks:
                current_blocks.append(block)
                self.processed_events.add(block["event_id"])
            
            # Update state
            state["blocks"] = current_blocks
            if new_blocks:
                state["latest_block"] = new_blocks[-1]
            state["last_updated"] = time.time()
            state["consensus_version"] = "3.9.0-alpha.2-automatic"
            state["processed_events_count"] = len(self.processed_events)
            
            # Write updated state
            os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
            with open(self.state_path, 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.info(f"📝 Updated blockchain state: {len(current_blocks)} total blocks")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating blockchain state: {e}")
            return False
    
    def update_api_cache(self, latest_block):
        """Update the API cache with the latest block."""
        try:
            with open(self.cache_path, 'w') as f:
                json.dump(latest_block, f, indent=2)
            logger.info(f"🔄 Updated API cache with block {latest_block['index']}")
            return True
        except Exception as e:
            logger.error(f"❌ Error updating API cache: {e}")
            return False
    
    def process_new_blocks(self):
        """Process new blocks and add them to the blockchain."""
        logger.info("🔍 Checking for new blocks...")
        
        # Get new events
        events = self.get_new_block_events()
        if not events:
            logger.info("📊 No new blocks to process")
            return True
        
        # Get current state
        state = self.get_current_blockchain_state()
        current_blocks = state.get("blocks", [])
        
        # Process new blocks
        new_blocks = []
        for event in events:
            event_id, block_hash, miner_address, work_score, ts, cid, capacity = event
            
            # Skip if already processed
            if event_id in self.processed_events:
                continue
            
            # Create block
            block = self.create_block_from_event(event, current_blocks)
            new_blocks.append(block)
            current_blocks.append(block)
            
            logger.info(f"✅ Processed block #{block['index']} by {miner_address}")
            logger.info(f"   Hash: {block_hash[:16]}...")
            logger.info(f"   Work score: {work_score}")
        
        if new_blocks:
            # Update blockchain state
            if self.update_blockchain_state(new_blocks):
                # Update API cache
                self.update_api_cache(new_blocks[-1])
                logger.info(f"🎉 Successfully processed {len(new_blocks)} new blocks!")
                return True
            else:
                logger.error("❌ Failed to update blockchain state")
                return False
        else:
            logger.info("📊 No new blocks to process")
            return True
    
    def run_continuous(self):
        """Run the processor continuously."""
        logger.info("🚀 Starting automatic block processor...")
        logger.info("🔄 Processing blocks every 30 seconds...")
        
        while True:
            try:
                self.process_new_blocks()
                time.sleep(30)  # Process every 30 seconds
            except KeyboardInterrupt:
                logger.info("🛑 Stopping automatic processor...")
                break
            except Exception as e:
                logger.error(f"❌ Error in continuous processing: {e}")
                time.sleep(10)  # Wait before retrying

def main():
    """Main function."""
    logger.info("🔧 Starting automatic block processor...")
    
    # Check if we're on the droplet
    if not os.path.exists("/opt/coinjecture-consensus"):
        logger.error("❌ This script must be run on the droplet")
        return 1
    
    # Create processor
    processor = AutomaticBlockProcessor()
    
    # Run continuously
    try:
        processor.run_continuous()
    except Exception as e:
        logger.error(f"❌ Processor failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
