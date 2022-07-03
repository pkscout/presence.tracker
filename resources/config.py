import sys
defaults = {'waittime': 5,
            'which_traker': 'bluetooth',
            'which_notifier': 'harest',
            'home_state': 'home',
            'away_state': 'not home',
            'occupied_device': 'occupied_by',
            'occupied': 'somebody',
            'not_occupied': 'nobody',
            'tracker_location': 'Main',
            'bt_timeout': 3,
            'devices': [],
            'host': '127.0.0.1',
            'rest_port': 8123,
            'rest_token': '',
            'mqtt_user': 'mqtt',
            'mqtt_pass': 'mqtt_password',
            'mqtt_clientid': 'presencetracker',
            'mqtt_port': 1883,
            'mqtt_path': 'PresenceTracker',
            'logbackups': 1,
            'debug': False,
            'testmode': False}

try:
    import data.settings as overrides
    has_overrides = True
except ImportError:
    has_overrides = False
if sys.version_info < (3, 0):
    _reload = reload
elif sys.version_info >= (3, 4):
    from importlib import reload as _reload
else:
    from imp import reload as _reload


def Reload():
    if has_overrides:
        _reload(overrides)


def Get(name):
    setting = None
    if has_overrides:
        setting = getattr(overrides, name, None)
    if not setting:
        setting = defaults.get(name, None)
    return setting
