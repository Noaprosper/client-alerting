#!/usr/bin/env python3
"""
Test script to verify Console API locality parameter format
Run this to find the correct locality IDs for your organization
"""

import os
import requests
import json

# Configuration - Replace with your actual values
SCALEWAY_API_KEY = os.getenv('SCALEWAY_API_KEY', 'scw_xxx')  # Set via: export SCALEWAY_API_KEY=scw_xxx
ORGANIZATION_ID = os.getenv('SCALEWAY_ORG_ID', 'b9661e0c-15bf-43bd-b8ee-11e3e1373f92')
CONSOLE_API_URL = 'https://api.scaleway.com/resource-private/v1alpha1'

def test_locality_format(locality_value, description):
    """Test a specific locality format"""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Locality value: {locality_value}")
    print(f"{'='*60}")
    
    try:
        headers = {'X-Auth-Token': SCALEWAY_API_KEY, 'Content-Type': 'application/json'}
        
        # Test with single locality
        params = {
            'organization_id': ORGANIZATION_ID,
            'products': [1],  # instance
            'localities': locality_value,
            'strategy': 1
        }
        
        response = requests.get(
            f"{CONSOLE_API_URL}/filtered-counters",
            headers=headers,
            params=params,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ SUCCESS: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"✗ ERROR: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ EXCEPTION: {e}")
        return False


def main():
    print("Scaleway Console API - Locality Format Tester")
    print(f"Organization ID: {ORGANIZATION_ID}")
    print(f"API Key configured: {'Yes' if SCALEWAY_API_KEY and 'xxx' not in SCALEWAY_API_KEY else 'No - Please set SCALEWAY_API_KEY'}")
    
    if not SCALEWAY_API_KEY or 'xxx' in SCALEWAY_API_KEY:
        print("\n⚠️  Please set your Scaleway API key:")
        print("   export SCALEWAY_API_KEY=scw_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        return
    
    # Test different locality formats
    tests = [
        # Format: (value, description)
        ([1], "Locality ID as array: [1]"),
        (1, "Locality ID as integer: 1"),
        ('1', "Locality ID as string: '1'"),
        ('fr-par-1', "Zone name: 'fr-par-1'"),
        ('PAR1', "Short zone name: 'PAR1'"),
        ([1, 2, 3], "Multiple localities as array: [1, 2, 3]"),
        ('1,2,3', "Multiple localities as comma-separated string: '1,2,3'"),
    ]
    
    results = []
    for locality_value, description in tests:
        success = test_locality_format(locality_value, description)
        results.append((description, success))
    
    # Print summary
    print(f"\n\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for description, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {description}")
    
    # Count successes
    passed = sum(1 for _, s in results if s)
    print(f"\n{passed}/{len(results)} tests passed")
    
    if passed > 0:
        print("\n✓ Use the working format in your ZONE_TO_LOCALITY mapping in main.py")
    else:
        print("\n⚠️  No format worked - check your API key and organization ID")


if __name__ == '__main__':
    main()