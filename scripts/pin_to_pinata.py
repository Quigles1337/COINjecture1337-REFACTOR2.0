#!/usr/bin/env python3
"""
Pin Genesis Block to Pinata
This script pins the genesis block CID to Pinata for public accessibility.
"""

import requests
import json
import sys
import os

# Pinata API configuration
PINATA_API_KEY = "YOUR_PINATA_API_KEY"  # Replace with actual API key
PINATA_SECRET_KEY = "YOUR_PINATA_SECRET_KEY"  # Replace with actual secret key
PINATA_JWT = "YOUR_PINATA_JWT"  # Replace with actual JWT token

# Genesis block CID
GENESIS_CID = "QmQNoHfC6e2eFHYPeTfAFQWmDh649TJZaKwNX6kjwZau5F"

def pin_to_pinata(cid, name="COINjecture Genesis Block"):
    """Pin a CID to Pinata."""
    
    url = "https://api.pinata.cloud/pinning/pinByHash"
    
    headers = {
        "pinata_api_key": PINATA_API_KEY,
        "pinata_secret_api_key": PINATA_SECRET_KEY,
        "Content-Type": "application/json"
    }
    
    data = {
        "hashToPin": cid,
        "pinataMetadata": {
            "name": name,
            "keyvalues": {
                "type": "genesis_block",
                "blockchain": "coinjecture",
                "version": "3.15.0"
            }
        },
        "pinataOptions": {
            "cidVersion": 0
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ Successfully pinned {cid} to Pinata")
        print(f"   Pin ID: {result.get('IpfsHash', 'N/A')}")
        print(f"   Pin Size: {result.get('PinSize', 'N/A')} bytes")
        print(f"   Timestamp: {result.get('Timestamp', 'N/A')}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error pinning to Pinata: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return False

def verify_pinata_access(cid):
    """Verify that the CID is accessible via Pinata gateway."""
    
    url = f"https://gateway.pinata.cloud/ipfs/{cid}"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Try to parse as JSON to verify it's our genesis block
        data = response.json()
        if data.get('block_hash') == 'd1700c2681b75c1d22ed08285994c202d310ff25cf40851365ca6fea22011358':
            print(f"✅ Genesis block verified accessible via Pinata gateway")
            print(f"   Target: {data['problem']['target']}")
            print(f"   Solution: {data['solution']}")
            print(f"   Sum: {sum(data['solution'])}")
            return True
        else:
            print(f"❌ Genesis block data doesn't match expected content")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying Pinata access: {e}")
        return False

def main():
    print("🚀 Pinning Genesis Block to Pinata...")
    print(f"   CID: {GENESIS_CID}")
    
    # Check if API keys are configured
    if PINATA_API_KEY == "YOUR_PINATA_API_KEY":
        print("❌ Pinata API keys not configured!")
        print("   Please update the script with your Pinata API credentials")
        return 1
    
    # Pin to Pinata
    success = pin_to_pinata(GENESIS_CID, "COINjecture Genesis Block v3.15.0")
    
    if success:
        print("\n🔍 Verifying Pinata accessibility...")
        verify_success = verify_pinata_access(GENESIS_CID)
        
        if verify_success:
            print("\n✅ Genesis block successfully pinned and accessible via Pinata!")
            print(f"   Pinata Gateway: https://gateway.pinata.cloud/ipfs/{GENESIS_CID}")
            return 0
        else:
            print("\n⚠️  Pinned to Pinata but verification failed")
            return 1
    else:
        print("\n❌ Failed to pin to Pinata")
        return 1

if __name__ == "__main__":
    sys.exit(main())
