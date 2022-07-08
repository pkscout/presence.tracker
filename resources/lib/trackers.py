import random
import time
try:
    import bluetooth
    has_bt = True
except ImportError:
    has_bt = False
try:
    import asyncio
    from bleak import BleakScanner
    has_btle = True
except:
    has_btle = False


def _test_mode(homestate, awaystate):
    loglines = ['in test mode, sending back random result']
    result = random.randint(0, 1)
    if result == 1:
        return homestate, loglines
    else:
        return awaystate, loglines


class BluetoothLETracker:
    def __init__(self, config):
        self.TESTMODE = config.Get('testmode')
        self.HOMESTATE = config.Get('home_state')
        self.AWAYSTATE = config.Get('away_state')
        self.EXPIRECACHE = config.Get('bt_expire')
        self.ADDRESSLIST = []
        self.TIMESTAMP = time.time()

    async def _get_device_list(self):
        now = time.time()
        if (now - self.TIMESTAMP) > self.EXPIRECACHE or not self.ADDRESSLIST:
            self.ADDRESSLIST = []
            devices = await BleakScanner.discover()
            for device in devices:
                self.ADDRESSLIST.append(device.address)
            self.TIMESTAMP = now

    def GetDeviceStatus(self, device):
        loglines = []
        if self.TESTMODE:
            return _test_mode(self.HOMESTATE, self.AWAYSTATE)
        elif has_btle:
            mac = device.get('mac')
            if mac:
                loglines.append('looking for %s in:' % mac)
                loop = asyncio.get_event_loop()
                loop.run_until_complete(self._get_device_list())
                loglines.append(self.ADDRESSLIST)
                if mac in self.ADDRESSLIST:
                    loglines.append('device found')
                    return self.HOMESTATE, loglines
                else:
                    loglines.append('device not found')
                    return self.AWAYSTATE, loglines
            else:
                loglines.append('no MAC address in device information')
        loglines.append('bleak python module unavialable or not loaded')
        return 'error', loglines


class BluetoothTracker:
    def __init__(self, config):
        self.TESTMODE = config.Get('testmode')
        self.HOMESTATE = config.Get('home_state')
        self.AWAYSTATE = config.Get('away_state')
        self.TIMEOUT = config.Get('bt_timeout')

    def GetDeviceStatus(self, device):
        loglines = []
        if self.TESTMODE:
            return _test_mode(self.HOMESTATE, self.AWAYSTATE)
        elif has_bt:
            mac = device.get('mac')
            if mac:
                attempts = 0
                result = None
                dname = device.get('name', 'unknown')
                loglines.append('checking for %s at %s' % (dname, mac))
                while not result and attempts < 6:
                    bt_unavailable = False
                    try:
                        result = bluetooth.lookup_name(
                            mac, timeout=self.TIMEOUT)
                    except (IndexError, bluetooth.BluetoothError) as e:
                        loglines.append(
                            'error connecting to bluetooth, trying again in 10 seconds')
                        result = None
                        bt_unavailable = True
                    if not result:
                        attempts = attempts + 1
                        time.sleep(10)
                if bt_unavailable:
                    loglines.append('unable to connect to bluetooth')
                    return 'error', loglines
                elif result:
                    loglines.append('device found')
                    return self.HOMESTATE, loglines
                else:
                    loglines.append('device not found')
                    return self.AWAYSTATE, loglines
            else:
                loglines.append('no MAC address in device information')
        loglines.append('bluetooth python module unavialable or not loaded')
        return 'error', loglines
