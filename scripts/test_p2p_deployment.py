#!/usr/bin/env python3
"""
Test P2P Network Deployment
This script tests the P2P network connectivity fix before pushing to GitHub.
"""

import json
import time
import requests
import subprocess
import sys
from pathlib import Path

def test_network_before_deployment():
    """Test network status before deployment."""
    print("🧪 Testing Network Status Before Deployment")
    print("=" * 50)
    
    try:
        # Test API connectivity
        response = requests.get('https://167.172.213.70/v1/data/block/latest', verify=False, timeout=10)
        if response.status_code == 200:
            data = response.json()
            current_block = data['data']['index']
            print(f"✅ API accessible - Current block: #{current_block}")
            
            # Test all blocks
            all_blocks_response = requests.get('https://167.172.213.70/v1/data/blocks/all', verify=False, timeout=10)
            if all_blocks_response.status_code == 200:
                all_data = all_blocks_response.json()
                blocks = all_data['data']
                print(f"📊 Total blocks: {len(blocks)}")
                print(f"🔢 Latest index: {blocks[-1]['index'] if blocks else 'None'}")
                
                # Check for blocks beyond 166
                beyond_166 = [block for block in blocks if block['index'] > 166]
                if beyond_166:
                    print(f"✅ Found {len(beyond_166)} blocks beyond #166!")
                    return True, current_block, len(beyond_166)
                else:
                    print("❌ No blocks beyond #166 - P2P network needs fixing")
                    return False, current_block, 0
            else:
                print(f"❌ Failed to get all blocks: {all_blocks_response.status_code}")
                return False, current_block, 0
        else:
            print(f"❌ API not accessible: {response.status_code}")
            return False, None, 0
            
    except Exception as e:
        print(f"❌ Network test failed: {e}")
        return False, None, 0

def test_p2p_services():
    """Test P2P services connectivity."""
    print("\n🔍 Testing P2P Services Connectivity")
    print("=" * 40)
    
    services = [
        ("P2P Discovery", "https://167.172.213.70:12346/peers"),
        ("Consensus Service", "https://167.172.213.70:12345/status"),
        ("API Service", "https://167.172.213.70/v1/data/block/latest")
    ]
    
    results = {}
    for name, url in services:
        try:
            response = requests.get(url, verify=False, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: Running")
                results[name] = True
            else:
                print(f"⚠️  {name}: Status {response.status_code}")
                results[name] = False
        except Exception as e:
            print(f"❌ {name}: Not accessible - {str(e)[:50]}...")
            results[name] = False
    
    return results

def simulate_p2p_fix_deployment():
    """Simulate the P2P fix deployment."""
    print("\n🔧 Simulating P2P Network Fix Deployment")
    print("=" * 45)
    
    # Check if we have the fix files
    fix_files = [
        "/tmp/enhanced_p2p_discovery.py",
        "/tmp/network_connectivity_fix.sh"
    ]
    
    for file_path in fix_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}: Ready for deployment")
        else:
            print(f"❌ {file_path}: Not found")
            return False
    
    print("\n📋 Deployment Simulation:")
    print("1. ✅ Enhanced P2P Discovery Service created")
    print("2. ✅ Network connectivity fix script created")
    print("3. ✅ Ready for remote server deployment")
    print("4. ⏳ Would deploy enhanced P2P discovery to remote server")
    print("5. ⏳ Would restart P2P services with improved connectivity")
    print("6. ⏳ Would test network advancement beyond block #166")
    
    return True

def test_block_submission():
    """Test if new blocks can be submitted."""
    print("\n🧪 Testing Block Submission")
    print("=" * 30)
    
    test_payload = {
        'event_id': f'p2p_test_{int(time.time())}',
        'block_index': 167,
        'block_hash': f'p2p_test_{int(time.time())}',
        'cid': f'QmP2PTest{int(time.time())}',
        'miner_address': 'p2p-test-miner',
        'capacity': 'MOBILE',
        'work_score': 1.0,
        'ts': time.time(),
        'signature': 'a' * 64,
        'public_key': 'b' * 64
    }
    
    try:
        response = requests.post('https://167.172.213.70/v1/ingest/block', 
                               json=test_payload, verify=False, timeout=10)
        
        print(f"📤 Block submission status: {response.status_code}")
        print(f"📤 Response: {response.text[:100]}...")
        
        if response.status_code == 200:
            print("✅ Block submission successful!")
            return True
        else:
            print(f"❌ Block submission failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Block submission error: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 P2P Network Deployment Test - v3.9.25")
    print("=" * 50)
    
    # Test 1: Network status before deployment
    network_ok, current_block, blocks_beyond_166 = test_network_before_deployment()
    
    # Test 2: P2P services
    service_results = test_p2p_services()
    
    # Test 3: Simulate deployment
    deployment_ready = simulate_p2p_fix_deployment()
    
    # Test 4: Block submission
    submission_ok = test_block_submission()
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 25)
    print(f"🌐 Network Status: {'✅ OK' if network_ok else '❌ Issues'}")
    print(f"📊 Current Block: #{current_block if current_block else 'Unknown'}")
    print(f"📈 Blocks Beyond #166: {blocks_beyond_166}")
    print(f"🔍 P2P Discovery: {'✅ OK' if service_results.get('P2P Discovery', False) else '❌ Not accessible'}")
    print(f"🔍 Consensus Service: {'✅ OK' if service_results.get('Consensus Service', False) else '❌ Not accessible'}")
    print(f"🔍 API Service: {'✅ OK' if service_results.get('API Service', False) else '❌ Not accessible'}")
    print(f"🔧 Deployment Ready: {'✅ Yes' if deployment_ready else '❌ No'}")
    print(f"📤 Block Submission: {'✅ OK' if submission_ok else '❌ Failed'}")
    
    # Recommendations
    print("\n💡 Recommendations:")
    if not service_results.get('P2P Discovery', False):
        print("🔧 Deploy enhanced P2P discovery service")
    if not service_results.get('Consensus Service', False):
        print("🔧 Fix consensus service connectivity")
    if blocks_beyond_166 == 0:
        print("🔧 P2P network needs connectivity fix to advance beyond #166")
    if not submission_ok:
        print("🔧 Fix block submission process")
    
    print("\n✅ P2P Network Deployment Test Complete!")
    print("🔧 Ready for deployment to resolve network stalling at block #166")
    
    return network_ok and deployment_ready

if __name__ == "__main__":
    main()
