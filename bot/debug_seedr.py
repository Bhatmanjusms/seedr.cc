#!/usr/bin/env python3
"""
Debug script to test Seedr API endpoints
Run this to find the correct authentication method
"""

import requests
import json

def test_seedr_endpoints(username, password):
    """Test various Seedr API endpoints to find working authentication"""
    
    session = requests.Session()
    
    # Test endpoints to try
    login_endpoints = [
        ("POST", "https://www.seedr.cc/api/login", {"username": username, "password": password}),
        ("POST", "https://www.seedr.cc/auth/login", {"username": username, "password": password}),
        ("POST", "https://www.seedr.cc/login", {"username": username, "password": password}),
        ("POST", "https://www.seedr.cc/api/auth", {"username": username, "password": password}),
        ("POST", "https://www.seedr.cc/api/user/login", {"username": username, "password": password}),
    ]
    
    print("🔍 Testing Seedr API endpoints...")
    print(f"Username: {username}")
    print("-" * 50)
    
    for method, url, data in login_endpoints:
        try:
            print(f"\n🧪 Testing: {method} {url}")
            
            # Try JSON format
            response = session.request(
                method, 
                url, 
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"   JSON - Status: {response.status_code}")
            if response.text:
                try:
                    resp_json = response.json()
                    print(f"   JSON - Response: {json.dumps(resp_json, indent=2)[:200]}...")
                except:
                    print(f"   JSON - Response: {response.text[:200]}...")
            
            # Try form data format
            response2 = session.request(
                method,
                url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )
            
            print(f"   FORM - Status: {response2.status_code}")
            if response2.text:
                try:
                    resp_json = response2.json()
                    print(f"   FORM - Response: {json.dumps(resp_json, indent=2)[:200]}...")
                except:
                    print(f"   FORM - Response: {response2.text[:200]}...")
            
            # If login was successful, test API access
            if response.status_code == 200 or response2.status_code == 200:
                print("   ✅ Testing API access...")
                api_test = session.get("https://www.seedr.cc/api/folder")
                print(f"   API Test Status: {api_test.status_code}")
                
                if api_test.status_code == 200:
                    print("   🎉 SUCCESS! This endpoint works!")
                    return True
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    # Test if the site is accessible at all
    print("\n🌐 Testing basic site access...")
    try:
        homepage = session.get("https://www.seedr.cc", timeout=10)
        print(f"Homepage status: {homepage.status_code}")
        
        api_folder = session.get("https://www.seedr.cc/api/folder", timeout=10)
        print(f"API folder (no auth): {api_folder.status_code}")
        
    except Exception as e:
        print(f"❌ Site access error: {str(e)}")
    
    print("\n❌ No working authentication method found")
    return False

if __name__ == "__main__":
    print("Seedr API Endpoint Tester")
    print("=" * 30)
    
    # You can modify these or make them command line arguments
    test_username = input("Enter Seedr username: ").strip()
    test_password = input("Enter Seedr password: ").strip()
    
    if test_username and test_password:
        test_seedr_endpoints(test_username, test_password)
    else:
        print("❌ Username and password required")
