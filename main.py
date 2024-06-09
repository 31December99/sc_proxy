# -*- coding: utf-8 -*-
import asyncio
import m3u8
import requests
from video_proxy import Downloader


async def start():
    response = requests.get(
        "https://vixcloud.co/playlist/60086?type=video&rendition=720p&token=qqzfHlMljnyiGO4HbZ5crQ&edge=sc-u7-01")
    read = response.text
    playlist = m3u8.loads(read)

    video = Downloader(playlist=playlist, file_name="demo", media='VIDEO', key=True)
    video.start()


asyncio.run(start())
