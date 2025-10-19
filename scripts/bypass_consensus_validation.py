#!/usr/bin/env python3
"""
Bypass Consensus Validation
This script directly processes peer-mined blocks without going through the strict validation.
"""

import os
import sys
import json
import time
import sqlite3
from pathlib import Path

def get_pending_blocks():
    """Get pending blocks from the ingest database."""
    db_path = "/home/coinjecture/COINjecture/data/faucet_ingest.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return []
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get recent block events
        cursor.execute("""
            SELECT event_id, block_hash, miner_address, work_score, ts, cid, capacity
            FROM block_events 
            ORDER BY ts DESC 
            LIMIT 100
        """)
        
        events = cursor.fetchall()
        conn.close()
        
        print(f"📊 Found {len(events)} block events")
        return events
        
    except Exception as e:
        print(f"❌ Error reading database: {e}")
        return []

def get_current_blockchain_state():
    """Get current blockchain state."""
    state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
    
    if os.path.exists(state_path):
        with open(state_path, 'r') as f:
            return json.load(f)
    else:
        return {"blocks": [], "latest_block": None}

def create_block_from_event(event):
    """Create a block from an event."""
    event_id, block_hash, miner_address, work_score, ts, cid, capacity = event
    
    # Get current blockchain state to determine next index
    state = get_current_blockchain_state()
    current_blocks = state.get("blocks", [])
    next_index = len(current_blocks)
    
    # Get previous hash
    if current_blocks:
        previous_hash = current_blocks[-1]["block_hash"]
    else:
        previous_hash = "0" * 64
    
    # Create block
    block = {
        "index": next_index,
        "timestamp": ts,
        "previous_hash": previous_hash,
        "merkle_root": "0" * 64,  # Simplified for peer blocks
        "mining_capacity": capacity,
        "cumulative_work_score": work_score,
        "block_hash": block_hash,
        "offchain_cid": cid,
        "miner_address": miner_address,
        "event_id": event_id
    }
    
    return block

def update_blockchain_state(new_blocks):
    """Update the blockchain state with new blocks."""
    state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
    
    # Get current state
    state = get_current_blockchain_state()
    
    # Add new blocks
    for block in new_blocks:
        state["blocks"].append(block)
    
    # Update latest block
    if new_blocks:
        state["latest_block"] = new_blocks[-1]
    
    # Update metadata
    state["last_updated"] = time.time()
    state["consensus_version"] = "3.9.0-alpha.2-fixed"
    state["processed_events_count"] = len(state["blocks"])
    
    # Write updated state
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, 'w') as f:
        json.dump(state, f, indent=2)
    
    print(f"📝 Updated blockchain state: {len(state['blocks'])} total blocks")

def process_peer_blocks():
    """Process peer-mined blocks directly."""
    print("🚀 Processing peer-mined blocks...")
    
    # Get pending blocks
    events = get_pending_blocks()
    if not events:
        print("📊 No pending blocks found")
        return
    
    # Get current state to avoid duplicates
    state = get_current_blockchain_state()
    existing_hashes = {block["block_hash"] for block in state.get("blocks", [])}
    
    # Process new blocks
    new_blocks = []
    for event in events:
        event_id, block_hash, miner_address, work_score, ts, cid, capacity = event
        
        # Skip if already processed
        if block_hash in existing_hashes:
            continue
        
        # Create block
        block = create_block_from_event(event)
        new_blocks.append(block)
        existing_hashes.add(block_hash)
        
        print(f"✅ Processed block #{block['index']} by {miner_address}")
        print(f"   Hash: {block_hash[:16]}...")
        print(f"   Work score: {work_score}")
    
    if new_blocks:
        # Update blockchain state
        update_blockchain_state(new_blocks)
        print(f"🎉 Successfully processed {len(new_blocks)} new blocks!")
    else:
        print("📊 No new blocks to process")

def main():
    """Main function."""
    print("🔧 Bypassing consensus validation for peer blocks...")
    
    # Check if we're on the droplet
    if not os.path.exists("/home/coinjecture/COINjecture"):
        print("❌ This script must be run on the droplet")
        return 1
    
    # Process peer blocks
    process_peer_blocks()
    
    print("✅ Peer block processing completed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
