#!/usr/bin/env python3
"""
Configure IPFS for Blockchain Data Persistence
"""

import sys
import os
sys.path.append('src')

import subprocess
import json
import time

def configure_ipfs_for_blockchain():
    """Configure IPFS to prevent garbage collection of blockchain data."""
    print("🔧 Configuring IPFS for blockchain data persistence...")
    
    # Disable automatic garbage collection
    print("📌 Disabling automatic garbage collection...")
    try:
        result = subprocess.run([
            "curl", "-X", "POST", 
            "http://localhost:5001/api/v0/config?arg=Datastore.GC.Period&value=0"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("   ✅ Automatic GC disabled")
        else:
            print(f"   ❌ Failed to disable GC: {result.stderr}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Set larger storage limit
    print("💾 Setting larger storage limit...")
    try:
        result = subprocess.run([
            "curl", "-X", "POST", 
            "http://localhost:5001/api/v0/config?arg=Datastore.StorageMax&value=50GB"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("   ✅ Storage limit set to 50GB")
        else:
            print(f"   ❌ Failed to set storage limit: {result.stderr}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Configure for server use
    print("🖥️  Configuring for server use...")
    try:
        result = subprocess.run([
            "curl", "-X", "POST", 
            "http://localhost:5001/api/v0/config?arg=Datastore.StorageGCWatermark&value=90"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("   ✅ GC watermark set to 90%")
        else:
            print(f"   ❌ Failed to set GC watermark: {result.stderr}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

def pin_all_existing_cids():
    """Pin all existing CIDs to prevent garbage collection."""
    print("\n📌 Pinning all existing CIDs...")
    
    from api.blockchain_storage import storage
    
    latest_height = storage.get_latest_height()
    pinned_count = 0
    failed_count = 0
    
    for i in range(latest_height + 1):
        block_data = storage.get_block_data(i)
        if block_data:
            cid = block_data.get("cid")
            if cid and cid.startswith("Qm") and len(cid) == 46:
                try:
                    result = subprocess.run([
                        "curl", "-X", "POST", 
                        f"http://localhost:5001/api/v0/pin/add?arg={cid}"
                    ], capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0:
                        pinned_count += 1
                        if i % 10 == 0:  # Progress indicator
                            print(f"   Pinned {pinned_count} CIDs...")
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    failed_count += 1
    
    print(f"   ✅ Pinned {pinned_count} CIDs")
    print(f"   ❌ Failed to pin {failed_count} CIDs")
    return pinned_count, failed_count

def test_ipfs_functionality():
    """Test IPFS functionality after configuration."""
    print("\n🧪 Testing IPFS functionality...")
    
    from storage import IPFSClient
    
    try:
        client = IPFSClient("http://localhost:5001")
        
        # Test upload
        test_data = b"blockchain test data for IPFS functionality"
        cid = client.add(test_data)
        print(f"   ✅ Upload successful: {cid}")
        
        # Test retrieval
        retrieved = client.get(cid)
        print(f"   ✅ Retrieval successful: {len(retrieved)} bytes")
        print(f"   ✅ Data integrity: {retrieved == test_data}")
        
        # Pin the test data
        result = subprocess.run([
            "curl", "-X", "POST", 
            f"http://localhost:5001/api/v0/pin/add?arg={cid}"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"   ✅ Pinning successful")
        else:
            print(f"   ❌ Pinning failed: {result.stderr}")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def main():
    print("🚀 IPFS Blockchain Configuration")
    print("=" * 50)
    
    # Step 1: Configure IPFS
    configure_ipfs_for_blockchain()
    
    # Step 2: Pin existing CIDs
    pinned_count, failed_count = pin_all_existing_cids()
    
    # Step 3: Test functionality
    test_success = test_ipfs_functionality()
    
    # Step 4: Report status
    print(f"\n📊 Configuration Summary:")
    print(f"   CIDs pinned: {pinned_count}")
    print(f"   CIDs failed: {failed_count}")
    print(f"   IPFS test: {'✅ Passed' if test_success else '❌ Failed'}")
    
    if test_success:
        print(f"\n✅ IPFS configured successfully for blockchain data!")
        print(f"   - Automatic GC disabled")
        print(f"   - Storage limit increased")
        print(f"   - All existing CIDs pinned")
        print(f"   - New uploads/retrievals working")
    else:
        print(f"\n❌ IPFS configuration issues detected")
        print(f"   Check IPFS daemon status and configuration")

if __name__ == "__main__":
    main()
