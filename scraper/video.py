# -*- coding: utf-8 -*-
class VideoTrack:
    def __init__(self, id: int, codec: str, bitrate: int, resolution: str):
        self.id = id
        self.codec = codec
        self.bitrate = bitrate
        self.resolution = resolution

    def __str__(self):
        return f"VideoTrack(id={self.id}, codec={self.codec}, bitrate={self.bitrate}, resolution={self.resolution})"

    @classmethod
    def from_json(cls, data: dict):
        return cls(
            id=data['id'],
            codec=data['codec'],
            bitrate=data['bitrate'],
            resolution=data['resolution']
        )


class Video:
    def __init__(self, id: int, name: str, filename: str, size: int, quality: int, duration: int, views: int,
                 is_viewable: int, status: str, fps: int, legacy: int, folder_id: str, created_at_diff: str):
                 # video_tracks: List[VideoTrack]):
        self.id = id
        self.name = name
        self.filename = filename
        self.size = size
        self.quality = quality
        self.duration = duration
        self.views = views
        self.is_viewable = is_viewable
        self.status = status
        self.fps = fps
        self.legacy = legacy
        self.folder_id = folder_id
        # self.video_tracks = video_tracks
        self.created_at_diff = created_at_diff

    def __str__(self):
        return (f"Video(id={self.id}, name={self.name}, filename={self.filename}, size={self.size}, "
                f"quality={self.quality}, duration={self.duration}, views={self.views}, is_viewable={self.is_viewable}, "
                f"status={self.status}, fps={self.fps}, legacy={self.legacy}, folder_id={self.folder_id}, "
                f"created_at_diff={self.created_at_diff})") # , video_tracks={self.video_tracks})")

    @classmethod
    def from_json(cls, data: dict):
        # video_tracks = [VideoTrack(**track) for track in data.get('video_tracks', [])]
        return cls(
            id=data['id'],
            name=data['name'],
            filename=data['filename'],
            size=data['size'],
            quality=data['quality'],
            duration=data['duration'],
            views=data['views'],
            is_viewable=data['is_viewable'],
            status=data['status'],
            fps=data['fps'],
            legacy=data['legacy'],
            folder_id=data['folder_id'],
            # video_tracks=video_tracks,
            created_at_diff=data['created_at_diff']
        )
