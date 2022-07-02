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
pip3 install paho-mqtt
```

It is recommended you install this script in `/home/pi`.  The service file you'll install later assumes this, so if you install it somewhere else, you'll need to edit presence.tracker.service.


## CONFIGURATION:
For the script to do anything, you need to create a settings file.  In the script directory if there is not yet a `data` folder, create it and then create a file called `settings.py`.  It must have the following at a minimum:
```
devices = [{"name": "device1", "mac": "09:76:C5:52:2E:E6"},
           {"name": "device2", "mac": "04:35:C6:19:C7:3D"}]
mqtt_host = '127.0.0.1'
```

There are a number of options available:

* `devices = <list>` (default `[]`)  
This is a list of devices for which to scan.  The device name can be whatever you like as long as you don't use spaces or reserved characters.  The mac item is the Bluetooth MAC address for the device.

* `mqtt_host = <str>` (default `127.0.0.1`)  
The IP address of your MQTT broker.

* `mqtt_port = <int>` (default `1883`)  
The port of your MQTT broker.

* `mqtt_user = <str>` (default `mqtt`)  
The username needed if authentication is required for your MQTT broker.

* `mqtt_pass = <str>` (default `mqtt_password`)  
The password needed if authentication is required for your MQTT broker.

* `mqtt_clientid = <str>` (default `presencetracker`)  
The client ID provided to the MQTT broker.

* `mqtt_path = <str>` (default `PresenceTracker`)  
The root topic send to your MQTT broker.

* `tracker_location = <str>` (default `Main`)  
The location of your tracker.  This is used as a subtopic so that you can have multiple trackers running on one location if needed.

* `which_tracker = <str>` (default `bluetooth`)  
The tracker type that should be used.  Currently bluetooth is the only supported tracker, but it is possible to add other tracker types.

* `home_state = <str>` (default `home`)  
The state that the tracker sends if the device is found.

* `away_state = <str>` (default `not home`)  
The state that the tracker sends if the device not is found.

* `occupied_device = <str>` (default `occupied_by`)  
The tracker sends back an additional message that indicates whether any of the devices were found.  This makes it easier for other systems to determine if anyone is home.  This item is the name of that device.

* `occupied = <str>` (default `somebody`)  
The state that the tracker sends for the `occupied_device` if any devices are found.

* `notoccupied = <str>` (default `nobody`)  
The state that the tracker sends for the `occupied_device` if no devices are found.


* `logbackups = <int>` (default `1`)  
The number of days of logs to keep.

* `debug = <boolean>` (default `False`)  
For debugging you can get a more verbose log by setting this to True.


## USAGE:
To run from the terminal (for testing): `python3 /home/pi/presence.tracker/execute.py`  
To exit: CNTL-C

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
To add the sensor to Home Assistant use the [MQTT Sensor Component](https://www.home-assistant.io/components/sensor.mqtt/) a sample configuration is below (based on default settings plus the sample devices):

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
