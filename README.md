# MPD control plugin for Ajenti

This is an [Ajenti][] plugin to control [MPD][] music player.
It also requires [models][] Ajenti plugin.

Install **models** plugin into `/var/lib/ajenti/plugins` along with this plugin and restart **Ajenti**:

```
# git clone https://github.com/kstep/ajenti-models.git /var/lib/ajenti/plugins
# git clone https://github.com/kstep/ajenti-mpd.git /var/lib/ajenti/plugins/mpd
# service restart ajenti
```

Now login to your Ajenti panel and go to new **MPD** menu item in **Software** section. You may need to configure it.

[Ajenti]: http://ajenti.org/
[MPD]: http://www.musicpd.org/
[models]: http://github.com/kstep/ajenti-models
