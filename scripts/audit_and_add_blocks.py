#!/usr/bin/env python3
"""
Audit and add original 16 blocks from cache to consensus database.
"""

import json
import sqlite3
import sys
import os
from pathlib import Path

def audit_blocks(blockchain_state_path):
    """Audit the blockchain state and return block data."""
    try:
        with open(blockchain_state_path, 'r') as f:
            blockchain_state = json.load(f)
        
        blocks = blockchain_state.get('blocks', [])
        print(f"📊 Found {len(blocks)} blocks in blockchain state")
        
        # Audit each block
        for i, block in enumerate(blocks):
            print(f"Block #{block['index']}: {block['block_hash'][:16]}... (prev: {block['previous_hash'][:16]}...)")
            
            # Validate block structure
            required_fields = ['index', 'timestamp', 'previous_hash', 'block_hash', 'cumulative_work_score']
            for field in required_fields:
                if field not in block:
                    print(f"❌ Missing field '{field}' in block {block['index']}")
                    return False
        
        return blocks
    except Exception as e:
        print(f"❌ Failed to audit blocks: {e}")
        return None

def add_blocks_to_consensus_db(blocks, consensus_db_path):
    """Add blocks to consensus database."""
    try:
        with sqlite3.connect(consensus_db_path) as conn:
            cur = conn.cursor()
            
            # Check if blocks table exists
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='blocks'")
            if not cur.fetchone():
                print("Creating blocks table...")
                cur.execute("""
                    CREATE TABLE blocks (
                        block_hash TEXT PRIMARY KEY,
                        height INTEGER,
                        previous_hash TEXT,
                        timestamp REAL,
                        merkle_root TEXT,
                        mining_capacity TEXT,
                        cumulative_work_score REAL,
                        offchain_cid TEXT,
                        created_at REAL
                    )
                """)
            
            # Insert each block
            for block in blocks:
                cur.execute("""
                    INSERT OR REPLACE INTO blocks 
                    (block_hash, height, previous_hash, timestamp, merkle_root, 
                     mining_capacity, cumulative_work_score, offchain_cid, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    block['block_hash'],
                    block['index'],
                    block['previous_hash'],
                    block['timestamp'],
                    block['merkle_root'],
                    block['mining_capacity'],
                    block['cumulative_work_score'],
                    block.get('offchain_cid', ''),
                    block['timestamp']  # Use block timestamp as created_at
                ))
            
            conn.commit()
            print(f"✅ Added {len(blocks)} blocks to consensus database")
            return True
            
    except Exception as e:
        print(f"❌ Failed to add blocks to consensus database: {e}")
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 audit_and_add_blocks.py <blockchain_state.json> <consensus.db>")
        sys.exit(1)
    
    blockchain_state_path = sys.argv[1]
    consensus_db_path = sys.argv[2]
    
    if not os.path.exists(blockchain_state_path):
        print(f"❌ Blockchain state file not found: {blockchain_state_path}")
        sys.exit(1)
    
    print("🔍 Auditing blockchain state...")
    blocks = audit_blocks(blockchain_state_path)
    if not blocks:
        sys.exit(1)
    
    print(f"✅ Audit complete: {len(blocks)} blocks validated")
    
    print("📝 Adding blocks to consensus database...")
    if add_blocks_to_consensus_db(blocks, consensus_db_path):
        print("🎉 Successfully added all blocks to consensus database!")
    else:
        print("❌ Failed to add blocks to consensus database")
        sys.exit(1)

if __name__ == "__main__":
    main()
