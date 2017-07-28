from __future__ import print_function
from drivers.gmusic import GoogleMusic
from drivers.youtube import YoutubeMusic
import subprocess
from utils import StoppableThread, time_elapse
import random
import json

adaptors = []

if __name__ == '__main__':
    config = json.load(open('./config/config.json'))
    for k, v in config.iteritems():
        if k == 'youtube':
            for params in v:
                adaptors.append(YoutubeMusic(params))
        elif k == 'gmusic':
            for params in v:
                adaptors.append(GoogleMusic(params))

    while True:
        adaptor = random.choice(adaptors)
        output = adaptor.get()
        if not output:
            print("output is nil")
            break
        print("song length: %d sec" % output.get('song_length', 0))
        print("album:", output.get('album', ''))
        print("artist:", output.get('artist', ''))
        print("title:", output.get("title", ''))
        print("song size:", len(output.get('audio')))
        ps = subprocess.Popen(('ffplay', '-autoexit', '-loglevel', 'panic',
            '-nodisp', '-vn', '-'), stdin=subprocess.PIPE)

        timer = StoppableThread(target=time_elapse,
                                args=(output.get('song_length', 0), ))
        timer.daemon = True
        timer.start()
        print(ps.communicate(input=output.get('audio')))
        timer.stop()
        timer.join()

