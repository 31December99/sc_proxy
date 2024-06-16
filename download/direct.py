# -*- coding: utf-8 -*-
import os
import warnings
import requests
from sessions import Agent
from urllib.parse import urlparse

""" SSL off """
warnings.filterwarnings('ignore', message='Unverified HTTPS request')


class Direct:
    """
        Classe generica per scaricare un file
        todo: rivedere

    """
    session = requests.Session()

    def __init__(self, file_name: str, media: str):
        self.media: str = media
        self.headers = None
        self.file_name: str = file_name
        self.user_agent = None
        self.results = {}
        self.next_headers()
        # Crea la cartella download in home/user
        home_folder = os.path.expanduser("~")
        self.file_path = os.path.join(home_folder, "SC_Downloads", self.file_name, self.media)

        if not os.path.exists(self.file_path):
            os.makedirs(self.file_path)

    def next_headers(self):
        # L'ordine degli headers è importante
        self.headers = Agent.headers(host="vixcloud.co",
                                     refer='streamingcommunity.foo',
                                     document='empty', mode='corse')

    def download_url(self, url) -> str:

        parsed_uri = urlparse(url)
        # aggiorno l'header con un nuovo host che corrisponde al net-loc dell'url scws
        self.headers['host'] = parsed_uri.netloc
        filename = parsed_uri.path.split('/')[-1]
        try:
            response = Direct.session.get(url, headers=self.headers, timeout=30, verify=False)
            if response.status_code == 200:
                content = response.content
                # print(f"[{response.status_code}] -> {url}")
                self.write_to_file(content)
                return self.file_path
            else:
                print(f"[{response.status_code}] -> {url}")
        except Exception as e:
            print(f"[ * EXCPT * ] -> {url}")

    def write_to_file(self, data: bytes):
        try:
            with open(os.path.join(self.file_path, self.file_name), 'wb') as file:
                if data is not None:
                    file.write(data)
        except Exception as e:
            print(f"Error: {e}")
