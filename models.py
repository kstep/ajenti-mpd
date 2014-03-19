from ajenti.util import public
from ajenti.plugins.mpd.api import *  # noqa

@public
class Output(Model):
    _cast = {
            'outputenabled': intbool,
            'outputid': int,
            }

@public
class Playlist(Model):
    _cast = {'last_modified': timestamp}

@public
class Song(Model):
    _cast = {
            'date': timestamp,
            'last_modified': timestamp,
            'pos': int,
            'id': int,
            'time': time,
            }

    def __init__(self, data={}, **kwargs):
        if not isinstance(data, dict):
            data = {'title': str(data)}
        else:
            data.setdefault('title', '')

        Model.__init__(self, data, **kwargs)
        self.icon = 'music'
        self.present = bool(self.title)

@public
class Status(Model):
    _cast = {
            'bitrate': int,
            'consume': intbool,
            'elapsed': float,
            'mixrampdb': float,
            'playlist': int,
            'playlistlength': int,
            'random': intbool,
            'repeat': intbool,
            'single': intbool,
            'song': int,
            'songid': int,
            'volume': int,
            }
