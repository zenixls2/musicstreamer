from asciimatics.widgets import Frame, Layout, Text, TextBox, Widget, Button
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication
from drivers.gmusic import GoogleMusic
from drivers.youtube import YoutubeMusic
from threading import Lock
import subprocess
from Queue import Queue, Empty
from utils import StoppableThread, time_elapse
import random, sys
import json

empty_response = {
    "song_length": None,
    "album": None,
    "artist": None,
    "title": None,
    'song_size': None
}

class PlayerModel(object):
    def __init__(self):
        self.adaptors = []
        self.adaptor = None
        self.adaptorLock = Lock()
        self._log = ""
        self._player = None
        config = json.load(open('./config/config.json'))
        for k, v in config.iteritems():
            if k == 'youtube':
                for params in v:
                    self.adaptors.append(YoutubeMusic(params, self.log))
            elif k == 'gmusic':
                for params in v:
                    self.adaptors.append(GoogleMusic(params, self.log))

    def log(self, *args):
        self._log += ' '.join(map(lambda a: unicode(a), args)) + "\n"
        self._log = '\n'.join(self._log.split('\n')[-10:])

    def terminate(self):
        self.adaptorLock.acquire()
        if self.adaptor:
            self.adaptor.thread.terminate()
        self.ps.terminate()
        self._player.terminate()
        self.adaptorLock.release()

    def get(self):
        adaptor = random.choice(self.adaptors)
        self.adaptorLock.acquire()
        self.adaptor = adaptor
        self.adaptorLock.release()
        output = adaptor.get()
        if not output:
            return empty_response
        self.ps = subprocess.Popen(('ffplay', '-autoexit', '-loglevel', 'panic',
                               '-nodisp', '-vn', '-'), stdin=subprocess.PIPE)
        self._player = StoppableThread(target=self.ps.communicate,
                                 kwargs={"input": output.get("audio")})
        self._player.daemon = True
        self._player.start()
        return {
            "song_length": '%d sec' % output.get('song_length', 0),
            "album": output.get('album', ''),
            "artist": output.get('artist', ''),
            "title": output.get('title', ''),
            "song_size": "%d" % len(output.get('audio')),
            "message": self._log
        }

class PlayerView(Frame):
    def __init__(self, screen, model):
        super(PlayerView, self).__init__(screen,
                                         screen.height - 3,
                                         screen.width - 3,
                                         hover_focus=True, title="Music Player")
        self._model = model
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(Text("Song Length:", "song_length"))
        layout.add_widget(Text("Album:", "album"))
        layout.add_widget(Text("Artist:", "artist"))
        layout.add_widget(Text("Title:", "title"))
        layout.add_widget(Text("Song size", "song_size"))
        layout.add_widget(TextBox(Widget.FILL_FRAME,
            "System Message:", "message", as_string=True))
        layout = Layout([1, 1, 1, 1])
        self.add_layout(layout)
        layout.add_widget(Button("Next", self._next), 1)
        layout.add_widget(Button("Quit", self._quit), 2)
        self.fix()

    def _quit(self):
        if self._model._player and self._model._player.isAlive():
            self._model.terminate()
        raise StopApplication("User pressed quit")

    def reset(self):
        super(PlayerView, self).reset()
        if self._model._player and self._model._player.isAlive():
            return
        self.data = self._model.get()

    def _next(self):
        if self._model._player and self._model._player.isAlive():
            self._model.terminate()
        self.data = self._model.get()

    def update(self, frame_no):
        super(PlayerView, self).update(frame_no)
        if not self._model._player or self._model._player.isAlive():
            return
        self.data = self._model.get()


playerModel = PlayerModel()
def main(screen, scene):
    scenes = [
        Scene([PlayerView(screen, playerModel)], -1, name="Main")
    ]
    screen.play(scenes, stop_on_resize=True, start_scene=scene)

last_scene = None
while True:
    try:
        Screen.wrapper(main, catch_interrupt=True, arguments=[last_scene])
        sys.exit(0)
    except ResizeScreenError as e:
        last_scene = e.scene

