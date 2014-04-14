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
            'time': timedelta,
            'genre': lambda g: ', '.join(set(g)) if isinstance(g, list) else g,

            'title': fixutf8,
            'album': fixutf8,
            'artist': fixutf8,
            }
    _defaults = {
            'time': None,
            }

    def _init(self):
        if 'name' in self:
            self.time = u'\u221E'
            self.icon = 'signal'

        elif 'title' in self:
            self.icon = 'music'

    @property
    def ticker(self):
        try:
            return _('Playing “%s” by “%s” from “%s”') % (self.title, self.artist, self.album)

        except AttributeError:
            try:
                return _('Playing “%s”') % self.name

            except AttributeError:
                return 'Playing something with unknown title'

    @ticker.setter
    def ticker(self, value):
        pass


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
            'time': lambda v: tuple(map(timedelta, v.split(':')))
            }

    _defaults = {
            'state': None,
            'volume': 0,
            }

    def _init(self):
        self.play_time, self.total_time = map(lambda t: t.total_seconds(), self.time)
        self.is_playing = self.state == 'play'

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
            'artist': None,
            'album': None,
            'genre': None,
            }

    def _init(self):
        self.artists_labels = map(lambda n: fixutf8(n) if n else '* Unknown *', self.artists)
        self.albums_labels = map(lambda n: fixutf8(n) if n else '* Unknown *', self.albums)
        self.genres_labels = map(lambda n: fixutf8(n) if n else '* Unknown *', self.genres)

        self.artists.insert(0, None)
        self.artists_labels.insert(0, '* All artists *')

        self.albums.insert(0, None)
        self.albums_labels.insert(0, '* All albums *')

        self.genres.insert(0, None)
        self.genres_labels.insert(0, '* All genres *')

