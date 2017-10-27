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

The result with youtube and gmusic account would be like this:

```json
{
    "youtube": [
        {
            "installed":{
                "client_id":"xxxxxxxxxxxx.apps.googleusercontent.com",
                "project_id":"xxxxxxxx",
                "auth_uri":"https://accounts.google.com/o/oauth2/auth",
                "token_uri":"https://accounts.google.com/o/oauth2/token",
                "auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs",
               "client_secret":"xxxxxxxxxxxxxxxxx",
               "redirect_uris":["urn:ietf:wg:oauth:2.0:oob","http://localhost"]
            },
            "blacklist": ["playlist id1", "playlist id2"]
        },
    ],
    "gmusic": [
        {"oauth_path": "{path your oauth credential}"},
        {"oauth_path": "{for your second credential}"},
        ...
    ]
}
```

The configuration about google music is straitforward.
You don't even have to download the credential on your own.
Just follow the steps to input the credential code from browser.

The youtube configuration is a little bit annoying, you have to go to the
google developer console, create a new project that enables youtube data api, and create to download the credential in order to past to the config.json. (Actually I could provide my own credential, but this means everyone have to share the same quota amount. Notice the free limitation is only 1,000,000 request quota per month. This should be enough for personal use, but not for a group of users.)

I will fix this in the future, and perhaps we will have the same interface of authentication as the google music part.

## Text Mode User Interface
To invoke it, use following command:
```bash
source venv/bin/activate && python ui.py
```
The Text-Mode UI supports song switch, and could resize according to the terminal size.

[![asciicast](https://asciinema.org/a/144511.png)](https://asciinema.org/a/144511)
