from __future__ import print_function
from gmusicapi import Musicmanager
from gmusicapi.protocol import musicmanager
import subprocess
import os
import random
from Queue import Queue, Empty
from threading import Thread, Event
import StringIO
import mutagen
import time
import sys

OAUTH_PATH = "./oauth.cred"
mm = Musicmanager()
if os.path.isfile(OAUTH_PATH):
    success = mm.login(oauth_credentials=OAUTH_PATH)
    if not success:
        mm.perform_oauth(storage_filepath=OAUTH_PATH, open_browser=True)
else:
    mm.perform_oauth(storage_filepath=OAUTH_PATH, open_browser=True)

random.seed()
songs = mm.get_uploaded_songs()
song = random.choice(songs)
filename, audio = mm.download_song(song['id'])
class Dummy(object):
    def __init__(self):
        self.text = ['']
        self.encoding = 'utf-8'

qu = Queue()
dummy = Dummy()

class StopThread(Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        super(StopThread, self).__init__(group, target, name, args, kwargs)
        self._stop_event = Event()
    def stop(self):
        self._stop_event.set()
    def stopped(self):
        return self._stop_event.is_set()

def enqueue_output(id, queue):
    filename, audio = mm.download_song(id)
    queue.put([filename, audio+'\0'])

def time_elapse(total_sec):
    start_time = time.time()
    now_time = time.time()
    while now_time - start_time < total_sec:
        print("%.1f sec/%.1f sec" % (now_time-start_time, total_sec), end="\r")
        sys.stdout.flush()
        time.sleep(0.1)
        now_time = time.time()
    print("")
    sys.stdout.flush()

def fix_name(name, recommend='utf-8'):
    recommend = str(recommend).replace('Encoding.', '')
    try:
        name = name.decode(recommend)
        return name
    except:
        pass

    try:
        name = name.decode('big5')
        return name
    except:
        pass
    try:
        name = name.decode('shift-jis')
        return name
    except:
        pass
    try:
        name = name.decode('utf-16')
        return name
    except:
        pass
    return name


# test
#filename, audio = mm.download_song('6090a58a-d361-3ae3-a4cf-a355916021ea')
#filelike = StringIO.StringIO(audio)
#metadata = mutagen.File(filelike)
#print(metadata)
#print((metadata.tags or metadata)['TALB'].encoding)
#print((metadata.tags or metadata)['TALB'].text[0])
#exit(0)

while True:
    song = random.choice(songs)
    #url = mm._make_call(musicmanager.GetDownloadLink, song['id'],
    #                    mm.uploader_id)['url']
    t = StopThread(target=enqueue_output, args=(song['id'], qu))
    t.daemon = True
    t.start()


    ps = subprocess.Popen(('ffplay', '-autoexit', '-loglevel', 'panic', '-nodisp', '-vn', '-'),
        stdin=subprocess.PIPE)

    print("playing %s" % fix_name(filename))
    filelike = StringIO.StringIO(audio)
    metadata = mutagen.File(filelike)
    timer = None

    if metadata:
        print(song['id'])
        album = (metadata.tags or metadata).get('TALB', dummy)
        artist = (metadata.tags or metadata).get('TPE1', dummy)
        title = (metadata.tags or metadata).get('TIT2', dummy)
        # the encoding is not trustworthy
        print("song length: %d sec" % metadata.info.length)
        print("album:", fix_name(album.text[0]))
        print("artist:", fix_name(artist.text[0]))
        print("title:", fix_name(title.text[0]))
        timer = StopThread(target=time_elapse, args=(metadata.info.length,))
        timer.daemon = True
        timer.start()
    ps.communicate(input=audio)

    if metadata:
        timer.stop()
        timer.join()

    filename, audio = qu.get(block=True)


