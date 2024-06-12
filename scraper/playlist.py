import m3u8


class BaseMedia:
    def __init__(self, group_id, name, uri):
        self.group_id = group_id
        self.name = name
        self.uri = uri

    def process(self):
        print("Elaborazione di media di base:", self.name)


class Audio(BaseMedia):
    def __init__(self, group_id, name, uri, language):
        super().__init__(group_id, name, uri)
        self.language = language

    def process(self):
        print("Elaborazione di audio:", self.name)


class Subtitle(BaseMedia):
    def __init__(self, group_id, name, uri, language, forced):
        super().__init__(group_id, name, uri)
        self.language = language
        self.forced = forced

    def process(self):
        print("Elaborazione di sottotitoli:", self.name)


class StreamInfo:
    def __init__(self, bandwidth, codecs, resolution, audio, subtitles, uri):
        self.bandwidth = bandwidth
        self.codecs = codecs
        self.resolution = resolution
        self.audio = audio
        self.subtitles = subtitles
        self.uri = uri


class Hls:

    def __init__(self, playlist: str):
        self.__playlist = playlist
        self.__m3u8 = m3u8.loads(playlist)
        self.__segments_uri = self.__m3u8.segments.uri

    @property
    def playlists(self):
        return self.__m3u8

    @property
    def segments_uri(self):
        return self.__segments_uri

    @property
    def media(self) -> []:
        media_list = []
        for media in self.playlists.media:
            if media.type == 'AUDIO':
                info = Audio(
                    media.group_id,
                    media.name,
                    media.uri,
                    media.language
                )
            elif media.type == 'SUBTITLES':
                info = Subtitle(
                    media.group_id,
                    media.name,
                    media.uri,
                    media.language,
                    media.forced
                )
            else:
                # Other media types
                info = BaseMedia(
                    media.group_id,
                    media.name,
                    media.uri
                )
            media_list.append(info)
        return media_list

    @property
    def stream_info(self) -> []:
        stream_info_list = []
        for stream in self.playlists.playlists:
            info = StreamInfo(
                stream.stream_info.bandwidth,
                stream.stream_info.codecs,
                stream.stream_info.resolution,
                stream.stream_info.audio,
                stream.stream_info.subtitles,
                stream.uri
            )
            stream_info_list.append(info)
        return stream_info_list


