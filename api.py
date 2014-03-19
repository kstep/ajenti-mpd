from ajenti.util import public
from gevent.lock import Semaphore
from datetime import datetime
from mpd import CommandError
import mpd

__all__ = ['ident', 'intbool', 'time', 'timestamp', 'CommandError']
ident = lambda x: x
intbool = lambda v: bool(int(v))
time = lambda t: '%2d:%02d' % (int(t) / 60, int(t) % 60)

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
class Model(object):
    _cast = {}

    def __init__(self, data={}, **kwargs):
        data.update(kwargs)
        for k, v in data.iteritems():
            k = k.replace('-', '_')
            setattr(self, k, self._cast.get(k, ident)(v))

    def get(self, name, default=None):
        return getattr(self, name, default)

    def __setitem__(self, name, value):
        setattr(self, name, value)

    def __repr__(self):
        return repr(self.__dict__)

    EMPTY = None
    class __metaclass__(type):
        def __init__(cls, name, bases, attrs):
            type.__init__(cls, name, bases, attrs)
            cls.EMPTY = cls()

@public
class MPD(object):
    def __init__(self, host='127.0.0.1', port=6600):
        self._host, self._port = host, port
        self._client, self._lock = mpd.MPDClient(), Semaphore(1)

    def reconnect(self):
        try:
            self._client.disconnect()
        except mpd.ConnectionError:
            pass

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

            except mpd.ConnectionError:
                if not self.reconnect():
                    break

        return options.get('defaults') or ([None] * len(commands))

    def do(self, command, *args, **kwargs):
        command = command.replace('_', ' ')

        for _ in xrange(0, 2):
            try:
                with self._lock:
                    return self._client._execute(command, args)

            except mpd.ConnectionError:
                if not self.reconnect():
                    break

        return kwargs.get('default', None)



