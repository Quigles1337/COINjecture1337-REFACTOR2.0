#!/usr/bin/env python3
"""
Test Production API Setup
Tests the new https://api.coinjecture.com endpoint
"""

import requests
import json
import sys
from urllib.parse import urljoin

API_BASE = "https://api.coinjecture.com"

def test_endpoint(endpoint, method="GET", data=None, headers=None):
    """Test a specific API endpoint"""
    url = urljoin(API_BASE, endpoint)
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10)
        else:
            print(f"❌ Unsupported method: {method}")
            return False
            
        print(f"🔍 {method} {url}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ Success")
            try:
                data = response.json()
                print(f"   📊 Response: {json.dumps(data, indent=2)[:200]}...")
            except:
                print(f"   📊 Response: {response.text[:200]}...")
            return True
        else:
            print(f"   ❌ Failed: {response.text[:200]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Test all production API endpoints"""
    print("🧪 Testing Production API: https://api.coinjecture.com")
    print("=" * 60)
    
    tests = [
        ("/health", "GET"),
        ("/v1/data/block/latest", "GET"),
        ("/v1/data/blocks?start=0&end=10", "GET"),
        ("/v1/rewards/leaderboard", "GET"),
    ]
    
    passed = 0
    total = len(tests)
    
    for endpoint, method in tests:
        if test_endpoint(endpoint, method):
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("✅ All tests passed! Production API is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the API configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
