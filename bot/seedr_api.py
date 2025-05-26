import requests
import time

class SeedrAPI:
    def __init__(self, client_id="seedr_xbmc", client_secret=None):
        self.session = requests.Session()
        self.access_token = None
        self.client_id = client_id
        self.client_secret = client_secret

    def get_device_code(self):
        """Get device code using POST method"""
        try:
            data = {
                "client_id": self.client_id,
                "response_type": "device_code"
            }
            if self.client_secret:
                data["client_secret"] = self.client_secret
            
            response = self.session.post(
                "https://www.seedr.cc/oauth/device/code",
                data=data
            )
            
            if response.ok:
                return response.json()
            else:
                raise Exception(f"Device code error: {response.status_code} - {response.text}")
                
        except Exception as e:
            # If device code endpoint fails, try alternative approach
            raise Exception(f"Device code request failed: {str(e)}")

    def poll_for_token(self, device_code, interval, timeout=1800):
        """Poll for access token"""
        token_url = "https://www.seedr.cc/oauth/token"
        elapsed = 0

        while elapsed < timeout:
            try:
                data = {
                    "client_id": self.client_id,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                }
                if self.client_secret:
                    data["client_secret"] = self.client_secret

                response = self.session.post(token_url, data=data)
                
                if response.status_code == 200:
                    response_data = response.json()
                    self.access_token = response_data.get("access_token")
                    return self.access_token
                elif response.status_code == 400:
                    response_data = response.json()
                    error = response_data.get("error")
                    if error in ["authorization_pending", "slow_down"]:
                        time.sleep(interval)
                        elapsed += interval
                    else:
                        raise Exception(f"Auth error: {error}")
                else:
                    raise Exception(f"Token request failed: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                raise Exception(f"Network error during token poll: {str(e)}")

        raise Exception("Authorization timeout")

    # Alternative authentication method using username/password
    def login_with_credentials(self, username, password):
        """Alternative login method using username/password"""
        try:
            login_data = {
                "username": username,
                "password": password,
                "grant_type": "password",
                "client_id": self.client_id
            }
            
            response = self.session.post(
                "https://www.seedr.cc/oauth/token",
                data=login_data
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                return self.access_token
            else:
                raise Exception(f"Login failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            raise Exception(f"Credential login failed: {str(e)}")

    # ========== API Methods (with proper headers) ==========
    def _auth_headers(self):
        if not self.access_token:
            raise Exception("Not authenticated")
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

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
