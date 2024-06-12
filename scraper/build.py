import json
from scraper import playlist, video


class Data:
    """ Raggruppa ogni oggetto media e lo incapsula in Data"""

    def __init__(self, audio: dict = None, subtitle: dict = None, video: dict = None):
        self.audio = audio
        self.subtitle = subtitle
        self.video = video


class Download:
    def __init__(self, data: Data):
        self.data = data

    @classmethod
    def from_data(cls, playlist_data: str, video_data: str):
        """ Crea un oggetto audio, video, subtitle per il prossimo download"""

        # legge la playlist è crea un oggetto audio e subtitle
        playlist_obj = playlist.Hls(playlist_data)

        # Legge l'oggetto video_data e crea un oggetto video con all'interno varie informazioni
        data = json.loads(video_data)
        video_obj = video.Video.from_json(data['data'])

        audio = None
        subtitle = None

        # Determina il tipo di Audio e Subtitle
        for media in playlist_obj.media:
            if isinstance(media, playlist.Audio):
                if 'ita' in media.language:
                    audio = {'audio': media.language, 'uri': media.uri}

            if isinstance(media, playlist.Subtitle):
                if 'ita' in media.language:
                    subtitle = {'subtitle': media.language, 'uri': media.uri, 'forced': media.forced}

        video_ = {
            'videoid': video_obj.id,
            'name': video_obj.name,
            'filename': video_obj.filename,
            'size': video_obj.size,
            'quality': video_obj.quality,
            'duration': video_obj.duration,
            'views': video_obj.views,
            'is_viewable': video_obj.is_viewable,
            'status': video_obj.status,
            'fps': video_obj.fps,
            'legacy': video_obj.legacy,
            'folder_id': video_obj.folder_id,
            'created_at_diff': video_obj.created_at_diff,
            # 'video_tracks': video_obj.video_tracks,
            'stream_info': playlist_obj.stream_info
        }
        data = Data(audio=audio, subtitle=subtitle, video=video_)
        return cls(data=data)


def data(playlist_data: str, video_data: str):
    return Download.from_data(playlist_data, video_data)
