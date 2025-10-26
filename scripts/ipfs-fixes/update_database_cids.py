#!/usr/bin/env python3
"""
Update Database with New IPFS CIDs
"""

import sys
import os
sys.path.append('src')

from api.blockchain_storage import COINjectureStorage
from storage import IPFSClient
import json
import sqlite3

def update_database_cids():
    """Update database with new IPFS CIDs that have accessible proof data."""
    print("🚀 Updating Database with New IPFS CIDs")
    print("=" * 45)
    
    # Initialize storage
    api_storage = COINjectureStorage(data_dir="/opt/coinjecture/data")
    ipfs_client = IPFSClient("http://localhost:5001")
    
    if not ipfs_client.health_check():
        print("❌ IPFS daemon not available. Start IPFS first.")
        return False
    
    print("✅ IPFS daemon is healthy")
    
    # Get all blocks
    latest_height = api_storage.get_latest_height()
    print(f"📊 Processing {latest_height + 1} blocks...")
    
    updated_count = 0
    
    # Test blocks that we know have new CIDs
    test_blocks = [10, 20, 30, 40, 50, 60, 70, 80, 90, 93]
    new_cids = [
        "QmavzDii8VR3VuZr",  # Block 10
        "QmXGLub4eoB8fAM4",  # Block 20
        "QmV2RxdSykZqh9BK",  # Block 30
        "QmPtuzC85CP76WJh",  # Block 40
        "QmZMXr98TvPEp4aN",  # Block 50
        "QmSXPvuyFYhz4USw",  # Block 60
        "QmTxrPkabrSQvtuS",  # Block 70
        "QmdDPV2W9CYEw71r",  # Block 80
        "QmUNTr97U4i3AcUF",  # Block 90
        "QmbZLaqRRqVtTkg6"   # Block 93
    ]
    
    for i, new_cid in zip(test_blocks, new_cids):
        if i <= latest_height:
            try:
                # Verify the new CID is accessible
                data = ipfs_client.get(new_cid)
                print(f"✅ Block {i}: {new_cid[:16]}... - {len(data)} bytes")
                
                # Update the database
                conn = sqlite3.connect(api_storage.db_path)
                cursor = conn.cursor()
                
                # Update the CID in the database
                cursor.execute('''
                    UPDATE blocks 
                    SET block_bytes = json_replace(block_bytes, '$.cid', ?)
                    WHERE height = ?
                ''', (new_cid, i))
                
                conn.commit()
                conn.close()
                
                updated_count += 1
                print(f"   ✅ Updated database for Block {i}")
                
            except Exception as e:
                print(f"   ❌ Block {i}: {str(e)[:50]}...")
    
    print(f"\\n📊 Update Summary:")
    print(f"   Updated blocks: {updated_count}")
    print(f"   Total tested: {len(test_blocks)}")
    
    return updated_count > 0

if __name__ == "__main__":
    success = update_database_cids()
    sys.exit(0 if success else 1)
