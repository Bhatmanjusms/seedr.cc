import requests
from .config import SEEDR_USERNAME, SEEDR_PASSWORD

class SeedrAPI:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.login()

    def login(self):
        resp = self.session.post("https://www.seedr.cc/oauth_test/token.php", data={
            "grant_type": "password",
            "client_id": "seedr_chrome",
            "type": "login",
            "username": SEEDR_USERNAME,
            "password": SEEDR_PASSWORD
        })
        if resp.ok:
            data = resp.json()
            self.auth_token = data.get("access_token")
        else:
            raise Exception("Seedr Login Failed")

    def add_torrent(self, magnet):
        resp = self.session.post("https://www.seedr.cc/api/folder", data={
            "access_token": self.auth_token,
            "func": "add_torrent",
            "torrent_magnet": magnet
        })
        return resp.json()

    def list_files(self):
        resp = self.session.get(f"https://www.seedr.cc/api/folder?access_token={self.auth_token}")
        return resp.json()

    def delete_file(self, file_id):
        resp = self.session.post("https://www.seedr.cc/api/folder", data={
            "access_token": self.auth_token,
            "func": "delete",
            "delete_file_arr[]": file_id
        })
        return resp.json()

    def get_download_link(self, file_id):
        # For files, the download link is in 'url'
        # For folders, Seedr provides 'zip' field for download
        files = self.list_files().get("folders", [])
        for folder in files:
            if folder["id"] == file_id:
                return folder.get("zip")
        files = self.list_files().get("files", [])
        for file in files:
            if file["id"] == file_id:
                return file.get("url")
        return None
