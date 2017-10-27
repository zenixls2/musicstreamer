from __future__ import print_function
import os
from google_auth_oauthlib.flow import InstalledAppFlow
import google_auth_httplib2
import cPickle
from apiclient import discovery
from apiclient.discovery import build
import googleapiclient
from googleapiclient.http import build_http
import requests
from urlparse import parse_qsl, parse_qs
import random
from Queue import Queue, Empty
import mutagen
import StringIO
import sys
import re
import pafy
import youtube_dl
from youtube_dl.YoutubeDL import YoutubeDL
from youtube_dl.extractor.youtube import YoutubeIE
from youtube_dl.downloader.http import HttpFD
sys.path.append(os.path.expanduser('.'))
from utils import StoppableThread

SCOPE = ["https://www.googleapis.com/auth/youtube.readonly"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
HEADER = {'origin': 'https://www.youtube.com', 'referer': 'https://www.youtube.com', 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'}


class YoutubeMusic(object):
    def __init__(self, config, log=print):
        self.config = config
        self.credential_dir = os.path.join(os.path.expanduser('.'),
                                           '.credential')
        self.credential_path = os.path.join(self.credential_dir,
                                            'credential.pkl')

        self.credentials = self.get_credentials()
        http = google_auth_httplib2.AuthorizedHttp(self.credentials,
                                                http=build_http())
        self.service = discovery.build(
                API_SERVICE_NAME, API_VERSION, http=http)
        self.cache_play_list = {}
        self.cache_song_list = {}
        random.seed()
        self.thread = None
        self.queue = Queue()
        self.log = log
        self._enqueue_output()

    def get_credentials(self):
        if not os.path.exists(self.credential_dir):
            os.makedirs(self.credential_dir)
        if os.path.exists(self.credential_path):
            with open(self.credential_path, 'rb') as f:
                return cPickle.load(f)

        flow = InstalledAppFlow.from_client_config(
                    self.config, SCOPE,
                    redirect_uri='urn:ietf:wg:oauth:2.0:oob')
        flow.run_local_server()
        session = flow.authorized_session()
        with open(self.credential_path, 'wb') as f:
            cPickle.dump(session.credentials, f, cPickle.HIGHEST_PROTOCOL)
        return session.credentials

    def playlist(self):
        '''
        example
        {
          "kind": "youtube#playlistListResponse",
          "etag": "ETAG",
          "pageInfo": {
            "totalResults": 7,
            "resultsPerPage": 25
          },
          "items": [
            {
              "kind": "youtube#playlist",
              "etag": "ETAG",
              "id": "ID",
              "snippet": {
                "publishedAt": "2016-02-19T16:01:09.000Z",
                "channelId": "ID_STRING",
                "title": "TITLE",
                "description": "",
                "thumbnails": {
                  "default": {
                    "url": "https://i.ytimg.com/vi/pZWYqkEwChE/default.jpg",
                    "width": 120,
                    "height": 90
                  },
                  "medium": {
                    "url": "https://i.ytimg.com/vi/pZWYqkEwChE/mqdefault.jpg",
                    "width": 320,
                    "height": 180
                  },
                  "high": {
                    "url": "https://i.ytimg.com/vi/pZWYqkEwChE/hqdefault.jpg",
                    "width": 480,
                    "height": 360
                  },
                  "standard": {
                    "url": "https://i.ytimg.com/vi/pZWYqkEwChE/sddefault.jpg",
                    "width": 640,
                    "height": 480
                  },
                  "maxres": {
                    "url": "https://i.ytimg.com/vi/pZWYqkEwChE/maxresdefault.jpg",
                    "width": 1280,
                    "height": 720
                  }
                },
                "channelTitle": "USER_NAME",
                "localized": {
                  "title": "TITLE_LOCAL",
                  "description": ""
                }
              }
            }
          ]
        }
        '''
        while True:
            try:
                data = self.service.playlists().list(
                        part='snippet', maxResults=50, mine=True).execute()
                result = {}
                for item in data.get('items', []):
                    if item.get('id') in self.config.get('blacklist', []):
                        continue
                    snippet = item.get('snippet', {})
                    result[item.get('id', '')] = [
                            snippet.get('title'), snippet.get('description')]
                return result
            except Exception as e:
                self.log(e)

    def playlistSongs(self, id):
        nextPageToken = ""
        songs = {}
        while True:
            try:
                data = self.service.playlistItems().list(
                    part='snippet', maxResults=50, playlistId=id,
                    pageToken=nextPageToken).execute()

                for i in data.get('items', []):
                    snippet = i.get('snippet', {})
                    videoId = snippet.get('resourceId', {}).get('videoId', '')
                    songs[videoId] = snippet.get('title', '')
                nextPageToken = data.get('nextPageToken', '')
                if nextPageToken == '':
                    break
            except Exception as e:
                self.log(e)
        return songs

    # Deprecated
    def getVideoUrlHQ(self, vid):
        vinfo = requests.get('http://www.youtube.com/get_video_info?video_id='+vid)
        params = parse_qs(vinfo.content)
        signature = parse_qs(params['probe_url'][0])['signature'][0]
        self.log(params['title'][0])
        self.log(params['length_seconds'][0])
        self.log(params['author'][0])
        self.log(params.keys())

        stream_map = params.get('adaptive_fmts', [''])[0] + ',' + params.get('url_encoded_fmt_stream_map', [''])[0]
        if 'rtmpe%3Dyes' in stream_map:
            raise Exception("rtmpe cannot be downloaded")
        vid_info = stream_map.split(',')

        for video_query in vid_info:
            if len(video_query) == 0:
                continue
            video = parse_qs(video_query)
            url = video['url'][0]
            if 'sig' in video:
                url += '&signature=' + video['sig'][0]
            elif 's' in video:
                encrypted_sig = video['s'][0]
                raise Exception('not implemented')
            return url


    def getVideoUrlDirect(self, vid):
        # blacklist webm, since most players cannot read
        yd = YoutubeIE(downloader=YoutubeDL(params={"quiet": True}))
        info = yd._real_extract('https://www.youtube.com/watch?v=%s' % vid)
        _max = -1
        url = ''
        result = {}
        for fmt in info['formats']:
            if fmt.get('height', 0) > _max and result.get('ext', '') != 'webm':
                _max = fmt.get('height', 0)
                result = fmt
                url = fmt['url']
        return url, result.get('ext', ''), info.get('duration', 0)

    def getAudioUrlDirect(self, vid):
        # only get audio format, but usually in bad quality...
        video = pafy.new('https://www.youtube.com/watch?v=%s' % vid)
        bestaudio = video.getbestaudio()
        self.log(bestaudio.bitrate)
        return bestaudio.url, bestaudio.extension, bestaudio.length


    def _enqueue_output(self):
        retry = 3
        while retry > 0:
            retry -= 1
            if not self.cache_play_list:
                self.cache_play_list = self.playlist()
            pid = random.choice(self.cache_play_list.keys())
            if not self.cache_song_list.get(pid, None):
                self.cache_song_list[pid] = self.playlistSongs(pid)

            self.log("select playlist:", pid, self.cache_play_list[pid][0]);
            if not self.cache_song_list.get(pid):
                print("select fail")
                self.cache_play_list.pop(pid)
                retry += 1
                continue
            vid = random.choice(self.cache_song_list[pid].keys())
            self.log("downloading https://www.youtube.com/watch?v="+vid)
            url = None
            ext = ''
            length = 0
            try:
                url, ext, length = self.getVideoUrlDirect(vid)
            except Exception as e:
                self.log(vid + ' exract fail')
                try:
                    self.log(e)
                except:
                    pass
                self.cache_song_list[pid].pop(vid)
                retry += 1
                continue
            if not url:
                self.log(vid + "'s video info get fail")
                continue
            result = requests.get(url, headers=HEADER)
            if result.status_code != 200:
                self.log("fail to download video")
                continue
            video = result.content
            filelike = StringIO.StringIO(video)
            output = {
                'song_length': length,
                'album': '',
                'artist': '',
                'title': self.cache_song_list[pid][vid],
                'audio': video,
                'song_size': len(video)
            }
            self.queue.put(output)
            break
        if retry == 0:
            self.log("Youtube download fail, please restart the program")
            self.queue.put({})


    def get(self):
        output = self.queue.get(block=True)
        self.thread = StoppableThread(target=self._enqueue_output)
        self.thread.daeamon = True
        self.thread.start()
        return output




if __name__ == '__main__':
    # change to test
    client_id = ""
    client_secret = ""
    y = YoutubeMusic({"installed":{"client_id":client_id,"project_id":"youtubetest-174705","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://accounts.google.com/o/oauth2/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":client_secret,"redirect_uris":["urn:ietf:wg:oauth:2.0:oob","http://localhost"]}})
    url = y.getVideoUrlDirect('U3saIiAhWV8')
    print(url)
    result = requests.get(url, headers=HEADER)
    print(result.status_code)
    print(len(result.content))
