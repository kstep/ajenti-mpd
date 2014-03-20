# -*- encoding: utf-8 -*-
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

    def init(self):
        self.isfile = bool(self.get('title'))
        self.isstream = bool(self.get('name'))

        if self.isstream:
            self.time = u'\u221E'
            self.icon = 'signal'

        else:
            self.icon = 'music'

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
