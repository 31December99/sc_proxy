import binascii
import os
import re
import threading
import random
import time
import requests
import warnings
import concurrent.futures
import queue
from Crypto.Cipher import AES
from typing import Dict
from user_agents import parse
from proxies import ips, user_agents
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
        self.start_timer = time.time()
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

    # Experimental header. Da aggiungere agli header
    def ua_to_ch(self, ua_string: str) -> Dict[str, str]:
        parsed = parse(ua_string)
        if parsed.browser.family == "Chrome":
            major_version = parsed.browser.version[0]
            return {
                "sec-ch-ua": f'"Not A;Brand";v="{major_version}", "Chromium";v="{major_version}", "Google Chrome";v="{major_version}"',
                "sec-ch-ua-mobile": f"?{int(parsed.is_mobile)}",
                "sec-ch-ua-platform": parsed.get_os().split()[0],
            }
        else:
            return {}

    def next_headers(self):
        # L'ordine degli headers è importante
        self.headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep - alive',
            "Upgrade-Insecure-Requests": "1",
            'Host': '',
            'Origin': 'https://vixcloud.co',
            'Referer': 'https://streamingcommunity.foo/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        }
        # Experimental header
        ua_to_ch = self.ua_to_ch(self.user_agent)
        if ua_to_ch:
            self.headers.update({'sec-ch-ua-mobile': ua_to_ch['sec-ch-ua-mobile']})
            self.headers.update({'sec-ch-ua-platform': ua_to_ch['sec-ch-ua-platform']})
            self.headers.update({'sec-ch-ua': ua_to_ch['sec-ch-ua']})

    def next_proxy(self):
        """
        Soltanto un thread per volta può accedere a next_proxy()
        Ottengo un nuovo ip proxy
        Aggiorno l'header con un nuovo user-agent
        """

        with Proxy.proxy_lock:
            Proxy.proxy_index = (Proxy.proxy_index + 1) % len(ips)
            self.proxy_ip = ips[Proxy.proxy_index]
            if not TEST_HEADER:
                self.user_agent = random.choice(user_agents)
            else:
                self.user_agent = user_agents[1]

    def run(self):
        """ threading.Thread"""
        while not self.queue.empty():
            url = self.queue.get()
            try:
                content, ts_filename = self.download_url(url)
                self.write_queue.put((content, ts_filename))
            finally:
                self.queue.task_done()

    def download_url(self, url):
        """ creo un nuovo url con il nuovo proxy. Timeout 30 secondi"""

        proxy_url = f"http://{self.proxy_ip}"
        try:
            parsed_uri = urlparse(url)
            # aggiorno l'header con un nuovo host che corrisponde al net-loc dell'url scws
            self.headers['host'] = parsed_uri.netloc

            pattern = r'/([^/]+\.ts)'
            match = re.search(pattern, url)
            if match:
                ts_filename = match.group(1)
            else:
                ts_filename = "error no file name ts"

            if not TEST_HEADER:
                response = Proxy.session.get(url, headers=self.headers, proxies={'http': proxy_url, 'https': proxy_url},
                                             timeout=30, verify=False)
            else:
                response = Proxy.session.get(url, headers=self.headers, timeout=30, verify=False)

            if response.status_code == 200:
                content = response.content
                print(f"[{response.status_code}] -> {url}")
                return content, ts_filename
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
                    self.write_to_file_async(segment_content, ts_filename)
            except queue.Empty:
                pass
            finally:
                threading.Event().wait(0.1)

    def write_to_file_async(self, data: bytes, ts_filename: str):
        try:
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
        print(f'[COMPLETATO] {time.time() - self.start_timer} secs\n')
        self.stop_event.set()
        self.executor.shutdown(wait=True)
