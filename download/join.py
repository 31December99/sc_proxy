import os
import re
import m3u8


class Test:
    @staticmethod
    def ts_sequence(ts_folder: str, playlist: m3u8) -> bool:
        """ Confronto la playlist con i files .ts scaricati  """

        # ottengo la lista dei segmenti
        segments_list = playlist.segments.uri

        # ottengo una lista ordinata dei files presenti all'interno della cartella ts
        dir_list = sorted(os.listdir(ts_folder))

        files_name = [file_name[5:].replace('.ts', '') for file_name in dir_list]

        playlist_files = [(match.group(1), segment) for index, segment in enumerate(segments_list)
                          if (match := re.search(r'\/([^\/]+)\.ts', segment))]

        failed = [segment for ts_name, segment in playlist_files if ts_name not in files_name]

        print(f"SEGMENTS:{len(segments_list)} - HDD FILES:{len(files_name)} - FAILED:{len(failed)}")
        return False if failed else True
