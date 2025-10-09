#!/usr/bin/env python3
"""
Test script to verify webapp functionality with the new remove_longlicks checkbox
"""

import requests
import time
import json

def test_webapp():
    """Test if webapp is accessible and working"""
    try:
        # Give webapp time to start
        time.sleep(2)
        
        # Test basic accessibility
        response = requests.get('http://127.0.0.1:8050/', timeout=10)
        print(f"✅ Webapp accessible: Status {response.status_code}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Webapp not accessible: {e}")
        return False

def test_lickcalc_parameters():
    """Test lickcalc function with remove_longlicks parameter"""
    try:
        from trompy import lickcalc
        
        # Test data
        test_licks = [0.1, 0.2, 0.8, 1.0, 1.2, 2.0, 2.5, 3.0, 3.8, 4.0]
        
        # Test remove_longlicks=False (default)
        result1 = lickcalc(test_licks, burstThreshold=0.5, minburstlength=1, 
                          longlickThreshold=0.3, remove_longlicks=False)
        print(f"✅ lickcalc with remove_longlicks=False: {result1['total']} total licks")
        
        # Test remove_longlicks=True
        result2 = lickcalc(test_licks, burstThreshold=0.5, minburstlength=1, 
                          longlickThreshold=0.3, remove_longlicks=True)
        print(f"✅ lickcalc with remove_longlicks=True: {result2['total']} total licks")
        
        # Test with various combinations
        result3 = lickcalc(test_licks, remove_longlicks=True)
        print(f"✅ lickcalc with minimal parameters + remove_longlicks=True: {result3['total']} total licks")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing lickcalc parameters: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_import():
    """Test if app module imports correctly"""
    try:
        import app
        print("✅ App module imports successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing app module: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing lickcalc webapp functionality...\n")
    
    # Test 1: App import
    print("1. Testing app module import:")
    test1_passed = test_app_import()
    
    # Test 2: lickcalc parameters
    print("\n2. Testing lickcalc parameters:")
    test2_passed = test_lickcalc_parameters()
    
    # Test 3: Webapp accessibility
    print("\n3. Testing webapp accessibility:")
    test3_passed = test_webapp()
    
    # Summary
    print(f"\n📊 Test Results:")
    print(f"   App Import: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"   lickcalc Parameters: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    print(f"   Webapp Accessibility: {'✅ PASS' if test3_passed else '❌ FAIL'}")
    
    if all([test1_passed, test2_passed, test3_passed]):
        print("\n🎉 All tests passed! The webapp should be working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")