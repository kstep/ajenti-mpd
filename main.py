from ajenti.api import *  # noqa
from ajenti.plugins import *  # noqa
from ajenti.plugins.main.api import SectionPlugin
from ajenti.ui.binder import Binder
from ajenti.ui import on
from datetime import datetime
from gevent.lock import RLock
import mpd
import gevent
import itertools as it

ident = lambda x: x
timestamp = lambda d: datetime.strptime(d, '%Y-%m-%dT%H:%M:%SZ')
intbool = lambda v: bool(int(v))

class Model(object):
    _cast = {}

    def __init__(self, data={}, **kwargs):
        data.update(kwargs)
        for k, v in data.iteritems():
            k = k.replace('-', '_')
            setattr(self, k, self._cast.get(k, ident)(v))

    def get(self, name, default=None):
        return getattr(self, name, default)

    def __repr__(self):
        return repr(self.__dict__)

class Output(Model):
    _cast = {
            'outputenabled': intbool,
            'outputid': int,
            }

class Playlist(Model):
    _cast = {'last_modified': timestamp}

class Song(Model):
    _cast = {
            'date': timestamp,
            'last_modified': timestamp,
            'pos': int,
            'id': int,
            'time': int,
            }

    def __init__(self, data={}, **kwargs):
        if not isinstance(data, dict):
            data = {'title': str(data)}
        else:
            data.setdefault('title', '')

        Model.__init__(self, data, **kwargs)
        self.icon = 'music'

NO_SONG = Song()

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

@plugin
class MpdPlugin(SectionPlugin):
    def init(self):
        self._client = mpd.MPDClient()
        self._client_lock = RLock()

        # meta-data
        self.title = 'MPD'
        self.icon = 'music'
        self.category = _("Software")

        self.append(self.ui.inflate('mpd:main'))

        # data-bindings
        self.playlist = []
        self.playlists = []
        self.outputs = []
        self.song = NO_SONG
        self.status = Status()

        def post_item_bind(obj, collection, item, ui):
            ui.find('play').on('click', self.play, item)

        def delete_item(item, collection):
            self.remove(item)

        self.find('playlist').post_item_bind = post_item_bind
        self.find('playlist').delete_item = delete_item

        def add_playlist(item, collection):
            for i in xrange(1, 1000000):
                try:
                    self.mpd_do('save', 'Untitled %d' % i)
                except mpd.CommandError:
                    continue
                else:
                    break

            self.refresh()

        def delete_playlist(item, collection):
            self.mpd_do('rm', item.playlist)
            self.refresh()

        def post_playlist_bind(obj, collection, item, ui):
            ui.find('play').on('click', self.mpd_do, 'load', item.playlist)

        self.find('playlists').add_item = add_playlist
        self.find('playlists').delete_item = delete_playlist
        self.find('playlists').post_item_bind = post_playlist_bind

        def post_output_bind(obj, collection, item, ui):
            ui.find('enabled').on('click', self.toggleoutput, item)

        self.find('outputs').post_item_bind = post_output_bind

    def on_first_page_load(self):
        self.binder = Binder(self, self.find('mpd'))
        self.context.session.spawn(self.worker)

    def worker(self):
        while True:
            self.refresh()
            gevent.sleep(5)

    @on('refresh', 'click')
    def refresh(self):
        playlist, status, song, playlists, outputs = self.mpd_bulk_do(
                'playlist',
                'status',
                'currentsong',
                'listplaylists',
                'outputs',
                defaults=([], {}, {}, [], []))
        #self.playlist = map(lambda s: Song(pos=s[0], title=s[1]), enumerate(playlist))
        self.status = Status(status)
        self.song = Song(song)
        self.playlists = map(Playlist, playlists)
        self.outputs = map(Output, outputs)
        self.playlist = map(lambda s: Song(s[1][0], pos=s[0]),
                enumerate(self.mpd_bulk_do(
                        it.imap(lambda s: ('lsinfo', s.split(': ')[1]), playlist),
                        defaults=[{}] * len(playlist)
                    ))) if playlist else []

        try:
            if self.status.get('state') == 'play':
                self.find('play').visible = False
                self.find('pause').visible = True
                self.playlist[self.status.song].icon = 'play'

            else:
                self.find('play').visible = True
                self.find('pause').visible = False

            self.status.pvolume = self.status.volume / 100.0
            self.status.muted = self.status.volume == 0

        except AttributeError:
            pass

        self.binder.populate()

    def toggleoutput(self, output):
        self.mpd_do('disableoutput' if output.outputenabled else 'enableoutput', output.outputid)
        self.refresh()

    @on('voldown', 'click')
    def voldown(self, delta=10):
        self.mpd_do('volume', -delta)
        self.refresh()

    @on('volup', 'click')
    def volup(self, delta=10):
        self.mpd_do('volume', delta)
        self.refresh()

    _last_volume = 0
    @on('mute', 'click')
    def mute(self):
        if self.status.volume == 0:
            self.volume(self._last_volume)
        else:
            self._last_volume = self.status.volume
            self.volume(0)

    def volume(self, value):
        self.mpd_do('setvol', value)
        self.refresh()

    def remove(self, song):
        self.mpd_do('deleteid', song.id)
        self.refresh()

    #@on('reorder', 'click')
    #def reorder(self):
        #self.binder.update()

    @on('play', 'click')
    def play(self, song=None):
        if pos is None:
            self.mpd_do('play')
        else:
            self.mpd_do('playid', song.id)

        self.refresh()

    @on('pause', 'click')
    def pause(self):
        self.mpd_do('pause')
        self.refresh()

    @on('stop', 'click')
    def stop(self):
        self.mpd_do('stop')
        self.refresh()

    @on('prev', 'click')
    def prev(self):
        self.mpd_do('previous')
        self.refresh()

    @on('next', 'click')
    def next(self):
        self.mpd_do('next')
        self.refresh()

    @on('clear', 'click')
    def clear(self):
        self.mpd_do('clear')
        self.refresh()

    def mpd_bulk_do(self, *commands, **options):
        if not commands:
            return

        if len(commands) == 1 and hasattr(commands[0], '__iter__'):
            commands = commands[0]

        retry = True
        while True:
            try:
                with self._client_lock:
                    self._client.command_list_ok_begin()

                    for cmd in commands:
                        if isinstance(cmd, basestring):
                            args = ()
                        else:
                            cmd, args = cmd[0], cmd[1:]

                        cmd = cmd.replace('_', ' ')
                        self._client._execute(cmd, args)

                    return tuple(self._client.command_list_end())

            except mpd.ConnectionError:
                if not (retry and self.reconnect()):
                    return options.get('defaults') or ([None] * len(commands))
                retry = False


    def mpd_do(self, command, *args, **kwargs):
        with self._client_lock:
            command = command.replace('_', ' ')
            try:
                return self._client._execute(command, args)

            except mpd.ConnectionError:
                if not self.reconnect():
                    return kwargs.get('default', None)
                return self._client._execute(command, args)

    _connected = True
    def reconnect(self):
        try:
            self._client.disconnect()
        except mpd.ConnectionError:
            pass

        try:
            self._client.connect('127.0.0.1', 6600)

        except (IOError, mpd.ConnectionError) as e:
            if self._connected:
                self.context.notify('error', _('MPD connection failed with error: %s.<br>MPD is not running?') % str(e))
                self._connected = False
            return None

        else:
            self._connected = True

        return self._client
