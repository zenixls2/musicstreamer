from __future__ import print_function
from drivers.gmusic import GoogleMusic
import subprocess
from utils import StoppableThread, time_elapse

if __name__ == '__main__':
    adaptor = GoogleMusic({'oauth_path': './oauth.cred'})
    while True:
        output = adaptor.get()
        if not output:
            print("output is nil")
            break
        ps = subprocess.Popen(('ffplay', '-autoexit', '-loglevel', 'panic',
            '-nodisp', '-vn', '-'), stdin=subprocess.PIPE)

        print("song length: %d sec" % output.get('song_length', 0))
        print("album:", output.get('album', ''))
        print("artist:", output.get('artist', ''))
        print("title:", output.get("title", ''))
        print(len(output.get('audio')))
        timer = StoppableThread(target=time_elapse,
                                args=(output.get('song_length', 0), ))
        timer.daemon = True
        timer.start()
        ps.communicate(input=output.get('audio'))
        timer.stop()
        timer.join()

