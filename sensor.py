from ajenti.api import *
from ajenti.api.sensors import Sensor
import mpd

@plugin
class MpdSensor (Sensor):
    id = 'mpd'
    timeout = 5

    def init(self):
        super(MpdSensor, self).init()
        self._client = mpd.MPDClient()

    def measure(self, conn=None):
        retry = True
        while True:
            try:
                self._client.command_list_ok_begin()
                self._client.status()
                self._client.currentsong()
                status, song = self._client.command_list_end()
                return {'status': status, 'song': song}

            except mpd.ConnectionError:
                if not (retry and self.reconnect()):
                    return {'status': {}, 'song': {}}
                retry = False

    _connected = True
    def reconnect(self):
        try:
            self._client.disconnect()
        except mpd.ConnectionError:
            pass

        try:
            self._client.connect('127.0.0.1', 6600)

        except (IOError, mpd.ConnectionError) as e:
            return None

        return self._client
