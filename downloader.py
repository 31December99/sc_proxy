# -*- coding: utf-8 -*-
import os
import m3u8

from queue import Queue
from proxy import Proxy, MAX_THREAD


class Downloader:

    def __init__(self, playlist: m3u8, file_name: str, media: str, key=False):
        self.playlist: m3u8 = playlist
        self.key: bool = key
        self.queue: Queue = Queue()
        self.threads: list = []
        self.file_name: str = file_name
        self.media: str = media

    def start(self):

        # Ritorna se playlist non disponibile
        if not self.playlist:
            return

        # Crea la cartella download in home/user
        home_folder = os.path.expanduser("~")
        file_path = os.path.join(home_folder, "SC_Downloads", self.file_name, self.media)

        # Salva tutti i segments.uri in una coda safe-thread
        for uri in self.playlist.segments.uri:
            self.queue.put(uri)

        # Creo i threads: ogni thread legge dalla coda e processa un url.
        # Terminato di processare l'url , leggerà nuovamente dalla coda è cos' via.
        # Finchè tutti i thread non processeranno tutti gli url della coda
        threads = []
        print()

        # Ho a disposizione proxy pari a MAX_PROXY. Utilizzerò un gruppo di ip massimo pari a MAX_THREAD a ogni avvio
        for _ in range(MAX_THREAD):
            thread = Proxy(coda=self.queue, file_path=file_path, key=self.key)
            thread.start()
            self.threads.append(thread)

        for thread in threads:
            thread.join()

        # Attendo la fine di tutto il processo
        self.queue.join()
        return file_path

    def close(self):
        for thread in self.threads:
            thread.stop_writing()
