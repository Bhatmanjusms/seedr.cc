import requests
import time

class SeedrAPI:
    def __init__(self, client_id="seedr_xbmc", client_secret=None):
        self.session = requests.Session()
        self.access_token = None
        self.client_id = client_id
        self.client_secret = client_secret  # Add if Seedr requires it

    def get_device_code(self):
        # Updated OAuth device code endpoint
        response = self.session.post(
            "https://www.seedr.cc/oauth/device/code",
            data={
                "client_id": self.client_id,
                # Include "client_secret" here if required by Seedr
            }
        )
        if response.ok:
            return response.json()
        else:
            raise Exception(f"Device code error: {response.status_code} - {response.text}")

    def poll_for_token(self, device_code, interval, timeout=1800):
        # Updated OAuth token endpoint
        token_url = "https://www.seedr.cc/oauth/token"
        elapsed = 0

        while elapsed < timeout:
            try:
                data = {
                    "client_id": self.client_id,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                }
                # Add client_secret if required
                if self.client_secret:
                    data["client_secret"] = self.client_secret

                response = self.session.post(token_url, data=data)
                response_data = response.json()

                if response.status_code == 200:
                    self.access_token = response_data.get("access_token")
                    return self.access_token
                elif response_data.get("error") in ["authorization_pending", "slow_down"]:
                    time.sleep(interval)
                    elapsed += interval
                else:
                    raise Exception(f"Auth error: {response_data.get('error')}")
            except Exception as e:
                raise Exception(f"Token poll failed: {str(e)}")

        raise Exception("Authorization timeout")

    # ========== API Methods (with proper headers) ==========
    def _auth_headers(self):
        if not self.access_token:
            raise Exception("Not authenticated")
        return {"Authorization": f"Bearer {self.access_token}"}

    def add_torrent(self, magnet_link):
        response = self.session.post(
            "https://www.seedr.cc/api/folder",
            headers=self._auth_headers(),
            data={
                "func": "add_torrent",
                "torrent_magnet": magnet_link
            }
        )
        return response.json()

    def list_contents(self):
        response = self.session.get(
            "https://www.seedr.cc/api/folder",
            headers=self._auth_headers()
        )
        return response.json()

    def delete_item(self, item_id):
        response = self.session.post(
            "https://www.seedr.cc/api/folder",
            headers=self._auth_headers(),
            data={
                "func": "delete",
                "delete_file_arr[]": item_id
            }
        )
        return response.json()

    def get_download_link(self, item_id):
        contents = self.list_contents()
        for file in contents.get("files", []):
            if str(file["id"]) == str(item_id):
                return file.get("url")
        for folder in contents.get("folders", []):
            if str(folder["id"]) == str(item_id):
                return folder.get("zip")
        return None
