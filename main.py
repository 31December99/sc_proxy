# -*- coding: utf-8 -*-
import asyncio
import time
import m3u8
import sessions
from downloader import Downloader
from scraper import page, build, utility
from sessions import Agent


async def start():
    # Ottengo l'ID del video dalla pagina Watch
    start_timer = time.time()
    playlist_audio: m3u8 = None
    playlist_video: m3u8 = None
    playlist_sub: m3u8 = None

    headers = Agent.headers(host="streamingcommunity.foo",
                            refer='www.google.com',
                            document='navigate')

    async with sessions.MyHttp(headers=headers) as my_http:

        print("Digita il numero di watch esempio: https://streamingcommunity.foo/watch/4020 -> 4020")
        watch = input("-> ")
        if not watch.isdigit():
            print("Devi digitare solo un numero..")
            return
        watch_url = f"https://streamingcommunity.foo/watch/{watch}"
        response = await my_http.get(watch_url)
        read = await response.read()
        scws_id = page.scws(read)  # Ottiene il video ID
        if scws_id == 0:
            print(f"Non trovo il video che hai scelto -> {watch_url}")
            return

    # Ottengo la playlist master e le playlist per resolution disponibili
    headers = Agent.headers(host="vixcloud.co",
                            refer='streamingcommunity.foo',
                            document='empty', mode='corse')

    async with sessions.MyHttp(headers=headers) as my_http:
        master_playlist_url = f"https://vixcloud.co/playlist/{scws_id}"  # Ricostruisci la playlist master
        response = await my_http.get(master_playlist_url)  # Ottiene la playlist master
        master_playlist_data = await response.text()

        # Ottengo filename e name da /video/
        video_url = f"https://vixcloud.co/video/{scws_id}"  # Ottiene informazioni sul video
        response = await my_http.get(video_url)
        video_data = await response.text()
        media = build.data(master_playlist_data, video_data)  # Costruisce un oggetto per video,audio,subtitle
        media_file_name = media.data.video['filename']
        media_name = media.data.video['name']
        # Non sempre il file_name è disponibile
        file_name = media_name if not media_file_name else media_file_name
        print(f"[FILE NAME] {file_name}")

        # Tento il recupero della playlist 1080p todo: Forzato a 720p. Per 1080 serve token
        url_1080p = f"https://vixcloud.co/playlist/{scws_id}?type=video&rendition=720p"
        response = await my_http.get(url_1080p)
        _1080p_data = await response.text()
        playlist_1080p = m3u8.loads(_1080p_data)
        if playlist_1080p.segments.uri:
            playlist_video_url = url_1080p
        else:
            # Altrimenti scelgo la migliore tra quelle disponibili nella playlist master
            playlist_video_url = utility.best_resolution(media=media.data.video['stream_info'])
        response = await my_http.get(playlist_video_url)
        playlist_video_data = await response.text()
        playlist_video = m3u8.loads(playlist_video_data)
        key = True if playlist_video.keys[0] else False
        key_message = 'Encrypted' if key else ''
        print(f"[VIDEO DATA {key_message}] {playlist_video_url}")

        if media.data.audio:
            response = await my_http.get(media.data.audio['uri'])
            playlist_audio_data = await response.text()
            playlist_audio = m3u8.loads(playlist_audio_data)
            print(f"[AUDIO DATA] Presente {media.data.audio['uri']}")

        if media.data.subtitle:
            response = await my_http.get(media.data.subtitle['uri'])
            playlist_sub_data = await response.text()
            playlist_sub = m3u8.loads(playlist_sub_data)
            print(f"[SUB DATA]   Presente {playlist_sub.segments.uri}")

    video = Downloader(playlist=playlist_video, file_name=file_name, media='VIDEO', key=key)
    video.start()
    video.close()

    audio = Downloader(playlist=playlist_audio, file_name=file_name, media='AUDIO', key=key)
    audio.start()
    audio.close()

    sub = Downloader(playlist=playlist_sub, file_name=file_name, media='SUB')
    sub.start()
    sub.close()

    print(f'[COMPLETATO] {time.time() - start_timer} secs\n')


if __name__ == "__main__":
    asyncio.run(start())
