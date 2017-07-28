## Things to know before you start
This application is only tested in Mac.

Now thanks to various libraries ([youtube_dl](https://rg3.github.io/youtube-dl/), [pafy](https://pypi.python.org/pypi/pafy), and [gmusicapi](https://github.com/simon-weber/gmusicapi/tree/master), we are able to shuffle music from different resources.

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
echo '{"gmusic": [{}]}' > config/config.json
python main.py
```

## About configuration
There's a sample config json in `config` folder.
fill in required fields and rename as `config.json`.

The configuration about google music is straitforward.
You don't even have to download the credential on your own.
Just follow the steps to input the credential code from browser.

The youtube configuration is a little bit annoying, you have to go to the
google developer console, create a new project that enables youtube data api, and create to download the credential in order to past to the config.json. (Actually I could provide my own credential, but this means everyone have to share the same quota amount. Notice the free limitation is only 1,000,000 request quota per month. This should be enough for personal use, but not for a group of users.)

I will fix this in the future, and perhaps we will have the same interface of authentication as the google music part.
