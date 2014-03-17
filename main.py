from ajenti.api import plugin
from ajenti.plugins.main.api import SectionPlugin
from ajenti.ui.binder import Binder
from ajenti.ui import on
import mpd

class Model(object):
    def __init__(self, data={}, **kwargs):
        data.update(kwargs)
        for k, v in data.iteritems():
            setattr(self, k, v)

    def get(self, name, default=None):
        return getattr(self, name, default)

    def __repr__(self):
        return repr(self.__dict__)

class Song(Model):
    def __init__(self, data={}, **kwargs):
        if not isinstance(data, dict):
            data = {'title': str(data)}
        else:
            data.setdefault('title', '')

        Model.__init__(self, data, **kwargs)
        self.icon = 'music'

NO_SONG = Song()

class Status(Model):
    pass

@plugin
class MpdPlugin(SectionPlugin):
    def init(self):
        self._client = mpd.MPDClient()

        # meta-data
        self.title = 'MPD'
        self.icon = 'music'
        self.category = "Software"

        self.append(self.ui.inflate('mpd:main'))

        # data-bindings
        self.playlist = []
        self.song = NO_SONG
        self.status = Status()

        def post_item_bind(obj, collection, item, ui):
            ui.find('play').on('click', self.play, item.pos)

        def delete_item(item, collection):
            self.remove(item.pos)

        self.find('playlist').post_item_bind = post_item_bind
        self.find('playlist').delete_item = delete_item


    def on_first_page_load(self):
        self.binder = Binder(self, self.find('mpd'))
        self.refresh()

    @on('refresh', 'click')
    def refresh(self):
        self.playlist = map(lambda s: Song(pos=s[0], title=s[1]), enumerate(self.mpd_do('playlist')))
        self.status = Status(self.mpd_do('status'))
        self.song = Song(self.mpd_do('currentsong'))

        try:
            self.playlist[int(self.status.song)] = self.song
            self.song.icon = 'play'
        except AttributeError:
            pass

        if self.status.state == 'play':
            self.find('play').visible = False
            self.find('pause').visible = True

        else:
            self.find('play').visible = True
            self.find('pause').visible = False

        self.binder.populate()

    def remove(self, pos):
        self.mpd_do('delete', pos)
        self.refresh()

    #@on('reorder', 'click')
    #def reorder(self):
        #self.binder.update()

    @on('play', 'click')
    def play(self, pos=None):
        if pos is None:
            self.mpd_do('play')
        else:
            self.mpd_do('play', pos)

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

    def mpd_do(self, command, *args):
        command = command.replace('_', ' ')
        try:
            return self._client._execute(command, args)

        except mpd.ConnectionError:
            self.reconnect()
            return self._client._execute(command, args)

    def reconnect(self):
        try:
            self._client.disconnect()
        except mpd.ConnectionError:
            pass

        self._client.connect('127.0.0.1', 6600)
        return self._client
