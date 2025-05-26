import requests
import time

class SeedrAPI:
    def __init__(self, client_id="seedr_xbmc", client_secret=None):
        self.session = requests.Session()
        self.access_token = None
        self.client_id = client_id
        self.client_secret = client_secret

    def login_with_credentials(self, username, password):
        """Enhanced login with CSRF protection and proper session handling"""
        try:
            # Step 1: Get the login page to extract CSRF token and set session cookies
            print("Getting login page...")
            login_page = self.session.get(
                "https://www.seedr.cc/login",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
            )
            
            csrf_token = None
            # Try to extract CSRF token from various possible sources
            if 'csrf' in login_page.text.lower():
                import re
                # Look for CSRF token in meta tags or hidden inputs
                csrf_patterns = [
                    r'<meta name="csrf-token" content="([^"]+)"',
                    r'<input[^>]*name="[^"]*csrf[^"]*"[^>]*value="([^"]+)"',
                    r'"csrf_token":"([^"]+)"',
                    r'csrf["\s]*:["\s]*["\']([^"\']+)["\']'
                ]
                
                for pattern in csrf_patterns:
                    match = re.search(pattern, login_page.text, re.IGNORECASE)
                    if match:
                        csrf_token = match.group(1)
                        print(f"Found CSRF token: {csrf_token[:10]}...")
                        break
            
            # Step 2: Prepare login data
            login_data = {
                "username": username,
                "password": password
            }
            
            # Add CSRF token if found
            if csrf_token:
                login_data["_token"] = csrf_token
                login_data["csrf_token"] = csrf_token
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": "https://www.seedr.cc/login",
                "Origin": "https://www.seedr.cc"
            }
            
            # Step 3: Try multiple login endpoints
            login_endpoints = [
                "https://www.seedr.cc/auth/login",
                "https://www.seedr.cc/api/login", 
                "https://www.seedr.cc/login",
                "https://www.seedr.cc/api/auth/login"
            ]
            
            for endpoint in login_endpoints:
                print(f"Trying login endpoint: {endpoint}")
                
                response = self.session.post(endpoint, data=login_data, headers=headers)
                print(f"Login response status: {response.status_code}")
                
                # Check for successful login indicators
                if response.status_code in [200, 302]:
                    # Test if we can access protected content
                    test_response = self.session.get(
                        "https://www.seedr.cc/api/folder",
                        headers={"User-Agent": headers["User-Agent"]}
                    )
                    
                    print(f"API test response: {test_response.status_code}")
                    
                    if test_response.status_code == 200:
                        self.access_token = "session_auth"
                        print("Login successful!")
                        return self.access_token
                    elif test_response.status_code == 401:
                        print("API still returns 401, trying next endpoint...")
                        continue
                    else:
                        print(f"Unexpected API response: {test_response.status_code}")
                        # Try to parse response for more info
                        try:
                            api_data = test_response.json()
                            if "error" in api_data:
                                print(f"API Error: {api_data['error']}")
                        except:
                            pass
                
                # Check if login response contains error messages
                try:
                    if response.headers.get('content-type', '').startswith('application/json'):
                        resp_data = response.json()
                        if 'error' in resp_data:
                            print(f"Login error: {resp_data['error']}")
                        elif 'message' in resp_data:
                            print(f"Login message: {resp_data['message']}")
                except:
                    pass
            
            # Step 4: If direct login fails, try checking if we need email instead of username
            if "@" not in username:
                print("Trying with email format...")
                email_variants = [f"{username}@gmail.com", f"{username}@yahoo.com", f"{username}@hotmail.com"]
                
                for email in email_variants:
                    login_data_email = login_data.copy()
                    login_data_email["username"] = email
                    login_data_email["email"] = email
                    
                    for endpoint in login_endpoints:
                        response = self.session.post(endpoint, data=login_data_email, headers=headers)
                        if response.status_code in [200, 302]:
                            test_response = self.session.get("https://www.seedr.cc/api/folder")
                            if test_response.status_code == 200:
                                self.access_token = "session_auth"
                                return self.access_token
            
            raise Exception("All login attempts failed - check credentials or account status")
            
        except Exception as e:
            raise Exception(f"Login process failed: {str(e)}")

    def _try_api_key_login(self, username, password):
        """Alternative API-based login"""
        try:
            # Some services have separate API login endpoints
            api_endpoints = [
                "https://www.seedr.cc/api/v1/auth/login",
                "https://www.seedr.cc/api/v2/auth/login",
                "https://www.seedr.cc/rest/login"
            ]
            
            for endpoint in api_endpoints:
                try:
                    response = self.session.post(
                        endpoint,
                        json={"username": username, "password": password},
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        for key in ["token", "access_token", "api_key", "auth_token"]:
                            if key in data:
                                self.access_token = data[key]
                                return self.access_token
                except:
                    continue
            
            raise Exception("No API key found in responses")
            
        except Exception as e:
            raise Exception(f"API key login failed: {str(e)}")

    def get_device_code(self):
        """OAuth device code flow - may not be available"""
        raise Exception("OAuth device flow not available. Please use username/password authentication.")

    def poll_for_token(self, device_code, interval, timeout=1800):
        """OAuth token polling - not implemented"""
        raise Exception("OAuth not available. Please use username/password authentication.")

    # ========== API Methods (with proper headers) ==========
    def _auth_headers(self):
        """Get authentication headers"""
        if not self.access_token:
            raise Exception("Not authenticated")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # If we have a real token (not session_auth), add Authorization header
        if self.access_token != "session_auth":
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        return headers

    def add_torrent(self, magnet_link):
        """Add torrent via magnet link"""
        try:
            response = self.session.post(
                "https://www.seedr.cc/api/folder",
                headers=self._auth_headers(),
                data={
                    "func": "add_torrent",
                    "torrent_magnet": magnet_link
                }
            )
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to add torrent: {str(e)}")

    def list_contents(self, folder_id=None):
        """List folder contents"""
        try:
            params = {}
            if folder_id:
                params["id"] = folder_id
                
            response = self.session.get(
                "https://www.seedr.cc/api/folder",
                headers=self._auth_headers(),
                params=params
            )
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to list contents: {str(e)}")

    def delete_item(self, item_id):
        """Delete file or folder"""
        try:
            # Handle both single IDs and arrays
            if isinstance(item_id, list):
                delete_data = {
                    "func": "delete",
                }
                for i, id_val in enumerate(item_id):
                    delete_data[f"delete_arr[{i}]"] = id_val
            else:
                delete_data = {
                    "func": "delete",
                    "delete_arr[0]": item_id
                }
            
            response = self.session.post(
                "https://www.seedr.cc/api/folder",
                headers=self._auth_headers(),
                data=delete_data
            )
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to delete item: {str(e)}")

    def get_download_link(self, item_id):
        """Get download link for file or folder"""
        try:
            contents = self.list_contents()
            
            # Check files
            for file in contents.get("files", []):
                if str(file["id"]) == str(item_id):
                    return file.get("url")
            
            # Check folders (zip download)
            for folder in contents.get("folders", []):
                if str(folder["id"]) == str(item_id):
                    return folder.get("zip")
            
            return None
        except Exception as e:
            raise Exception(f"Failed to get download link: {str(e)}")

    def get_account_info(self):
        """Get account information"""
        try:
            response = self.session.get(
                "https://www.seedr.cc/api/settings",
                headers=self._auth_headers()
            )
            return response.json()
        except Exception as e:
            raise Exception(f"Failed to get account info: {str(e)}")
