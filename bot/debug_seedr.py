#!/usr/bin/env python3
"""
Enhanced debug script for Seedr API authentication
"""

import requests
import json
import re

def extract_csrf_token(html_content):
    """Extract CSRF token from HTML"""
    csrf_patterns = [
        r'<meta name="csrf-token" content="([^"]+)"',
        r'<input[^>]*name="[^"]*csrf[^"]*"[^>]*value="([^"]+)"',
        r'"csrf_token":"([^"]+)"',
        r'csrf["\s]*:["\s]*["\']([^"\']+)["\']',
        r'_token["\s]*:["\s]*["\']([^"\']+)["\']'
    ]
    
    for pattern in csrf_patterns:
        match = re.search(pattern, html_content, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

def test_seedr_comprehensive(username, password):
    """Comprehensive Seedr API testing"""
    
    session = requests.Session()
    
    print("🔍 Comprehensive Seedr API Test")
    print(f"Username: {username}")
    print("=" * 60)
    
    # Step 1: Test basic connectivity
    print("\n1️⃣ Testing basic connectivity...")
    try:
        homepage = session.get("https://www.seedr.cc", timeout=10)
        print(f"   Homepage: {homepage.status_code}")
        
        login_page = session.get("https://www.seedr.cc/login", timeout=10)
        print(f"   Login page: {login_page.status_code}")
        
        # Extract CSRF token
        csrf_token = None
        if login_page.status_code == 200:
            csrf_token = extract_csrf_token(login_page.text)
            if csrf_token:
                print(f"   CSRF Token found: {csrf_token[:10]}...")
            else:
                print("   No CSRF token found")
        
    except Exception as e:
        print(f"   ❌ Connectivity error: {str(e)}")
        return False
    
    # Step 2: Test login endpoints
    print("\n2️⃣ Testing login endpoints...")
    
    # Prepare different login data formats
    login_formats = []
    
    # Basic format
    basic_data = {"username": username, "password": password}
    if csrf_token:
        basic_data["_token"] = csrf_token
        basic_data["csrf_token"] = csrf_token
    login_formats.append(("Basic", basic_data))
    
    # Email format (if username doesn't contain @)
    if "@" not in username:
        email_data = {"email": username, "password": password}
        if csrf_token:
            email_data["_token"] = csrf_token
        login_formats.append(("Email field", email_data))
    
    # Alternative field names
    alt_data = {"user": username, "pass": password}
    if csrf_token:
        alt_data["_token"] = csrf_token
    login_formats.append(("Alternative fields", alt_data))
    
    endpoints = [
        "https://www.seedr.cc/auth/login",
        "https://www.seedr.cc/api/login",
        "https://www.seedr.cc/login",
        "https://www.seedr.cc/api/auth/login",
        "https://www.seedr.cc/api/v1/auth/login"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.seedr.cc/login",
        "Origin": "https://www.seedr.cc"
    }
    
    for endpoint in endpoints:
        print(f"\n   Testing: {endpoint}")
        
        for format_name, data in login_formats:
            try:
                # Try form data
                form_headers = headers.copy()
                form_headers["Content-Type"] = "application/x-www-form-urlencoded"
                
                response = session.post(endpoint, data=data, headers=form_headers, timeout=10)
                print(f"     {format_name} (form): {response.status_code}")
                
                if response.status_code in [200, 302]:
                    # Test API access
                    api_test = session.get("https://www.seedr.cc/api/folder", headers=headers)
                    print(f"     API test: {api_test.status_code}")
                    
                    if api_test.status_code == 200:
                        print(f"     🎉 SUCCESS with {format_name} at {endpoint}!")
                        try:
                            api_data = api_test.json()
                            print(f"     API Response: {json.dumps(api_data, indent=2)[:200]}...")
                        except:
                            print(f"     API Response: {api_test.text[:200]}...")
                        return True
                    elif api_test.status_code == 401:
                        print(f"     Still 401 after login")
                    
                    # Check response for clues
                    if response.headers.get('content-type', '').startswith('application/json'):
                        try:
                            resp_json = response.json()
                            print(f"     Response: {resp_json}")
                        except:
                            pass
                
                # Try JSON format
                json_headers = headers.copy()
                json_headers["Content-Type"] = "application/json"
                
                response2 = session.post(endpoint, json=data, headers=json_headers, timeout=10)
                print(f"     {format_name} (json): {response2.status_code}")
                
                if response2.status_code in [200, 302]:
                    api_test = session.get("https://www.seedr.cc/api/folder", headers=headers)
                    if api_test.status_code == 200:
                        print(f"     🎉 SUCCESS with {format_name} JSON at {endpoint}!")
                        return True
                
            except Exception as e:
                print(f"     ❌ Error with {format_name}: {str(e)}")
    
    # Step 3: Check for specific error messages
    print("\n3️⃣ Analyzing error responses...")
    
    try:
        # Try a simple login to get error details
        simple_login = session.post(
            "https://www.seedr.cc/auth/login",
            data={"username": username, "password": password},
            headers=headers
        )
        
        print(f"   Status: {simple_login.status_code}")
        print(f"   Headers: {dict(simple_login.headers)}")
        
        if simple_login.text:
            print(f"   Response preview: {simple_login.text[:300]}...")
            
            # Look for specific error messages
            error_indicators = [
                "invalid", "incorrect", "wrong", "error", "failed",
                "banned", "suspended", "disabled", "captcha"
            ]
            
            for indicator in error_indicators:
                if indicator.lower() in simple_login.text.lower():
                    print(f"   ⚠️  Found '{indicator}' in response")
        
    except Exception as e:
        print(f"   Error analysis failed: {str(e)}")
    
    # Step 4: Alternative suggestions
    print("\n4️⃣ Troubleshooting suggestions:")
    print("   • Verify your Seedr.cc username and password on the website")
    print("   • Check if your account requires email verification")
    print("   • Try logging in through a web browser first")
    print("   • Check if Seedr requires 2FA or captcha")
    print("   • Verify your account isn't suspended or limited")
    
    return False

if __name__ == "__main__":
    print("Enhanced Seedr API Debug Tool")
    print("=" * 40)
    
    test_username = input("Enter Seedr username/email: ").strip()
    test_password = input("Enter Seedr password: ").strip()
    
    if test_username and test_password:
        success = test_seedr_comprehensive(test_username, test_password)
        if not success:
            print("\n❌ No working authentication method found")
            print("\n💡 Next steps:")
            print("1. Verify credentials work on https://www.seedr.cc")
            print("2. Check if account needs verification")
            print("3. Look for official Seedr API documentation")
    else:
        print("❌ Username and password required")
