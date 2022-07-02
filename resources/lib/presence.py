
import resources.config as config
import os
import time
import traceback
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
from resources.lib.trackers import BluetoothTracker
from resources.lib.xlogger import Logger


class CheckPresence:

    def __init__(self, lw):
        self.LW = lw
        self.KEEPRUNNING = True
        self.TRACKER = self._pick_tracker(config.Get('which_traker'))
        self.MQTTAUTH = {'username': config.Get(
            'mqtt_user'), 'password': config.Get('mqtt_pass')}
        self.MQTTHOST = config.Get('mqtt_host')
        self.MQTTPORT = config.Get('mqtt_port')
        self.MQTTCLIENT = config.Get('mqtt_clientid')
        self.MQTTPATH = config.Get('mqtt_path')
        self.LOCATION = config.Get('tracker_location')
        self.HOMESTATE = config.Get('home_state')
        self.AWAYSTATE = config.Get('away_state')
        self.OCCUPIEDDEVICE = config.Get('occupied_device')
        self.OCCUPIED = config.Get('occupied')
        self.NOTOCCUPIED = config.Get('not_occupied')

    def Start(self):
        self.LW.log(['starting up CheckPresence'], 'info')
        try:
            while self.KEEPRUNNING and self.TRACKER:
                occupied_state = self.NOTOCCUPIED
                for device in config.Get('devices'):
                    device_state = self.TRACKER.GetDeviceStatus(device)
                    self._publish(device['name'], device_state)
                    if device_state == self.HOMESTATE:
                        occupied_state = self.OCCUPIED
                self._publish(self.OCCUPIEDDEVICE, occupied_state)
                time.sleep(config.Get('waittime') * 60)
                config.Reload()
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
        else:
            self.LW.log(['invalid tracker specified'])
            return None

    def _publish(self, device_name, device_state):
        self.LW.log(['sending information on device %s with status of %s' %
                    (device_name, device_state)], 'debug')
        try:
            publish.single('%s/%s/%s' % (self.MQTTPATH, self.LOCATION, device_name),
                           payload=device_state,
                           hostname=self.MQTTHOST,
                           client_id=self.MQTTCLIENT,
                           auth=self.MQTTAUTH,
                           port=self.MQTTPORT,
                           protocol=mqtt.MQTTv311)
        except ConnectionRefusedError:
            self.LW.log(["MQTT connection refused"], 'error')
        except ConnectionAbortedError:
            self.LW.log(["MQTT connection aborted"], 'error')
        except ConnectionResetError:
            self.LW.log(["MQTT connection reset"], 'error')
        except ConnectionError:
            self.LW.log(["MQTT connection error"], 'error')


class Main:

    def __init__(self, thepath):
        self.LW = Logger(logfile=os.path.join(os.path.dirname(thepath), 'data', 'logs', 'logfile.log'),
                         numbackups=config.Get('logbackups'), logdebug=config.Get('debug'))
        self.LW.log(['script started, debug set to %s' %
                    str(config.Get('debug'))], 'info')
        self.CHECKPRESENCE = CheckPresence(self.LW)
        self.CHECKPRESENCE.Start()
        self.LW.log(['closing down CheckPresence'], 'info')
