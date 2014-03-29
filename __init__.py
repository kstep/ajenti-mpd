from ajenti.api import *  # noqa
from ajenti.plugins import *  # noqa


info = PluginInfo(
    title='MPD',
    icon='music',
    dependencies=[
        PluginDependency('main'),
        PluginDependency('models'),
        BinaryDependency('mpd'),
    ],
)


def init():
    import main
