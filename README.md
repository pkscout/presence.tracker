# presence.tracker
This python script is designed to run as a service on a Raspberry Pi.  This script checks to see if specified bluetooth devices are in range and send MQTT messages regarding their status.


## PREREQUISITES:
1. You should be running Raspian Buster or later.
1. Python3 is required.


## INSTALLATION:
For the script to work properly, you need to install a few things first:
```
sudo apt install bluetooth libbluetooth-dev
```

You will also need a bluetooth Python library.  The default tracker uses the older pybluez module.  This isn't well maintained any longer and won't work with Python 3.10 or later.
```
pip3 install pybluez
```

There is a Bluetooth LE tracker available as well.  To use that you need to install the Bleak python library.  Bleak is a more modern and supported Bluetooth library, so you should use this if at all possible.
```
pip3 install bleak
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
The tracker type that should be used.  The script also supports a Bluetooth LE tracker by using `ble` for this option.  The Bluetooth LE tracker is coded using the Bleak python module.  Bleak is a more modern and supported Bluetooth library, so you should use that if at all possible.

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
The location of your tracker.  With REST, this is included in the name of the sensor to uniquely identify a device/tracker combination (in case you have more than one tracker in the house).  With MQTT, this is used as a subtopic to differentiate the tracker.

* `home_state = <str>` (default `home`)  
The state that the tracker sends if the device is found.

* `away_state = <str>` (default `not_home`)  
The state that the tracker sends if the device not is found.

* `occupied_device = <str>` (default `occupied_by`)  
The tracker sends an additional message that indicates whether any of the devices were found.  This makes it easier for other systems to determine if anyone is home.  This item is the name of that device.

* `occupied = <str>` (default `somebody`)  
The state that the tracker sends for the `occupied_device` if any devices are found.

* `notoccupied = <str>` (default `nobody`)  
The state that the tracker sends for the `occupied_device` if no devices are found.

* `waittime = <float>` (default `5`)  
The number of minutes the tracker waits before checking for devices again.  You can use decimals, so if you want something under a minute, you can use an entry like `0.5`.

* `bt_timeout = <int>` (default `3`)  
If you are using the standard Bluetooth tracker, this is the amount of time in seconds the bluetooth tracker will wait for a response from the Bluetooth subsystem before aborting.

* `bt_expire = <int>` (default `60`)  
If you are using the Bluetooth LE tracker, this is the amount of time in seconds tracker will cache the results list.  The list is cached because it takes several seconds to generate, so you don't want to have to regenerate it for every device you are tracking.  If you set `waittime` to less than a minute, you will need to reduce this item so that the cache is purged after each check.

* `logbackups = <int>` (default `1`)  
The number of days of logs to keep.

* `debug = <boolean>` (default `False`)  
For debugging you can get a more verbose log by setting this to True.

## A WORD ABOUT BLUETOOTH PRIVACY

If you are using the Bluetooth LE tracker, that uses a more modern version of the Bluetooth protocol that does something called MAC address randomization.  In order to keep unknown devices from tracking you via Bluetooth, devices randomize the MAC address advertised.  While this is great for privacy, it makes it hard to use the device for presence tracking.  To deal with that, you have to pair the device you want to track with the Pi running the presence tracker.  It doesn't have to stay connected (or even reconnect). It just needs to be paired.  That allows the Pi and the device you want to track to exchange some keys so that the Pi can get the actual physical MAC address of the Bluetooth on the tracked device.  Unfortunately, the pairing doesn't always exchange the keys properly, so you might have to unpair and try again.  In my experience, this is very hit or miss.  I had one device exchange keys the first try.  I had another than took a half a dozen tries.

On the Raspberry Pi you need to run the bluetooth tool as root by using `sudo bluetoothctl`.  The "as root" part is very important.  If you don't do that, the keys won't get exchanged properly, and you'll never be able to match the static Bluetooth address in your settings with the tracked device.  Once you do that, issue the following commands:
```
discoverable on
pairable on
agent on
```

From the device you want to track (probably a phone), open up the Bluetooth settings and follow the normal process for pairing a device.  You should see the Raspberry Pi in the list of devices to which you can pair.  During the process, you'll need to confirm you see the same code on the phone as on the Pi.  Answer `yes` on the Pi and accept on your phone.  On the Pi you;ll see a bunch of services registering and then another question confirming that it's OK to add them.  Answer `yes` again.  The devices are now paired.  To finish, issue the following commands:
```
discoverable off
exit
```

You should now be back at the main command prompt.  To test this, go to the presence.tracker folder and run the test script using `python3 test.py`.  You'll get a list back of every device found.  If the key exchange worked, you should see your device name and the actual MAC address in the list somewhere.  If you don't see your device, the keys didn't exchange.  You'll need to remove the device and then pair again.
```
sudo bluetoothctl
paired-devices
```

This will get you a list of the paired devices and their MAC addresses.  With that you can remove the device.
```
remove <MAC ADDRESS>
exit
```

You'all also need to forget the presence tracker device on your phone.  Go back to the beginning of this section and try pairing again.  Keep trying until the `test.py` shows you your device.

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

#### Multiple Trackers in One House

If you're just trying to know whether anyone is home at all, you can use a [bayesian sensor](https://www.home-assistant.io/components/bayesian/) with the `occupied_by` sensor from each tracker to determine if anyone is home.  Make sure to give each tracker it's own unique `tracker_location` in the settings, or the trackers will be updating the same sensors.  For room based detection, you would likely need trackers in every room, and where they overlap you'd need logic to make the best guess as to what room the device is actually in.  
