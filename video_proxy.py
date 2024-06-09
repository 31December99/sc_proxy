# -*- coding: utf-8 -*-
import os
import m3u8

from queue import Queue
from proxy_test_04 import Proxy, MAX_THREAD


class Downloader:

    def __init__(self, playlist: m3u8, file_name: str, media: str, key=False):
        self.playlist: m3u8 = playlist
        self.key: bool = key
        self.queue = Queue()

        # Salva tutti i segments.uri in una coda safe-thread
        for uri in self.playlist.segments.uri:
            self.queue.put(uri)

        # Crea la cartella download in home/user
        home_folder = os.path.expanduser("~")
        self.file_path = os.path.join(home_folder, "SC_Downloads", file_name, media)


    def start(self) -> str:

        # Creo i threads: ogni thread legge dalla coda e processa un url.
        # Terminato di processare l'url , leggerà nuovamente dalla coda è cos' via.
        # Finchè tutti i thread non processeranno tutti gli url della coda
        threads = []

        # Ho a disposizione proxy pari a MAX_PROXY. Utilizzerò un gruppo di ip massimo pari a MAX_THREAD a ogni avvio
        for _ in range(MAX_THREAD):
            thread = Proxy(coda=self.queue, file_path=self.file_path, key=False)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        # Attendo la fine di tutto il processo
        self.queue.join()
        return self.file_path
