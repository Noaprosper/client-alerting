#!/usr/bin/env python3
"""
Test script to verify Scaleway Console API configuration.
This script tests the /dashboard endpoint with your API key.
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CONSOLE_API_URL = os.getenv('CONSOLE_API_URL', 'https://api.scaleway.com/resource-private/v1alpha1/dashboard')
SCALEWAY_API_KEY = os.getenv('SCALEWAY_API_KEY', '')

def test_api_connection(org_id=None):
    """Test connection to Scaleway Console API"""
    
    if not SCALEWAY_API_KEY:
        print("❌ SCALEWAY_API_KEY not set in .env file")
        return False
    
    print(f"🔧 Testing Scaleway Console API...")
    print(f"   Endpoint: {CONSOLE_API_URL}")
    print(f"   API Key: {SCALEWAY_API_KEY[:8]}...{SCALEWAY_API_KEY[-4:]}")
    
    if not org_id:
        print("\n⚠️  No organization_id provided. Testing with a sample UUID...")
        org_id = "11111111-1111-1111-1111-111111111111"
    
    params = {
        'organization_id': org_id,
        'products': [1, 3, 7],  # instance, object_storage, rdb
        'localities': 1,
        'strategy': 1
    }
    
    print(f"\n📤 Request:")
    print(f"   URL: {CONSOLE_API_URL}")
    print(f"   Params: {params}")
    
    try:
        response = requests.get(
            CONSOLE_API_URL,
            headers={'X-Auth-Token': SCALEWAY_API_KEY},
            params=params,
            timeout=30
        )
        
        print(f"\n📥 Response:")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success!")
            print(f"   Response: {data}")
            
            # Check if response has expected format
            if 'counters' in data:
                print(f"\n✅ API response format is correct!")
                print(f"   Found {len(data.get('counters', []))} counter(s)")
                return True
            else:
                print(f"\n⚠️  Response format unexpected - missing 'counters' field")
                return False
                
        elif response.status_code == 403:
            print(f"\n❌ Permission denied (403)")
            print(f"   Error: {response.text}")
            print(f"\n💡 Solution: Check that your API key has READ permissions on the organization")
            return False
            
        elif response.status_code == 404:
            print(f"\n❌ Endpoint not found (404)")
            print(f"   Error: {response.text}")
            print(f"\n💡 Solution: Verify the CONSOLE_API_URL is correct")
            return False
            
        elif response.status_code == 401:
            print(f"\n❌ Authentication failed (401)")
            print(f"   Error: {response.text}")
            print(f"\n💡 Solution: Verify your SCALEWAY_API_KEY is valid")
            return False
            
        else:
            print(f"\n❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"\n❌ Request timeout (30s)")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

def main():
    print("=" * 70)
    print("Scaleway Console API - Connection Test")
    print("=" * 70)
    
    # Get org_id from command line if provided
    org_id = sys.argv[1] if len(sys.argv) > 1 else None
    
    success = test_api_connection(org_id)
    
    print("\n" + "=" * 70)
    if success:
        print("✅ API configuration is VALID")
        print("\nNext steps:")
        print("1. Edit database/organizations.csv with your real organization IDs")
        print("2. Import: python database/import_csv.py organizations.csv")
        print("3. Test cron job: python cron-match-incidents/main.py")
        sys.exit(0)
    else:
        print("❌ API configuration has ISSUES")
        print("\nTroubleshooting:")
        print("1. Verify SCALEWAY_API_KEY in .env file")
        print("2. Check API key has READ permissions on the organization")
        print("3. Test with a real organization_id: python test_api.py YOUR_ORG_ID")
        sys.exit(1)

if __name__ == '__main__':
    main()