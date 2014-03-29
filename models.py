# -*- encoding: utf-8 -*-
from ajenti.util import public
from ajenti.plugins.mpd.api import *  # noqa
from ajenti.plugins.models.api import *  # noqa

@public
class Output(Model):
    _casts = {
            'outputenabled': intbool,
            'outputid': int,
            }

@public
class Playlist(Model):
    _casts = {'last_modified': timestamp}

@public
class Song(Model):
    _casts = {
            'date': timestamp,
            'last_modified': timestamp,
            'pos': int,
            'id': int,
            'time': int,
            'genre': lambda g: ', '.join(set(g)) if isinstance(g, list) else g,

            'title': fixutf8,
            'album': fixutf8,
            'artist': fixutf8,
            }
    _defaults = {
            'time': None,
            }

    def _init(self):
        self.is_file = bool(self.get('title'))
        self.is_stream = bool(self.get('name'))

        if self.is_stream:
            self.time_str = u'\u221E'
            self.icon = 'signal'

        else:
            self.time_str = time(self.time)
            self.icon = 'music'

@public
class Status(Model):
    _casts = {
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
            'time': lambda v: tuple(map(int, v.split(':')))
            }

    _defaults = {
            'state': None,
            'volume': 0,
            }

    def _init(self):
        try:
            self.play_time, self.total_time = self.time
            self.play_time_str, self.total_time_str = time(self.play_time), time(self.total_time)
            self.progress = float(self.play_time) / float(self.total_time)
            self.time_ticker = '%s / %s' % (self.play_time_str, self.total_time_str)

        except (AttributeError, ValueError, TypeError):
            self.total_time, self.play_time = None, None
            self.total_time_str, self.play_time_str = None, None
            self.time, self.progress = None, None
            self.time_ticker = ''

        except ZeroDivisionError:
            self.play_time, self.total_time = self.time[0], None
            self.play_time_str, self.total_time_str = time(self.play_time), u'\u221E'
            self.progress = None
            self.time_ticker = '%s / %s' % (self.play_time_str, self.total_time_str)

        self.pvolume = self.volume / 100.0
        self.muted = self.volume == 0

@public
class Stats(Model):
    _casts = {
            'albums': int,
            'artists': int,
            'db_playtime': int,
            'db_update': unixtime,
            'playtime': int,
            'uptime': int,
            }

    def _init(self):
        self.uptime_str = time(self.uptime)
        self.playtime_str = time(self.playtime)
        self.db_playtime_str = time(self.db_playtime)

@public
class UpdateInfo(Model):
    _casts = {
            'status': Status,
            'currentsong': Song,
            'playlistinfo': listof(Song),
            'listplaylists': listof(Playlist),
            'outputs': listof(Output),
            }

    _defaults = {
            'status': Status.EMPTY,
            'currentsong': Song.EMPTY,
            'playlistinfo': [],
            'listplaylists': [],
            'outputs': [],
            }

@public
class Taxonomy(Model):
    _casts = {
            'artists': listof(str),
            'albums': listof(str),
            'genres': listof(str),
            }

    _defaults = {
            'artists': [],
            'albums': [],
            'genres': [],
            'artist': '',
            'album': '',
            'genre': '',
            }

