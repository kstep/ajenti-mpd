from ajenti.util import public
from gevent.lock import Semaphore
import mpd

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

    def wait(self, systems=(), timeout=0):
        for _ in xrange(0, 2):
            try:
                with self._lock:
                    return self._client.idle(*systems)

            except (mpd.ConnectionError, IOError):
                if not self.reconnect():
                    break

