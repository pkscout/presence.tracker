from resources.lib import url
import json
try:
    import paho.mqtt.publish as publish
    import paho.mqtt.client as mqtt
    has_mqtt = True
except ImportError:
    has_mqtt = False


class MqttNotifier:
    def __init__(self, config):
        self.MQTTAUTH = {'username': config.Get(
            'user'), 'password': config.Get('pass')}
        self.MQTTHOST = config.Get('host')
        self.MQTTPORT = config.Get('mqtt_port')
        self.MQTTCLIENT = config.Get('mqtt_clientid')
        self.MQTTPATH = config.Get('mqtt_path')
        self.LOCATION = config.Get('tracker_location')

    def Send(self, device_name, device_state):
        loglines = []
        conn_error = ''
        if has_mqtt:
            loglines.append('sending information on device %s with status of %s' %
                            (device_name, device_state))
            try:
                publish.single('%s/%s/%s' % (self.MQTTPATH, self.LOCATION, device_name),
                               payload=device_state,
                               hostname=self.MQTTHOST,
                               client_id=self.MQTTCLIENT,
                               auth=self.MQTTAUTH,
                               port=self.MQTTPORT,
                               protocol=mqtt.MQTTv311)
            except ConnectionRefusedError:
                conn_error = 'refused'
            except ConnectionAbortedError:
                conn_error = 'aborted'
            except ConnectionResetError:
                conn_error = 'reset'
            except ConnectionError:
                conn_error = 'error'
            if conn_error:
                loglines.append('MQTT connection %s' % conn_error)
        else:
            loglines.append(
                'MQTT python libraries are not installed, no message sent')
        return loglines


class HaRestNotifier:
    def __init__(self, config):
        self.LOCATION = config.Get('tracker_location')
        headers = {}
        headers['Content-Type'] = 'application/json'
        headers['Accept'] = 'application/json'
        headers['Authorization'] = 'Bearer %s' % config.Get('rest_token')
        self.JSONURL = url.URL('json', headers=headers)
        self.RESTURL = 'http://%s:%s/api/states/sensor.' % (config.Get(
            'host'), config.Get('rest_port'))

    def Send(self, device_name, device_state):
        loglines = []
        payload = {'state': device_state, 'attributes': {
            'friendly_name': '%s %s Presence' % (device_name, self.LOCATION)}}
        status, loglines, results = self.JSONURL.Post('%s%s_%s_presence' %
                                                      (self.RESTURL,
                                                       self._urlprep(
                                                           device_name),
                                                       self._urlprep(self.LOCATION)),
                                                      data=json.dumps(payload))
        return loglines

    def _urlprep(self, item):
        return item.lower().replace(' ', '_')
