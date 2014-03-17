from ajenti.api import *  # noqa
from ajenti.plugins import *  # noqa


info = PluginInfo(
    title='MPD',
    icon='music',
    dependencies=[
        PluginDependency('main'),
        BinaryDependency('mpd'),
    ],
)


def init():
    import main
