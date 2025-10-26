#!/usr/bin/env python3
"""
Add original 16 blocks to consensus database using proper schema.
"""

import json
import sqlite3
import sys
import os
import hashlib
import struct

def create_block_header(block_data):
    """Create block header bytes from block data."""
    # Create a simplified header structure
    # This is a placeholder - in reality, this would be the actual block header format
    header_data = {
        'index': block_data['index'],
        'timestamp': int(block_data['timestamp']),
        'previous_hash': block_data['previous_hash'],
        'merkle_root': block_data['merkle_root'],
        'mining_capacity': block_data['mining_capacity'],
        'cumulative_work_score': block_data['cumulative_work_score']
    }
    
    # Serialize header data (simplified)
    header_json = json.dumps(header_data, sort_keys=True)
    return header_json.encode('utf-8')

def add_blocks_to_consensus(blocks, consensus_db_path):
    """Add blocks to consensus database using proper schema."""
    try:
        with sqlite3.connect(consensus_db_path) as conn:
            cur = conn.cursor()
            
            print(f"📝 Adding {len(blocks)} blocks to consensus database...")
            
            for block in blocks:
                # Create header
                header_bytes = create_block_header(block)
                header_hash = hashlib.sha256(header_bytes).digest()
                
                # Insert header
                cur.execute("""
                    INSERT OR REPLACE INTO headers 
                    (header_hash, header_bytes, height, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (
                    header_hash,
                    header_bytes,
                    block['index'],
                    int(block['timestamp'])
                ))
                
                # Create block bytes (simplified)
                block_data = {
                    'index': block['index'],
                    'timestamp': block['timestamp'],
                    'previous_hash': block['previous_hash'],
                    'block_hash': block['block_hash'],
                    'merkle_root': block['merkle_root'],
                    'mining_capacity': block['mining_capacity'],
                    'cumulative_work_score': block['cumulative_work_score'],
                    'offchain_cid': block.get('offchain_cid', '')
                }
                block_bytes = json.dumps(block_data, sort_keys=True).encode('utf-8')
                block_hash_bytes = bytes.fromhex(block['block_hash'].replace('0x', ''))
                
                # Insert block
                cur.execute("""
                    INSERT OR REPLACE INTO blocks 
                    (block_hash, block_bytes, header_hash)
                    VALUES (?, ?, ?)
                """, (
                    block_hash_bytes,
                    block_bytes,
                    header_hash
                ))
                
                # Add to work index
                cur.execute("""
                    INSERT OR REPLACE INTO work_index 
                    (height, cumulative_work, block_hash)
                    VALUES (?, ?, ?)
                """, (
                    block['index'],
                    int(block['cumulative_work_score']),
                    block_hash_bytes
                ))
                
                print(f"  ✅ Added block #{block['index']}: {block['block_hash'][:16]}...")
            
            # Set the latest block as tip
            latest_block = blocks[-1]
            latest_block_hash = bytes.fromhex(latest_block['block_hash'].replace('0x', ''))
            latest_work = int(latest_block['cumulative_work_score'])
            
            cur.execute("""
                INSERT OR REPLACE INTO tips 
                (id, tip_hash, cumulative_work)
                VALUES (1, ?, ?)
            """, (latest_block_hash, latest_work))
            
            conn.commit()
            print(f"✅ Successfully added {len(blocks)} blocks to consensus database")
            print(f"🎯 Set block #{latest_block['index']} as tip with work score {latest_work}")
            return True
            
    except Exception as e:
        print(f"❌ Failed to add blocks to consensus database: {e}")
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 add_blocks_to_consensus.py <blockchain_state.json> <consensus.db>")
        sys.exit(1)
    
    blockchain_state_path = sys.argv[1]
    consensus_db_path = sys.argv[2]
    
    if not os.path.exists(blockchain_state_path):
        print(f"❌ Blockchain state file not found: {blockchain_state_path}")
        sys.exit(1)
    
    # Load blockchain state
    with open(blockchain_state_path, 'r') as f:
        blockchain_state = json.load(f)
    
    blocks = blockchain_state.get('blocks', [])
    print(f"📊 Found {len(blocks)} blocks in blockchain state")
    
    if add_blocks_to_consensus(blocks, consensus_db_path):
        print("🎉 Successfully added all blocks to consensus database!")
    else:
        print("❌ Failed to add blocks to consensus database")
        sys.exit(1)

if __name__ == "__main__":
    main()
