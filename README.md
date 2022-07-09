# presence.tracker
This python script is designed to run as a service on a Raspberry Pi.  This script checks to see if specified bluetooth devices are in range and send REST messages to Home Assistant or MQTT messages to a broker regarding their status.

## PREREQUISITES:
1. You should be running Raspian Buster or later.
1. Python3 is required.

## OTHER PLATFORMS
If you using the BluetoothLE tracker option, this will work on OSX and probably Windows too.  On OSX you have to use the devices UUID instead of MAC address.  See the Bleak Python docs for more information on that.

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
The tracker type that should be used.  The script also supports a Bluetooth LE tracker by using `bluetooth_le` for this option.  The Bluetooth LE tracker is coded using the Bleak python module.  Bleak is a more modern and supported Bluetooth library, so you should use that if at all possible.

* `which_notifier = <str>` (default `harest`)  
The notifier to use.  If you leave this as the default, you must specific a Home Assistant token for use with the rest API in the `rest_token` setting.  To use an MQTT broker, change this to `mqtt`.

* `devices = <list>` (default `[]`)  
This is a list of devices for which to scan.  The device name can be whatever you like as long as you don't use spaces or reserved characters.  The mac item is the Bluetooth MAC address for the device.

* `host = <str>` (default `127.0.0.1`)  
The IP address of your Home Assistant server or MQTT broker.

* `rest_port = <int>` (default `8123`)  
The port of your Home Assistant server.

* `rest_token = <str>` (default `emptry string`)  
The API token from your Home Assistant server.  For information on generating a token, see [Home Assistant User Profiles](https://www.home-assistant.io/docs/authentication/#your-account-profile).

* `mqtt_port = <int>` (default `1883`)  
The port of your MQTT broker.

* `mqtt_user = <str>` (default `mqtt`)  
The username needed if authentication is required for your MQTT broker.

* `mqtt_pass = <str>` (default `mqtt_password`)  
The password needed if authentication is required for your MQTT broker.

* `mqtt_clientid = <str>` (default `presencetracker`)  
The client ID provided to the MQTT broker.

* `mqtt_path = <str>` (default `homeassistant/presence_tracker`)  
The root topic sent to your MQTT broker.  The default is configured so that you can use [MQTT Discovery](https://www.home-assistant.io/docs/mqtt/discovery/) with Home Assistant.

* `mqtt_discover = <boolean` (default `True`)  
This tells presence tracker whether or not to send the presence_tracker config to Home Assistant.  If you set this to `False`, Home Assistant will not automatically create entities.

* `tracker_location = <str>` (default `empty string`)  
The location of your tracker.  This is included in the name of the sensor to uniquely identify a device/tracker combination (in case you have more than one presence tracker in the house).

* `home_state = <str>` (default `home`)  
The state that the tracker sends if the device is found.

* `away_state = <str>` (default `not_home`)  
The state that the tracker sends if the device not is found.

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

There is no further configuration required in home assistant.  The devices and occupancy state will appear in your home assistant setup.  The sensor will have a name like `sensor.device1_location` with a friendly name of `Device 1 Location`.

Note that after a restart of Home Assistant, these sensors will either show as unavailable or disappear all together.  They will become available and/or reappear once the presence tracker sends its next status update.

#### MQTT

By default, the MQTT notifier uses [MQTT Discovery](https://www.home-assistant.io/docs/mqtt/discovery/) to create presence_tracker entities in Home Assistant.  If you turn that off, you can manually create sensors in Home Assistant use the [MQTT Sensor Component](https://www.home-assistant.io/components/sensor.mqtt/). You should also change the `mqtt_path` to something else (like `PresenceTracker/`.  A sample configuration is below (based on default settings plus the sample devices):

```yaml
mqtt:
  sensor:
    - state_topic: "PresenceTracker/device1"
      name: "Device 1 Presence"
    - state_topic: "PresenceTracker/device2"
      name: "Device 2 Presence"
```

#### Using with Home Assistant Presence

If you want to use the built-in home assistant presence features, you have to have presence trackers for each device and assign the new presence tracker(s) to a person.

If you are using the REST notifier or turn of MQTT Discovery in the MQTT notifier, you also have to create an automation to update the presence trackers.  To manually create presence trackers you need to add them to the `known_devices.yaml` file (or create the file if it doesn't exist) in your Home Assistant config directory.  The MAC entry doesn't really matter, but I use the same MAC address as the device just to keep track of things.
```
device1_main:
  name: Device 1 Main
  mac: 09:76:C5:52:2E:E6
  track: true

device2_main:
  name: Device 2 Main
  mac: 04:35:C6:19:C7:3D
  track: true
```

This will create two presence trackers named `device_tracker.device1_main` and `device_tracker.device2_main`.

The automation uses the `device_tracker.see` service to update a device tracker.  As written, any update to any of the REST sensors will trigger an update of them all (the logic is easier, and there's no harm in updating something with the same status it already has).
```
alias: Set Presence
description: ''
trigger:
  - platform: state
    entity_id:
      - sensor.device1_main_presence
      - sensor.device2_main_presence
condition: []
action:
  - service: device_tracker.see
    data:
      dev_id: device1_main
      location_name: '{{ states(''sensor.device1_main_presence'') }}'
  - service: device_tracker.see
    data:
      dev_id: device2_main
      location_name: '{{ states(''sensor.device2_main_presence'') }}'
mode: single
```

Once this is running and the device trackers are assigned to a person, you'll be able to use all the built-in Home Assistant presence features.  For instance, I use the `numeric state` of the `Home` entity to determine if anyone is home.

#### Multiple Trackers in One House

If you are using the Home Assistant Presence features, you can just add the devices from each pi to the right person.  A person is considered home as long as at least one of their devices is home.  If you aren't using the presence features, you will probably need an automation with some logic to change the state of a switch to determine occupancy.
