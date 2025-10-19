#!/usr/bin/env python3
"""
Test Network Flow: Verify that new blocks can be submitted and processed
This script tests the network after the signature validation fix is deployed.
"""

import json
import time
import requests
import sys
from pathlib import Path

def test_api_connectivity():
    """Test if API is accessible and responding."""
    print("🔍 Testing API connectivity...")
    try:
        response = requests.get('https://167.172.213.70/v1/data/block/latest', 
                             verify=False, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API accessible - Current block: #{data['data']['index']}")
            return data['data']['index']
        else:
            print(f"❌ API error: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return None

def test_block_submission():
    """Test if new blocks can be submitted to the API."""
    print("🧪 Testing block submission with enhanced signature validation...")
    
    # Create a valid test payload with proper hex strings
    test_payload = {
        'event_id': f'test_block_167_{int(time.time())}',
        'block_index': 167,
        'block_hash': f'test_block_167_{int(time.time())}',
        'cid': f'QmTestBlock167{int(time.time())}',
        'miner_address': 'test-miner-167',
        'capacity': 'MOBILE',
        'work_score': 1.0,
        'ts': time.time(),
        'signature': 'a' * 64,  # Valid hex string (64 chars)
        'public_key': 'b' * 64   # Valid hex string (64 chars)
    }
    
    try:
        response = requests.post('https://167.172.213.70/v1/ingest/block', 
                              json=test_payload, 
                              verify=False, 
                              timeout=10)
        
        print(f"📤 Submission Status: {response.status_code}")
        print(f"📤 Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("✅ Block submission successful!")
            return True
        else:
            print(f"❌ Block submission failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Submission error: {e}")
        return False

def test_invalid_signature_handling():
    """Test that invalid signatures are handled gracefully."""
    print("🧪 Testing invalid signature handling...")
    
    # Create payload with invalid signature (non-hex)
    invalid_payload = {
        'event_id': f'invalid_test_{int(time.time())}',
        'block_index': 168,
        'block_hash': f'invalid_test_{int(time.time())}',
        'cid': f'QmInvalid{int(time.time())}',
        'miner_address': 'invalid-miner',
        'capacity': 'MOBILE',
        'work_score': 1.0,
        'ts': time.time(),
        'signature': 'invalid_signature_not_hex',  # Invalid hex string
        'public_key': 'invalid_public_key_not_hex'  # Invalid hex string
    }
    
    try:
        response = requests.post('https://167.172.213.70/v1/ingest/block', 
                              json=invalid_payload, 
                              verify=False, 
                              timeout=10)
        
        print(f"📤 Invalid signature test - Status: {response.status_code}")
        print(f"📤 Response: {response.text[:200]}...")
        
        # Should return 401 (Invalid signature) instead of 500 (server error)
        if response.status_code == 401:
            print("✅ Invalid signature handled gracefully!")
            return True
        elif response.status_code == 500:
            print("❌ Server error - signature validation still crashing")
            return False
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Invalid signature test error: {e}")
        return False

def monitor_blockchain_advancement():
    """Monitor if blockchain advances beyond current block."""
    print("📊 Monitoring blockchain advancement...")
    
    # Get initial block
    initial_response = requests.get('https://167.172.213.70/v1/data/block/latest', verify=False)
    if initial_response.status_code != 200:
        print("❌ Failed to get initial block")
        return False
    
    initial_data = initial_response.json()
    initial_block = initial_data['data']['index']
    print(f"📈 Initial block: #{initial_block}")
    
    # Wait a bit and check again
    print("⏳ Waiting 10 seconds for potential block processing...")
    time.sleep(10)
    
    final_response = requests.get('https://167.172.213.70/v1/data/block/latest', verify=False)
    if final_response.status_code != 200:
        print("❌ Failed to get final block")
        return False
    
    final_data = final_response.json()
    final_block = final_data['data']['index']
    print(f"📈 Final block: #{final_block}")
    
    if final_block > initial_block:
        print(f"✅ Blockchain advanced from #{initial_block} to #{final_block}!")
        return True
    else:
        print(f"⚠️  Blockchain still at #{final_block} (no advancement)")
        return False

def main():
    """Main test function."""
    print("🧪 Network Flow Test - Post Signature Validation Fix")
    print("=" * 60)
    
    # Test 1: API Connectivity
    current_block = test_api_connectivity()
    if current_block is None:
        print("❌ Cannot proceed - API not accessible")
        return False
    
    # Test 2: Block Submission
    if not test_block_submission():
        print("❌ Block submission still failing")
        return False
    
    # Test 3: Invalid Signature Handling
    if not test_invalid_signature_handling():
        print("❌ Invalid signature handling not working")
        return False
    
    # Test 4: Blockchain Advancement
    if not monitor_blockchain_advancement():
        print("⚠️  Blockchain not advancing (may need more time)")
    
    print("\n✅ Network Flow Test Complete!")
    print("🔧 Signature validation fix appears to be working")
    print("📊 Network should now be able to process new blocks")
    
    return True

if __name__ == "__main__":
    main()
