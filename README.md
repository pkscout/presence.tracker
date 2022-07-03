# presence.tracker
This python script is designed to run as a service on a Raspberry Pi.  This script checks to see if specified bluetooth devices are in range and send MQTT messages regarding their status.


## PREREQUISITES:
1. You should be running Raspian Buster or later.
1. Python3 is required.


## INSTALLATION:
For the script to work properly, you need to install a few things first:
```
sudo apt install bluetooth libbluetooth-dev
pip3 install pybluez
```

If you are going to use an MQTT broker to communicate status, you will also need the following:
```
pip3 install paho-mqtt
```

It is recommended you install this script in `/home/pi`.  The service file you'll install later assumes this, so if you install it somewhere else, you'll need to edit presence.tracker.service.


## CONFIGURATION:
For the script to do anything, you need to create a settings file.  In the script directory if there is not yet a `data` folder, create it and then create a file called `settings.py`.  It must have the following at a minimum:
```
devices = [{"name": "device1", "mac": "09:76:C5:52:2E:E6"},
           {"name": "device2", "mac": "04:35:C6:19:C7:3D"}]
host = '127.0.0.1'
rest_token = 'your HA long lived token'
```

For more information about the HA long lived token, please see `rest_token` below.  If you are using an MQTT broker, you do not need to include `rest_token` in the settings.  There are a number of options available in the settings:

* `which_tracker = <str>` (default `bluetooth`)  
The tracker type that should be used.  Currently bluetooth is the only supported tracker, but it is possible to add other tracker types.

* `which_notifier = <str>` (default `harest`)  
The notifier to use.  If you leave this as the default, you must specific a Home Assistant token for use with the rest API in the `rest_token` setting.  To use an MQTT broker, change this to `mqtt`.

* `devices = <list>` (default `[]`)  
This is a list of devices for which to scan.  The device name can be whatever you like as long as you don't use spaces or reserved characters.  The mac item is the Bluetooth MAC address for the device.

* `host = <str>` (default `127.0.0.1`)  
The IP address of your Home Assistant server or MQTT broker.

* `rest_port = <int>` (default `8123`)  
The port of your Home Assistant server.

* `rest_token = <str>` (default `None`)  
The API token from your Home Assistant server.  For information on generating a token, see [Home Assistant User Profiles](https://www.home-assistant.io/docs/authentication/#your-account-profile).

* `mqtt_port = <int>` (default `1883`)  
The port of your MQTT broker.

* `mqtt_user = <str>` (default `mqtt`)  
The username needed if authentication is required for your MQTT broker.

* `mqtt_pass = <str>` (default `mqtt_password`)  
The password needed if authentication is required for your MQTT broker.

* `mqtt_clientid = <str>` (default `presencetracker`)  
The client ID provided to the MQTT broker.

* `mqtt_path = <str>` (default `PresenceTracker`)  
The root topic sent to your MQTT broker.

* `tracker_location = <str>` (default `Main`)  
The location of your tracker.  This is used as a subtopic so that you can have multiple trackers running on one home if needed.

* `home_state = <str>` (default `home`)  
The state that the tracker sends if the device is found.

* `away_state = <str>` (default `not home`)  
The state that the tracker sends if the device not is found.

* `occupied_device = <str>` (default `occupied_by`)  
The tracker sends an additional message that indicates whether any of the devices were found.  This makes it easier for other systems to determine if anyone is home.  This item is the name of that device.

* `occupied = <str>` (default `somebody`)  
The state that the tracker sends for the `occupied_device` if any devices are found.

* `notoccupied = <str>` (default `nobody`)  
The state that the tracker sends for the `occupied_device` if no devices are found.

* `logbackups = <int>` (default `1`)  
The number of days of logs to keep.

* `debug = <boolean>` (default `False`)  
For debugging you can get a more verbose log by setting this to True.


## USAGE:

### FROM THE COMMAND LINE

To run from the terminal (for testing): `python3 /home/pi/presence.tracker/execute.py`  
To exit: CNTL-C

### AS A SERVICE

Running from the terminal is useful during initial testing, but once you know it's working the way you want, you should set it to autostart.  To do that you need to copy rpiwsl.service.txt to the systemd directory, change the permissions, and configure systemd. From a terminal window:
```
sudo cp -R /home/pi/presence.tracker/presence.tracker.service.txt /lib/systemd/system/presence.tracker.service
sudo chmod 644 /lib/systemd/system/presence.tracker.service
sudo systemctl daemon-reload
sudo systemctl enable presence.tracker.service
```

From now on the script will start automatically after a reboot.  If you want to manually stop, start, or restart the service you can do that as well. From a terminal window:
```
sudo systemctl stop presence.tracker.service
sudo systemctl start presence.tracker.service
sudo systemctl restart presence.tracker.service
```

If you change anything in the `settings.py` file, you will need to restart the service.


### USING WITH HOME ASSISTANT

#### REST

By default the presence tracker is set to send its information to Home Assistant via a [REST API call](https://developers.home-assistant.io/docs/api/rest/).  As noted in that link, if you are not using the `frontend` in your setup, you will need to add the API integration.  For this to work, you **must** also provide a Long Lived Token via the `rest_token` option in the settings file.

There is no further configuration required in home assistant.  The devices and occupancy state will appear in your home assistant setup.  The sensor will have a name like `sensor.device1_main_presence` with a friendly name of `Device 1 Main Presence`.

Note that after a restart of Home Assistant, these sensors will either show as unavailable or disappear all together.  They will become available and/or reappear once the presence tracker sends its next status update.

#### MQTT

To add the sensor to Home Assistant use the [MQTT Sensor Component](https://www.home-assistant.io/components/sensor.mqtt/). A sample configuration is below (based on default settings plus the sample devices):

```yaml
mqtt:
  sensor:
    - state_topic: "PresenceTracker/Main/device1"
      name: "Device 1 Presence"
    - state_topic: "PresenceTracker/Main/device2"
      name: "Device 2 Presence"
    - state_topic: "PresenceTracker/Main/occupied_by"
      name: "House Occupied By"
```

Using the above sensor in conjuction with other device trackers and a [bayesian sensor](https://www.home-assistant.io/components/bayesian/), can make a pretty accurate device tracker.
