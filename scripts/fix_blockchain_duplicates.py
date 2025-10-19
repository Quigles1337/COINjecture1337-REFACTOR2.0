#!/usr/bin/env python3
"""
Fix Blockchain Duplicates
This script fixes the duplicate block index issue and properly sequences blocks.
"""

import os
import sys
import json
import time
import sqlite3
from pathlib import Path

def get_current_blockchain_state():
    """Get current blockchain state."""
    state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
    
    if os.path.exists(state_path):
        with open(state_path, 'r') as f:
            return json.load(f)
    else:
        return {"blocks": [], "latest_block": None}

def fix_blockchain_duplicates():
    """Fix the duplicate block index issue."""
    print("🔧 Fixing blockchain duplicate index issue...")
    
    # Get current state
    state = get_current_blockchain_state()
    
    if not state.get("blocks"):
        print("📊 No blocks found in state")
        return False
    
    # Find the actual latest block (highest index)
    max_index = max(block["index"] for block in state["blocks"])
    print(f"📊 Current max block index: {max_index}")
    
    # Count duplicates at max index
    duplicates = [block for block in state["blocks"] if block["index"] == max_index]
    print(f"📊 Found {len(duplicates)} blocks with index {max_index}")
    
    if len(duplicates) <= 1:
        print("✅ No duplicate index issue found")
        return True
    
    # Remove all duplicate blocks except the first one
    print(f"🗑️  Removing {len(duplicates) - 1} duplicate blocks...")
    
    # Keep only the first block at max index
    first_duplicate = duplicates[0]
    other_duplicates = duplicates[1:]
    
    # Remove other duplicates
    for duplicate in other_duplicates:
        state["blocks"].remove(duplicate)
    
    # Update latest block
    state["latest_block"] = first_duplicate
    
    # Write fixed state
    state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
    with open(state_path, 'w') as f:
        json.dump(state, f, indent=2)
    
    print(f"✅ Fixed blockchain state: {len(state['blocks'])} blocks, latest: {state['latest_block']['index']}")
    return True

def process_peer_blocks_correctly():
    """Process peer blocks with correct sequential indexing."""
    print("🚀 Processing peer blocks with correct indexing...")
    
    # Get current state
    state = get_current_blockchain_state()
    current_blocks = state.get("blocks", [])
    
    # Find the actual latest index
    if current_blocks:
        latest_index = max(block["index"] for block in current_blocks)
    else:
        latest_index = -1
    
    print(f"📊 Current latest block index: {latest_index}")
    
    # Get pending events from database
    db_path = "/home/coinjecture/COINjecture/data/faucet_ingest.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get recent block events
        cursor.execute("""
            SELECT event_id, block_hash, miner_address, work_score, ts, cid, capacity
            FROM block_events 
            ORDER BY ts ASC 
            LIMIT 50
        """)
        
        events = cursor.fetchall()
        conn.close()
        
        print(f"📊 Found {len(events)} block events")
        
        # Get existing block hashes to avoid duplicates
        existing_hashes = {block["block_hash"] for block in current_blocks}
        
        # Process events with correct sequential indexing
        new_blocks = []
        next_index = latest_index + 1
        
        for event in events:
            event_id, block_hash, miner_address, work_score, ts, cid, capacity = event
            
            # Skip if already processed
            if block_hash in existing_hashes:
                continue
            
            # Get previous hash
            if current_blocks:
                previous_hash = current_blocks[-1]["block_hash"]
            else:
                previous_hash = "0" * 64
            
            # Create block with correct index
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
            
            new_blocks.append(block)
            current_blocks.append(block)
            existing_hashes.add(block_hash)
            next_index += 1
            
            print(f"✅ Processed block #{block['index']} by {miner_address}")
        
        if new_blocks:
            # Update state
            state["blocks"] = current_blocks
            state["latest_block"] = new_blocks[-1]
            state["last_updated"] = time.time()
            state["consensus_version"] = "3.9.0-alpha.2-fixed"
            
            # Write updated state
            state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
            with open(state_path, 'w') as f:
                json.dump(state, f, indent=2)
            
            print(f"📝 Updated blockchain state: {len(state['blocks'])} total blocks")
            print(f"🎉 Successfully processed {len(new_blocks)} new blocks with correct indexing!")
        else:
            print("📊 No new blocks to process")
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing blocks: {e}")
        return False

def main():
    """Main function."""
    print("🔧 Fixing blockchain duplicate index issue...")
    
    # Check if we're on the droplet
    if not os.path.exists("/opt/coinjecture-consensus"):
        print("❌ This script must be run on the droplet")
        return 1
    
    # First, fix the duplicates
    if not fix_blockchain_duplicates():
        print("❌ Failed to fix duplicates")
        return 1
    
    # Then process new blocks correctly
    if not process_peer_blocks_correctly():
        print("❌ Failed to process new blocks")
        return 1
    
    print("✅ Blockchain duplicate issue fixed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
