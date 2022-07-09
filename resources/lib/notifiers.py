from resources.lib import url
import json
import re
try:
    import paho.mqtt.publish as publish
    import paho.mqtt.client as mqtt
    has_mqtt = True
except ImportError:
    has_mqtt = False


def _cleanup(item):
    if item:
        return re.sub(r'[^\w]', '_', item.lower())
    return item


class MqttNotifier:
    def __init__(self, config):
        self.MQTTAUTH = {'username': config.Get('mqtt_user'),
                         'password': config.Get('mqtt_pass')}
        self.MQTTHOST = config.Get('host')
        self.MQTTPORT = config.Get('mqtt_port')
        self.MQTTCLIENT = config.Get('mqtt_clientid')
        self.MQTTPATH = config.Get('mqtt_path')
        self.MQTTRETAIN = config.Get('mqtt_retain')
        self.MQTTDISCOVER = config.Get('mqtt_discover')
        self.LOCATION = config.Get('tracker_location')
        self.HOMESTATE = config.Get('home_state')
        self.AWAYSTATE = config.Get('away_state')
        self.CONFIGSENT = []
        self.WHICHTRACKER = config.Get('which_tracker')

    def _mqtt_send(self, mqtt_publish, payload):
        loglines = []
        conn_error = ''
        if has_mqtt:
            try:
                publish.single(mqtt_publish,
                               payload=payload,
                               retain=self.MQTTRETAIN,
                               hostname=self.MQTTHOST,
                               auth=self.MQTTAUTH,
                               client_id=self.MQTTCLIENT,
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

    def Send(self, device, device_state):
        loglines = []
        payload = {}
        friendly_name = device['name']
        if self.LOCATION:
            friendly_name = friendly_name + ' ' + self.LOCATION
        entity_id = _cleanup(device.get('entity_id'))
        if entity_id:
            if self.LOCATION:
                entity_id = entity_id + '_' + _cleanup(self.LOCATION)
            payload['object_id'] = entity_id
        else:
            entity_id = _cleanup(friendly_name)
        mqtt_publish = '%s/%s' % (self.MQTTPATH, entity_id)
        payload['name'] = friendly_name
        payload['state_topic'] = mqtt_publish + '/state'
        payload['payload_home'] = self.HOMESTATE
        payload['payload_not_home'] = self.AWAYSTATE
        payload['source_type'] = self.WHICHTRACKER
        if self.MQTTDISCOVER:
            if not entity_id in self.CONFIGSENT:
                mqtt_config = mqtt_publish + '/config'
                loglines.append('sending config for device %s to %s' %
                                (friendly_name, self.MQTTHOST))
                loglines.extend(self._mqtt_send(
                    mqtt_config, json.dumps(payload)))
                self.CONFIGSENT.append(entity_id)
        loglines.append('sending %s as status for device %s to %s' %
                        (device_state, friendly_name, self.MQTTHOST))
        loglines.extend(self._mqtt_send(
            mqtt_publish + '/state', device_state))
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

    def Send(self, device, device_state):
        friendly_name = device['name']
        entity_id = _cleanup(device['entity_id'])
        if not entity_id:
            entity_id = _cleanup(friendly_name)
        if self.LOCATION:
            friendly_name = friendly_name + ' ' + self.LOCATION
            entity_id = entity_id + '_' + _cleanup(self.LOCATION)
        payload = {'state': device_state, 'attributes': {
            'friendly_name': friendly_name}}
        returned = self.JSONURL.Post('%s%s' %
                                     (self.RESTURL, entity_id),
                                     data=json.dumps(payload))
        return returned(1)
