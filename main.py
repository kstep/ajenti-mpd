# -*- encoding: utf-8 -*-

from ajenti.api import *  # noqa
from ajenti.plugins import *  # noqa
from ajenti.plugins.mpd.models import *  # noqa
from ajenti.plugins.mpd.api import MPD, CommandError
from ajenti.plugins.main.api import SectionPlugin
from ajenti.ui.binder import Binder
from ajenti.ui import on
from itertools import izip, ifilter, imap, count
from gevent import sleep
from urllib2 import urlopen
from contextlib import closing
import os

@plugin
class MpdPlugin(SectionPlugin):
    def bindui(self, ui_id, method_name):
        def decorator(method):
            setattr(self.find(ui_id), method_name, method)
            return method
        return decorator

    def init(self):
        self._mpd = MPD()

        # meta-data
        self.title = 'MPD'
        self.icon = 'music'
        self.category = _("Software")

        self.append(self.ui.inflate('mpd:main'))

        # data-bindings
        self.playlist = []
        self.playlists = []
        self.outputs = []
        self.library = []
        self.taxonomy = {'artists': [], 'albums': [], 'genres': [], 'artist': '', 'album': '', 'genre': ''}
        self.song = Song()
        self.status = Status()

        self.init_ui_bindings()


    def init_ui_bindings(self):
        @self.bindui('playlist', 'post_item_bind')
        def post_item_bind(obj, collection, item, ui):
            ui.find('play').on('click', self.play, item)

        @self.bindui('playlist', 'delete_item')
        def delete_item(item, collection):
            self.remove(item)

        @self.bindui('playlists', 'add_item')
        def add_playlist(item, collection):
            for i in count(1):
                try:
                    self._mpd.do('save', 'Untitled %d' % i)
                except CommandError:
                    continue
                else:
                    break

            self.refresh()

        @self.bindui('playlists', 'delete_item')
        def delete_playlist(item, collection):
            self._mpd.do('rm', item.playlist)
            self.refresh()

        @self.bindui('playlists', 'post_item_bind')
        def post_playlist_bind(obj, collection, item, ui):
            ui.find('load').on('click', lambda *args: self._mpd.do(*args) or self.refresh(), 'load', item.playlist)
            #ui.find('clear').on('click', self._mpd.do, 'playlistclear', item.playlist)

        @self.bindui('outputs', 'post_item_bind')
        def post_output_bind(obj, collection, item, ui):
            ui.find('enabled').on('click', self.toggleoutput, item)

        @self.bindui('library', 'post_item_bind')
        def post_library_bind(obj, collection, item, ui):
            ui.find('add').on('click', self.add, item.file)

    @on('tabs', 'switch')
    def tab_switch(self):
        if self.find('tabs').active == 2:  # library tab
            #self.library = imap(Song, ifilter(lambda s: 'file' in s, self._mpd.do('listallinfo', default=[])))
            self.taxonomy.update(
                    imap(lambda v: (v[0], ['* All ' + v[0] + ' *'] + v[1]),
                    izip(
                        ('artists', 'albums', 'genres'),
                        self._mpd.bulk_do([
                            ('list', 'artist'),
                            ('list', 'album'),
                            ('list', 'genre')
                            ], defaults=([], [], [])))
                        ))
            self.binder.populate()

    @on('search', 'click')
    def search(self, add=False):
        self.binder.update()

        filter = []
        for f in ('artist', 'album', 'genre'):
            if self.taxonomy[f] and not self.taxonomy[f].startswith('* All '):
                filter.append(f)
                filter.append(self.taxonomy[f])

        if add and not filter:
            self.context.notify('error', _('Can not add all library! Select some filters first.'))
            return

        self.library = map(Song,
                (self._mpd.do('findadd' if add else 'find', *filter) or []) if filter
                else ifilter(lambda s: 'file' in s, self._mpd.do('listallinfo')))
        self.binder.populate()

    @on('searchadd', 'click')
    def searchadd(self):
        self.search(add=True)
        self.refresh()

    @on('rename', 'click')
    def rename_playlists(self):
        old_names = map(lambda p: p.playlist, self.playlists)
        self.binder.update()
        new_names = map(lambda p: p.playlist, self.playlists)

        self._mpd.bulk_do(
                imap(lambda p: ('rename',) + p,
                    ifilter(lambda p: p[0] != p[1],
                        izip(old_names, new_names))))

        self.refresh()


    def on_first_page_load(self):
        self.binder = Binder(self, self.find('mpd'))
        self.refresh()
        #self.context.session.spawn(self.worker)

    def worker(self):
        while True:
            self.refresh()
            sleep(5)

    def add(self, *urls):
        if not urls:
            return

        def readfile(url):
            with closing(urlopen(url) if url.startswith(('http://', 'https://')) else open(url, 'r')) as f:
                return f.read().splitlines()

        clean_playlist = lambda lines: ifilter(None, imap(str.strip, imap(str, lines)))
        parse_null = lambda url: (url,)

        parsers = {
                '.m3u': lambda url: ifilter(lambda line: not line.startswith('#'), readfile(url)),
                '.pls': lambda url: imap(lambda line: line.split('=')[1], ifilter(lambda line: line.startswith('File'), readfile(url))),
                }

        urls = imap(lambda url: clean_playlist(parsers.get(os.path.splitext(url)[1], parse_null)(url)), urls)

        cmds = (('addid', url) for _ in urls for url in _)

        try:
            self._mpd.bulk_do(cmds)

        except CommandError:
            self.context.notify('error', _('Songs not found'))

        else:
            self.refresh()

    @on('consume', 'click')
    def toggleconsume(self):
        self._mpd.do('consume', int(not self.status.consume))
        self.refresh()

    @on('single', 'click')
    def togglesingle(self):
        self._mpd.do('single', int(not self.status.single))
        self.refresh()

    @on('random', 'click')
    def togglerandom(self):
        self._mpd.do('random', int(not self.status.random))
        self.refresh()

    @on('repeat', 'click')
    def togglerepeat(self):
        self._mpd.do('repeat', int(not self.status.repeat))
        self.refresh()

    @on('add', 'click')
    def open_add_dialog(self):
        self.find('add_dialog').visible = True

    @on('add_dialog', 'button')
    def submit_add_dialog(self, button):
        dialog = self.find('add_dialog')
        dialog.visible = False
        if button == 'add':
            self.add(*dialog.find('new_song_url').value.strip().splitlines())

    @on('refresh', 'click')
    def refresh(self):
        playlist, status, song, playlists, outputs = self._mpd.bulk_do(
                'playlistinfo',
                'status',
                'currentsong',
                'listplaylists',
                'outputs',
                defaults=([], {}, {}, [], []))
        self.playlist = map(Song, playlist)
        self.status = Status(status)
        self.song = Song(song)
        self.playlists = map(Playlist, playlists)
        self.outputs = map(Output, outputs)

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
        self._mpd.do('disableoutput' if output.outputenabled else 'enableoutput', output.outputid)
        self.refresh()

    @on('voldown', 'click')
    def voldown(self, delta=10):
        self._mpd.do('volume', -delta)
        self.refresh()

    @on('volup', 'click')
    def volup(self, delta=10):
        self._mpd.do('volume', delta)
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
        self._mpd.do('setvol', value)
        self.refresh()

    def remove(self, song):
        self._mpd.do('deleteid', song.id)
        self.refresh()

    #@on('reorder', 'click')
    #def reorder(self):
        #self.binder.update()

    @on('update', 'click')
    def update(self):
        num = self._mpd.do('update')
        if num:
            self.context.notify('info', _('Update #%s started...') % num)

    @on('play', 'click')
    def play(self, song=None):
        if song is None:
            self._mpd.do('play')
        else:
            self._mpd.do('playid', song.id)

        self.refresh()

    @on('pause', 'click')
    def pause(self):
        self._mpd.do('pause')
        self.refresh()

    @on('stop', 'click')
    def stop(self):
        self._mpd.do('stop')
        self.refresh()

    @on('prev', 'click')
    def prev(self):
        self._mpd.do('previous')
        self.refresh()

    @on('next', 'click')
    def next(self):
        self._mpd.do('next')
        self.refresh()

    @on('clear', 'click')
    def clear(self):
        self._mpd.do('clear')
        self.refresh()

