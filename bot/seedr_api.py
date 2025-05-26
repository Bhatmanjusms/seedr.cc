import requests
import time

class SeedrAPI:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None

    def get_device_code(self):
        response = self.session.post("https://www.seedr.cc/api/device/code", data={
            "client_id": "seedr_xbmc"
        })
        if response.ok:
            return response.json()
        else:
            raise Exception("Failed to obtain device code.")

    def poll_for_token(self, device_code, interval, timeout=1800):
        elapsed = 0
        while elapsed < timeout:
            time.sleep(interval)
            elapsed += interval
            response = self.session.post("https://www.seedr.cc/api/device/token", data={
                'client_id': 'seedr_xbmc',
                'device_code': device_code,
                'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
            })
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                return self.access_token
            elif response.status_code == 400:
                error = response.json().get("error")
                if error != "authorization_pending":
                    raise Exception(f"Authorization failed: {error}")
            else:
                raise Exception(f"Unexpected response: {response.status_code}")
        raise Exception("Authorization timed out.")

    def add_torrent(self, magnet_link):
        response = self.session.post("https://www.seedr.cc/api/folder", data={
            "access_token": self.access_token,
            "func": "add_torrent",
            "torrent_magnet": magnet_link
        })
        return response.json()

    def list_contents(self):
        response = self.session.get(f"https://www.seedr.cc/api/folder?access_token={self.access_token}")
        return response.json()

    def delete_item(self, item_id):
        response = self.session.post("https://www.seedr.cc/api/folder", data={
            "access_token": self.access_token,
            "func": "delete",
            "delete_file_arr[]": item_id
        })
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
