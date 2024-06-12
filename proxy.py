# -*- coding: utf-8 -*-

import binascii
import os
import threading
import random
import warnings
import concurrent.futures
import queue
import requests
from Crypto.Cipher import AES
from sessions import ips
from sessions import Agent
from urllib.parse import urlparse

iv = binascii.unhexlify('43A6D967D5C17290D98322F5C8F6660B')
aes_key = b'\xb2\x07\x82\xcb\xc3*xC\xe7i\x1dU\x95\x0c\x9aj'

""" SSL off """
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

MAX_PROXY = 100
MAX_THREAD = 25
MAX_INIT_RND = MAX_PROXY - MAX_THREAD
# Test header in locale 127.0.0.1 con test_headers.py
TEST_HEADER = False
proxy_queue = queue.Queue()


class Proxy(threading.Thread):
    """
    - Ogni proxy un thread
    - cambia agente per ogni ip
    - cambio host in header per ogni ip
    - Processa il prossimo url in run()
    - A ogni avvio scelgo un gruppo di ip casuale:
      esempio:
        init_ = 33 -> gruppo ip = 33 + MAX_THREAD.
        Ovvero un gruppo di ip MAX_THREAD creato a partire dall'ip n° init_
    """

    proxy_lock = threading.Lock()
    proxy_index = random.randrange(0, MAX_INIT_RND)
    session = requests.Session()

    def __init__(self, coda: queue, file_path: str, key: bool):
        super(Proxy, self).__init__()
        self.headers = None
        self.queue = coda
        self.key: bool = key
        self.folder = file_path
        self.user_agent = None
        self.proxy_ip = None
        self.stop_event = threading.Event()
        self.write_queue: queue = queue.Queue()
        self.executor: concurrent = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        threading.Thread(target=self.process_write_queue, daemon=True).start()
        self.results = {}
        self.next_proxy()
        self.next_headers()

        if not os.path.exists(file_path):
            os.makedirs(file_path)

    def next_headers(self):
        # L'ordine degli headers è importante
        self.headers = Agent.headers(host="vixcloud.co",
                                     refer='streamingcommunity.foo',
                                     document='empty', mode='corse')

    def next_proxy(self):
        """
        Soltanto un thread per volta può accedere a next_proxy()
        Ottengo un nuovo ip proxy
        Aggiorno l'header con un nuovo user-agent
        """

        with Proxy.proxy_lock:
            Proxy.proxy_index = (Proxy.proxy_index + 1) % len(ips)
            self.proxy_ip = ips[Proxy.proxy_index]
            self.next_headers()

    def run(self):
        """ threading.Thread"""
        while not self.queue.empty():
            url = self.queue.get()
            try:
                content, segment_filename = self.download_url(url)
                self.write_queue.put((content, segment_filename))
            finally:
                self.queue.task_done()

    def download_url(self, url):
        """ creo un nuovo url con il nuovo proxy. Timeout 30 secondi"""

        proxy_url = f"http://{self.proxy_ip}"
        parsed_uri = urlparse(url)
        # aggiorno l'header con un nuovo host che corrisponde al net-loc dell'url scws
        self.headers['host'] = parsed_uri.netloc
        filename = parsed_uri.path.split('/')[-1]


        try:
            response = Proxy.session.get(url, headers=self.headers, proxies={'http': proxy_url, 'https': proxy_url},
                                         timeout=30, verify=False)

            if response.status_code == 200:
                content = response.content
                # print(f"[{response.status_code}] -> {url} {proxy_url}")
                return content, filename
            else:
                print(f"[{response.status_code}] {proxy_url} -> {url}")
                return None
        except Exception as e:
            print(f"[EXCPT] {proxy_url} -> {url} {e}")
            return None

    def decrypt_cbc(self, data: bytes) -> bytes:
        cipher = AES.new(aes_key, AES.MODE_CBC, iv)
        try:
            dec = cipher.decrypt(data)
            return dec
        except ValueError as e:
            print(f"[Decrypt_CBC] {e}")
            input("Decrypt error")
            return b''

    def process_write_queue(self):
        while not self.stop_event.is_set():
            try:
                while not self.write_queue.empty():
                    segment_content, ts_filename = self.write_queue.get()
                    if segment_content:
                        self.write_to_file(segment_content, ts_filename)
            except queue.Empty:
                pass
            finally:
                threading.Event().wait(1)

    def write_to_file(self, data: bytes, ts_filename: str):
        try:
            print(self.folder, ts_filename)
            with open(os.path.join(self.folder, ts_filename), 'wb') as file:
                if data is not None:
                    _data = self.decrypt_cbc(data=data) if self.key else data
                    file.write(_data)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.write_queue.task_done()
            if not self.write_queue.empty():
                self.executor.submit(self.process_write_queue)

    def stop_writing(self):
        # Attende la fine della coda
        self.write_queue.join()
        # fine processo write_queue
        self.stop_event.set()
        # chiude thread
        self.executor.shutdown(wait=True)
