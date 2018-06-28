from __future__ import print_function
from gmusicapi import Musicmanager, CallFailure
from gmusicapi.protocol import musicmanager
import os
import random
from Queue import Queue, Empty
import StringIO
import mutagen
from utils import fix_name, StoppableThread

class Dummy(object):
    def __init__(self):
        self.text = ['']
        self.encoding = 'utf-8'

dummy = Dummy()

class GoogleMusic(object):
    def __init__(self, config, log=print):
        self.OAUTH_PATH = config.get('oauth_path', '/tmp/oauth.cred')
        self.mm = Musicmanager()
        if os.path.isfile(self.OAUTH_PATH):
            success = self.mm.login(oauth_credentials=self.OAUTH_PATH)
            if not success:
                self.mm.perform_oauth(storage_filepath=self.OAUTH_PATH,
                                      open_browser=True)
        else:
            self.mm.perform_oauth(storage_filepath=self.OAUTH_PATH,
                                  open_browser=True)
        random.seed()
        self.songs = self.mm.get_uploaded_songs()
        self.queue = Queue()
        self.thread = None
        self.log = log
        self._enqueue_output()

    def _enqueue_output(self):
        song = random.choice(self.songs)
        self.log("get song id" + song['id'])
        retry = 3
        while retry > 0:
            try:
                filename, audio = self.mm.download_song(song['id'])
                if len(audio) == 0:
                    self.log("audio size 0")
                    song = random.choice(self.songs)
                    continue

                filelike = StringIO.StringIO(audio)
                metadata = mutagen.File(filelike)
                output = {
                    'song_length': 0,
                    'album': '',
                    'artist': '',
                    'title': '',
                    'audio': audio
                }

                if metadata:
                    output['song_length'] = metadata.info.length
                    output['album'] = fix_name(
                        (metadata.tags or metadata).get('TALB', dummy).text[0])
                    output['artist'] = fix_name(
                        (metadata.tags or metadata).get('TPE1', dummy).text[0])
                    output['title'] = fix_name(
                        (metadata.tags or metadata).get('TIT2', dummy).text[0])

                self.queue.put(output)
                break
            except CallFailure:
                self.log("call failure")
                song = random.choice(self.songs)
                retry -= 1

        if retry == 0:
            self.log("Google Music download fail, please restart the program")
            self.queue.put({})


    def get(self):
        # TODO: set timeout from config, blacklist this instance when retry fail
        output = self.queue.get(block=True)
        self.thread = StoppableThread(target=self._enqueue_output)
        self.thread.daemon = True
        self.thread.start()
        return output

