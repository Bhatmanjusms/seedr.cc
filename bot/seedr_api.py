import requests
import time

class SeedrAPI:
    def __init__(self, client_id="seedr_xbmc", client_secret=None):
        self.session = requests.Session()
        self.access_token = None
        self.client_id = client_id
        self.client_secret = client_secret

    def login_with_credentials(self, username, password):
        """Login using username and password via session-based auth"""
        try:
            # First, get the login page to extract any CSRF tokens if needed
            login_page = self.session.get("https://www.seedr.cc/login")
            
            # Attempt login with form data
            login_data = {
                "username": username,
                "password": password
            }
            
            # Try the login endpoint
            response = self.session.post(
                "https://www.seedr.cc/auth/login",
                data=login_data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
            
            # Check if login was successful by trying to access a protected endpoint
            test_response = self.session.get("https://www.seedr.cc/api/folder")
            
            if test_response.status_code == 200:
                # Session-based authentication successful
                self.access_token = "session_auth"  # Placeholder since we're using cookies
                return self.access_token
            else:
                raise Exception(f"Login verification failed: {test_response.status_code}")
                
        except Exception as e:
            # Try alternative login method
            try:
                return self._try_api_key_login(username, password)
            except:
                raise Exception(f"All login methods failed: {str(e)}")

    def _try_api_key_login(self, username, password):
        """Try logging in and extracting API key from response"""
        try:
            # Some services provide API keys after login
            login_response = self.session.post(
                "https://www.seedr.cc/api/login",
                json={
                    "username": username,
                    "password": password
                },
                headers={
                    "Content-Type": "application/json"
                }
            )
            
            if login_response.status_code == 200:
                data = login_response.json()
                if "token" in data:
                    self.access_token = data["token"]
                    return self.access_token
                elif "api_key" in data:
                    self.access_token = data["api_key"]
                    return self.access_token
            
            raise Exception(f"API key login failed: {login_response.status_code}")
            
        except Exception as e:
            raise Exception(f"API key extraction failed: {str(e)}")

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
