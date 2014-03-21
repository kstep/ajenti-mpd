from ajenti.api import plugin
from ajenti.api.sensors import Sensor
from ajenti.plugins.dashboard.api import DashboardWidget
from ajenti.ui.binder import Binder

@plugin
class MpdWidget (DashboardWidget):
    name = _('MPD Status')
    icon = 'music'

    def init(self):
        self.append(self.ui.inflate('mpd:widget'))
        Binder(Sensor.find('mpd').value(),
            self.find('mpd')).populate()
