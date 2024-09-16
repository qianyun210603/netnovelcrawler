import requests
from urllib.parse import urlparse


class HttpEngine:

    def __init__(self, start_page: str):
        self.session = requests.Session()
        parsed = urlparse(start_page)
        self.base_url = f"{parsed.scheme}://{parsed.netloc}"

    def login(self, login_info: dict, login_page: str):
        pass
