
import resources.config as config
import os
import time
import traceback
from resources.lib.trackers import BluetoothTracker, BluetoothLETracker
from resources.lib.notifiers import MqttNotifier, HaRestNotifier
from resources.lib.xlogger import Logger


class CheckPresence:

    def __init__(self, lw):
        self.LW = lw
        self.KEEPRUNNING = True
        self.TRACKER = self._pick_tracker(config.Get('which_tracker'))
        self.NOTIFIER = self._pick_notifier(config.Get('which_notifier'))
        self.HOMESTATE = config.Get('home_state')
        self.AWAYSTATE = config.Get('away_state')
        self.OCCUPIEDDEVICE = config.Get('occupied_device')
        self.OCCUPIED = config.Get('occupied')
        self.NOTOCCUPIED = config.Get('not_occupied')

    def Start(self):
        self.LW.log(['starting up CheckPresence'], 'info')
        try:
            while self.KEEPRUNNING and self.TRACKER and self.NOTIFIER:
                occupied_state = self.NOTOCCUPIED
                for device in config.Get('devices'):
                    device_state, loglines = self.TRACKER.GetDeviceStatus(
                        device)
                    self.LW.log(loglines, 'debug')
                    loglines = self.NOTIFIER.Send(device, device_state)
                    self.LW.log(loglines, 'debug')
                config.Reload()
                time.sleep(config.Get('waittime') * 60)
        except KeyboardInterrupt:
            self.KEEPRUNNING = False
        except Exception as e:
            self.KEEPRUNNING = False
            self.LW.log([traceback.format_exc()], 'error')
            print(traceback.format_exc())

    def _pick_tracker(self, whichtracker):
        self.LW.log(['setting up %s tracker' % whichtracker])
        if whichtracker.lower() == 'bluetooth':
            return BluetoothTracker(config=config)
        elif whichtracker.lower() == 'bluetooth_le':
            return BluetoothLETracker(config=config)
        else:
            self.LW.log(['invalid tracker specified'])
            return None

    def _pick_notifier(self, whichnotifier):
        self.LW.log(['setting up %s notifier' % whichnotifier])
        if whichnotifier.lower() == 'mqtt':
            return MqttNotifier(config=config)
        elif whichnotifier.lower() == 'harest':
            return HaRestNotifier(config=config)
        else:
            self.LW.log(['invalid notifier specified'])
            return None


class Main:

    def __init__(self, thepath):
        self.LW = Logger(logfile=os.path.join(os.path.dirname(thepath), 'data', 'logs', 'logfile.log'),
                         numbackups=config.Get('logbackups'), logdebug=config.Get('debug'))
        self.LW.log(['script started, debug set to %s' %
                    str(config.Get('debug'))], 'info')
        self.CHECKPRESENCE = CheckPresence(self.LW)
        self.CHECKPRESENCE.Start()
        self.LW.log(['closing down CheckPresence'], 'info')
