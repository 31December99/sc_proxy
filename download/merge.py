# -*- coding: utf-8 -*-

import os
import ffmpeg
import re
import logging


def ts_number(file_path):
    """ estrae il numero di ts dal filename """
    match = re.search(r'(\d{4})_', file_path)
    if match:
        return int(match.group(1).zfill(4))
    return -1


class Merge:

    def __init__(self, file_name: str, audio_folder: str, video_folder: str, subtitles_folder: str):

        self.file_name = file_name
        self.audio_folder = audio_folder
        self.video_folder = video_folder
        self.subtitles_folder = subtitles_folder
        self.output_folder = video_folder.replace("VIDEO", '')

        # Ordino i files nella cartella in base all'indice
        if audio_folder:
            _list = (
                [os.path.join(self.audio_folder, f) for f in os.listdir(self.audio_folder) if f.endswith('.ts')])
            # passo ogni elemento di _list a ts_number attraverso l'assegnazione a key
            self.audio_files = sorted(_list, key=ts_number)

        # Ordino i files nella cartella in base all'indice
        if video_folder:
            _list = (
                [os.path.join(self.video_folder, f) for f in os.listdir(self.video_folder) if f.endswith('.ts')])
            # passo ogni elemento di _list a ts_number attraverso l'assegnazione a key
            self.video_files = sorted(_list, key=ts_number)

    def _vtt_to_srt(self):
        """ Converte un file vtt in srt . mp4 non supporta vtt"""

        vtt_file = os.path.join(self.subtitles_folder, self.file_name)
        srt_file = os.path.join(self.output_folder, "SUB", f"{self.file_name}.srt")
        try:
            ffmpeg.input(vtt_file).output(srt_file).run()
        except ffmpeg.Error as e:
            print(f"Errore durante la conversione VTT in SRT: {e}")

    def _check_ts_file(self, file_path):
        try:
            ffmpeg.probe(file_path)
            # return True
        except ffmpeg.Error as e:
            print(f"Errore nel controllo del file {file_path}: {e}")
            return False

    def verify_ts_files(self):
        for video_f in self.video_files:
            try:
                print(f"[VERIFY] {video_f}")
                ffmpeg.probe(video_f)
            except Exception as e:
                print(e)

    def join_ts_files(self, file_list, output_file):

        if not file_list:
            print("No files to concatenate.")
            return

        # with open('file_list.txt', 'w', encoding='utf-8') as f:
        with open('file_list.txt', 'w') as f:
            for file_name in file_list:
                f.write(f"file '{file_name}'\n")

        # ffmpeg non determina il tipo di file se non esiste l'estensione....
        file_ext = os.path.splitext(self.file_name)[1]
        if not file_ext:
            # Analizzo il primo file ts e determino se mp4 o mkv quindi aggiungo l'estensione
            ext = self.format(self.video_files[0])
            output_file += '.' + ext

        final_output = os.path.join(self.output_folder, output_file)
        try:
            # Run the ffmpeg command using the file list
            """
            ffmpeg.input('file_list.txt', format='concat', safe=0).output(final_output, c='copy',
                                                                          threads=8).global_args('-loglevel',
                                                                                                 'debug').run(quiet=True)
            """

            ffmpeg.input('file_list.txt', format='concat', safe=0).output(
                final_output, c='copy', shortest=None, preset='ultrafast', threads=8).run(quiet=True)

            # capture_stdout=True, capture_stderr=True)
            print(f"[OK] {output_file}")
        except FileNotFoundError as e:
            logging.error(f"FileNotFoundError: {e.strerror} ({e.filename})")
        except ffmpeg.Error as e:
            logging.error(f"Error during TS file concatenation: {e.stderr.decode('utf-8')}")
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
        finally:
            pass

    def merge_ts_files(self):

        print("Merging....")
        audio_concat_file = os.path.join(self.output_folder, "audio_concat.ts")
        video_concat_file = os.path.join(self.output_folder, "video_concat.ts")

        if not self.audio_folder:  # Se la lista dei file audio è vuota
            # Concatena solo i file video
            self.join_ts_files(self.video_files, self.file_name)
            return

        """
        if len(self.audio_files) != len(self.video_files):
            print(
                f"Errore: Il numero di file audio ({len(self.audio_files)}) e video ({len(self.video_files)}) non corrisponde.")
        """

        self.join_ts_files(self.audio_files, audio_concat_file)
        self.join_ts_files(self.video_files, video_concat_file)

        if not self.subtitles_folder:
            final_output_file = os.path.join(self.output_folder, self.file_name)
        else:
            final_output_file = os.path.join(self.output_folder, "video_tmp.mp4")

        try:
            # Unire video e audio senza il filtro concat
            ffmpeg.output(ffmpeg.input(video_concat_file), ffmpeg.input(audio_concat_file), final_output_file,
                          **{'c:v': 'copy', 'c:a': 'copy'}, shortest=None, preset='ultrafast', threads=8).run()

        except ffmpeg.Error as e:
            print(f"Errore durante la fusione dei file: {e}")

        if self.subtitles_folder:
            self._vtt_to_srt()
            subtitle_files = sorted(
                [os.path.join(self.subtitles_folder, f) for f in os.listdir(self.subtitles_folder) if
                 f.endswith('.srt')])
            for subtitle_file in subtitle_files:
                output_with_subs = os.path.join(self.output_folder, self.file_name)
                sub_type = 'mov_text'
                file_format = self.format(final_output_file)
                if file_format == 'mkv': sub_type = 'srt'
                if file_format == 'mp4': sub_type = 'mov_text'
                print(f"[SUB Fileformat] {file_format}")
                try:
                    ffmpeg.output(ffmpeg.input(final_output_file), ffmpeg.input(subtitle_file), output_with_subs,
                                  c='copy',
                                  **{'c:s': sub_type}, scodec=sub_type).run()
                    final_output_file = output_with_subs  # Aggiorna il file finale con i sottotitoli

                except ffmpeg.Error as e:
                    print(f"Impossibile aggiungere i sottotitoli: {e}")

                os.remove(os.path.join(self.output_folder, "video_tmp.mp4"))

        if os.path.exists(audio_concat_file):
            os.remove(audio_concat_file)
        if os.path.exists(video_concat_file):
            os.remove(video_concat_file)

    def format(self, file_path):
        """ Determina il formato del file utilizzando ffprobe """
        try:
            info = ffmpeg.probe(file_path)
            codec_name = info['streams'][0]['codec_name']
            if codec_name == 'h264':
                return 'mkv'  # srt
            elif codec_name == 'hevc':
                return 'mp4'  #mov_text
            else:
                raise ValueError(f"Formato non supportato per il file {file_path}")
        except Exception as e:
            print(f"Errore durante l'analisi di {file_path} con ffprobe: {e}")
            raise
