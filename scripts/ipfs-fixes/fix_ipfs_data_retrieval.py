#!/usr/bin/env python3
"""
Fix IPFS Data Retrieval - Pin all CIDs and regenerate missing blocks
"""

import sys
import os
sys.path.append('src')

from api.blockchain_storage import storage
from storage import IPFSClient
import json
import subprocess

def pin_all_cids():
    """Pin all CIDs in the database to prevent garbage collection."""
    print("📌 Pinning all CIDs to prevent garbage collection...")
    
    ipfs_client = IPFSClient("http://localhost:5001")
    latest_height = storage.get_latest_height()
    
    pinned_count = 0
    failed_count = 0
    
    for i in range(latest_height + 1):
        block_data = storage.get_block_data(i)
        if block_data:
            cid = block_data.get("cid")
            if cid and cid.startswith("Qm") and len(cid) == 46:
                try:
                    # Pin the CID
                    result = subprocess.run([
                        "curl", "-X", "POST", 
                        f"http://localhost:5001/api/v0/pin/add?arg={cid}"
                    ], capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0:
                        pinned_count += 1
                        print(f"✅ Pinned Block {i}: {cid}")
                    else:
                        failed_count += 1
                        print(f"❌ Failed to pin Block {i}: {cid}")
                        
                except Exception as e:
                    failed_count += 1
                    print(f"❌ Exception pinning Block {i}: {e}")
    
    print(f"\n📊 Pinning Summary:")
    print(f"   Successfully pinned: {pinned_count}")
    print(f"   Failed to pin: {failed_count}")
    return pinned_count, failed_count

def test_cid_retrieval():
    """Test retrieval of all CIDs after pinning."""
    print("\n🔍 Testing CID retrieval after pinning...")
    
    ipfs_client = IPFSClient("http://localhost:5001")
    latest_height = storage.get_latest_height()
    
    working_cids = []
    failed_cids = []
    
    for i in range(min(20, latest_height + 1)):  # Test first 20 blocks
        block_data = storage.get_block_data(i)
        if block_data:
            cid = block_data.get("cid")
            if cid and cid.startswith("Qm") and len(cid) == 46:
                try:
                    data = ipfs_client.get(cid)
                    working_cids.append((i, cid, len(data)))
                    print(f"✅ Block {i}: {cid} - {len(data)} bytes")
                except Exception as e:
                    failed_cids.append((i, cid, str(e)[:50]))
                    print(f"❌ Block {i}: {cid} - {str(e)[:50]}...")
    
    print(f"\n📈 Retrieval Test Summary:")
    print(f"   Working CIDs: {len(working_cids)}")
    print(f"   Failed CIDs: {len(failed_cids)}")
    
    return working_cids, failed_cids

def regenerate_missing_blocks():
    """Regenerate blocks that can't be retrieved from IPFS."""
    print("\n🔄 Regenerating missing blocks...")
    
    # This would require the original mining process
    # For now, we'll focus on pinning existing CIDs
    print("   Note: Block regeneration requires original mining process")
    print("   Current focus: Pin existing CIDs to prevent further data loss")

def main():
    print("🔧 IPFS Data Retrieval Fix")
    print("=" * 50)
    
    # Step 1: Pin all CIDs
    pinned_count, failed_count = pin_all_cids()
    
    # Step 2: Test retrieval
    working_cids, failed_cids = test_cid_retrieval()
    
    # Step 3: Report status
    print(f"\n📊 Final Status:")
    print(f"   Total CIDs pinned: {pinned_count}")
    print(f"   CIDs working after pinning: {len(working_cids)}")
    print(f"   CIDs still failing: {len(failed_cids)}")
    
    if len(working_cids) > 1:
        print(f"\n✅ Success! Multiple blocks now accessible:")
        for block_num, cid, size in working_cids[:5]:
            print(f"   Block {block_num}: {cid} ({size} bytes)")
    else:
        print(f"\n⚠️  Only {len(working_cids)} block(s) accessible")
        print("   Consider regenerating missing blocks")

if __name__ == "__main__":
    main()
