## Things to know before you start
This application is only tested in Mac.
Notice that this application is still in its early stage,
no key bindings and not configurable for multiple sources of streaming.
Currently only support google music.
In the near future, it should be able to stream music from youtube
 or other platforms.

I start coding for this because I cannot find a proper command line tool 
that does shuffling on the playlist.

## Requirement
- python2
- ffplay
- virtualenv

## Installation
```bash
brew install ffmpeg --with-sdl2
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```
