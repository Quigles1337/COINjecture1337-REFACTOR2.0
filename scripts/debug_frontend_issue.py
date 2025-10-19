#!/usr/bin/env python3
"""
Debug frontend refresh loop issue
"""

import requests
import json

def test_api_endpoint():
    """Test the API endpoint that the frontend is calling"""
    try:
        response = requests.get('https://api.coinjecture.com/v1/data/block/latest', timeout=10)
        print(f"✅ API Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Response: {json.dumps(data, indent=2)[:200]}...")
            return True
        else:
            print(f"❌ API Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ API Exception: {e}")
        return False

def test_frontend_files():
    """Test if frontend files are accessible"""
    try:
        response = requests.get('https://api.coinjecture.com/', timeout=10)
        print(f"✅ Frontend Status: {response.status_code}")
        if response.status_code == 200:
            content = response.text
            if '<html' in content.lower():
                print("✅ Frontend serving HTML")
                return True
            else:
                print("❌ Frontend not serving HTML")
                print(f"Content: {content[:200]}...")
                return False
        else:
            print(f"❌ Frontend Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Frontend Exception: {e}")
        return False

def main():
    print("🔍 Debugging Frontend Refresh Loop Issue")
    print("=" * 50)
    
    print("\n1. Testing API endpoint...")
    api_works = test_api_endpoint()
    
    print("\n2. Testing frontend files...")
    frontend_works = test_frontend_files()
    
    print(f"\n📊 Results:")
    print(f"   API: {'✅ Working' if api_works else '❌ Failed'}")
    print(f"   Frontend: {'✅ Working' if frontend_works else '❌ Failed'}")
    
    if api_works and frontend_works:
        print("\n🎯 Issue Analysis:")
        print("   - API is working correctly")
        print("   - Frontend files are accessible")
        print("   - The refresh loop is likely caused by:")
        print("     1. JavaScript error in browser console")
        print("     2. Certificate issue in browser")
        print("     3. CORS issue")
        print("     4. Infinite loop in JavaScript code")
        print("\n💡 Next Steps:")
        print("   1. Check browser console for JavaScript errors")
        print("   2. Check if certificate is accepted in browser")
        print("   3. Try accessing https://api.coinjecture.com directly")
        print("   4. Clear browser cache completely")
    
    return 0

if __name__ == "__main__":
    exit(main())
