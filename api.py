from ajenti.util import public
from gevent.lock import Semaphore
from datetime import datetime
from mpd import CommandError
from itertools import chain, imap
import mpd

__all__ = ['ident', 'intbool', 'time', 'unixtime', 'listof', 'CommandError']
ident = lambda x: x
intbool = lambda v: bool(int(v))
time = lambda t: '%2d:%02d' % (int(t or 0) / 60, int(t or 0) % 60)
unixtime = lambda t: datetime.fromtimestamp(int(t))
listof = lambda cast: lambda lst: map(cast, lst)

@public
def timestamp(d):
    for pattern in (
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y',
            ):
        try:
            return datetime.strptime(d, pattern)
        except ValueError:
            continue
    return d

@public
def flatten(items):
    return (item
            for _ in items
            for item in _)


@public
def unique(items):
    last_item = next(items)
    yield last_item

    for item in items:
        if item != last_item:
            yield item
            last_item = item

@public
class Model(object):
    _casts = {}
    _defaults = {}

    def __init__(self, items=(), **kwargs):
        self.update(items, **kwargs)
        self.init()

    def init(self):
        pass

    @classmethod
    def castseq(cls, items):
        return imap(lambda kv: (kv[0].replace('-', '_'),
            cls._casts.get(kv[0], ident)(kv[1]) if kv[1] is not None else None),
            items)

    def get(self, key, default=None):
        if default is None:
            default = self._defaults.get(key, None)

        return getattr(self, key, default)

    def update(self, items=(), **kwargs):
        if isinstance(items, dict):
            items = items.iteritems()

        if kwargs:
            items = chain(items, kwargs.iteritems())

        items = self.castseq(items)

        for k, v in items:
            setattr(self, k, v)

    def __getattr__(self, key):
        try:
            return self._defaults[key]
        except KeyError:
            raise AttributeError(key)

    def __setitem__(self, key, value):
        key = key.replace('-', '_')
        setattr(self, key, self._casts.get(key, ident)(value) if value is not None else value)

    def __delitem__(self, key):
        try:
            delattr(self, key)
        except AttributeError:
            pass

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError:
            return self._defaults[key]

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, repr(self.__dict__))

    EMPTY = None
    class __metaclass__(type):
        def __init__(cls, name, bases, attrs):
            type.__init__(cls, name, bases, attrs)
            try:
                cls.EMPTY = cls()
            except AttributeError:
                pass

@public
class MPD(object):
    EV_DB_CHANGED = 'database'
    EV_DB_UPDATING = 'update'
    EV_PLAYLIST_CHANGED = 'stored_playlist'
    EV_QUEUE_CHANGED = 'playlist'
    EV_PLAYER_CHANGED = 'player'
    EV_VOLUME_CHANGED = 'mixer'
    EV_OUTPUT_CHANGED = 'output'
    EV_OPTIONS_CHANGED = 'options'
    EV_STICKER_CHANGED = 'sticker'
    EV_SUBS_CHANGED = 'subscription'
    EV_MESSAGE_RECEIVED = 'message'

    EV_PLAYBACK_CHANGED = [EV_PLAYER_CHANGED, EV_OPTIONS_CHANGED]
    EV_AUDIO_CHANGED = [EV_VOLUME_CHANGED, EV_OUTPUT_CHANGED]
    EV_ANY = [EV_DB_CHANGED, EV_PLAYLIST_CHANGED, EV_QUEUE_CHANGED, EV_PLAYER_CHANGED, EV_VOLUME_CHANGED,
            EV_OUTPUT_CHANGED, EV_OPTIONS_CHANGED, EV_STICKER_CHANGED, EV_SUBS_CHANGED, EV_MESSAGE_RECEIVED]

    def __init__(self, host='127.0.0.1', port=6600):
        self._host, self._port = host, port
        self._client, self._lock = mpd.MPDClient(), Semaphore(1)

    def disconnect(self):
        while True:
            try:
                self._client.disconnect()

            # already disconnected, ignore it
            except mpd.ConnectionError:
                pass

            # happens when connection is timed out,
            # need to disconnect again
            except IOError:
                continue

            break

    def reconnect(self):
        self.disconnect()

        try:
            self._client.connect(self._host, self._port)

        except (IOError, mpd.ConnectionError) as e:
            return None

        return self._client

    def bulk_do(self, *commands, **options):
        if not commands:
            return

        if len(commands) == 1 and hasattr(commands[0], '__iter__'):
            commands = commands[0]

        commands = map(lambda cmd:
                (cmd.replace('_', ' '), ()) if isinstance(cmd, basestring)
                else (cmd[0].replace('_', ' '), cmd[1:]),
                commands)

        for _ in xrange(0, 2):
            try:
                with self._lock:
                    self._client.command_list_ok_begin()

                    for cmd in commands:
                        self._client._execute(*cmd)

                    return tuple(self._client.command_list_end())

            except (mpd.ConnectionError, mpd.CommandListError, IOError):
                if not self.reconnect():
                    break

        return options.get('defaults') or ([None] * len(commands))

    def do(self, command, *args, **kwargs):
        command = command.replace('_', ' ')

        for _ in xrange(0, 2):
            try:
                with self._lock:
                    return self._client._execute(command, args)

            except (mpd.ConnectionError, IOError):
                if not self.reconnect():
                    break

        return kwargs.get('default', None)


    _wait_client = None
    _wait_client_lock = Semaphore(1)
    @property
    def wait_client(self):
        if not self._wait_client:
            self._wait_client = mpd.MPDClient()
            self._wait_client.connect(self._host, self._port)

        return self._wait_client

    def wait(self, systems=(), timeout=0):
        with self._wait_client_lock:
            return self.wait_client.idle(*systems)
