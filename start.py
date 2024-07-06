# -*- coding: utf-8 -*-
import asyncio
import time
import m3u8
import sessions
from download import Downloader, Direct, merge, join
from scraper import build, utility
from sessions import Agent



async def start():
    # Timer
    start_timer = time.time()

    scws_id = input("Digita il video ID: -> ")
    if not scws_id.isdigit():
        return

    # Creo un nuovo Agent
    headers = Agent.headers(host="vixcloud.co",
                            refer='streamingcommunity.boston',
                            document='empty', mode='cors', secfetchSite='cross-site')

    # Inizio una nuova sessione http con il nuovo Agent
    async with sessions.MyHttp(headers=headers) as my_http:

        # Ottengo la playlist master e le playlist per resolution disponibili
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
        file_name = file_name.replace("'", "_")
        print(f"[FILE NAME] {file_name}")
        print(f"# MASTER # {master_playlist_url}")  # todo

        # scelgo la migliore risoluzione tra quelle disponibili nella playlist master
        playlist_video_url = utility.best_resolution(media=media.data.video['stream_info'])
        print(f"[BEST RESOLUTION] {playlist_video_url}")

        response = await my_http.get(playlist_video_url)
        playlist_video_data = await response.text()
        playlist_video = m3u8.loads(playlist_video_data)
        key = True if playlist_video.keys[0] else False
        key_message = 'Encrypted' if key else ''
        print(f"[VIDEO DATA] {key_message} {playlist_video_url}")

        # Ottengo la playlist audio
        playlist_audio: m3u8 = None
        if media.data.audio:
            response = await my_http.get(media.data.audio['uri'])
            playlist_audio_data = await response.text()
            playlist_audio = m3u8.loads(playlist_audio_data)
            print(f"[AUDIO DATA] Presente {media.data.audio['uri']}")

        # Ottengo la playlist subtitles
        subtitles_path = ''
        if media.data.subtitle:
            response = await my_http.get(media.data.subtitle['uri'])
            playlist_sub_data = await response.text()
            playlist_sub = m3u8.loads(playlist_sub_data)
            sub = Direct(file_name=file_name, media='SUB')
            subtitles_path = sub.download_url(url=playlist_sub.segments.uri[0])  # todo verificare le lingue
            print(f"[SUB DATA]   Presente {playlist_sub.segments.uri}")

    # Inizio i download del video
    video = Downloader(playlist=playlist_video, file_name=file_name, media='VIDEO', key=key)
    video_path = video.start()
    video.close()
    del video
    print(f'[DOWNLOAD COMPLETATO] {time.time() - start_timer} secs\n') if video_path else None

    # Inizio i download dell' Audio
    audio = Downloader(playlist=playlist_audio, file_name=file_name, media='AUDIO', key=key)
    audio_path = audio.start()
    audio.close()
    del audio
    print(f'[DOWNLOAD COMPLETATO] {time.time() - start_timer} secs\n') if audio_path else None

    # Test
    """
    audio_path = ''
    video_path = "/home/midnight/SC_Downloads/Rick and Morty S:3 E:2/VIDEO"
    subtitles_path = ''
    """

    # Se almeno i files della playlist video sono stati scaricati proseguo con il merge
    if playlist_video:
        test_ts = join.Test()
        audio_verify = True
        video_verify = True

        if playlist_audio:
            audio_verify = test_ts.ts_sequence(ts_folder=audio_path, playlist=playlist_audio)
        if playlist_video:
            video_verify = test_ts.ts_sequence(ts_folder=video_path, playlist=playlist_video)

        if audio_verify and video_verify:
            m = merge.Merge(file_name=file_name, video_folder=video_path, audio_folder=audio_path,
                            subtitles_folder=subtitles_path)
            # todo: 'probe' per il momento non utilizzato
            # m.verify_ts_files()
            m.merge_ts_files()


if __name__ == "__main__":
    asyncio.run(start())
