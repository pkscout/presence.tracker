import random
import time
try:
    import bluetooth
    has_bt = True
except ImportError:
    has_bt = False


class BluetoothTracker:
    def __init__(self, config):
        self.TESTMODE = config.Get('testmode')
        self.HOMESTATE = config.Get('home_state')
        self.AWAYSTATE = config.Get('away_state')
        self.TIMEOUT = config.Get('bt_timeout')

    def GetDeviceStatus(self, device):
        loglines = []
        if self.TESTMODE:
            loglines.append('in test mode, sending back random result')
            result = random.randint(0, 1)
            if result == 1:
                return self.HOMESTATE, loglines
            else:
                return self.AWAYSTATE, loglines
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
                    except IndexError:
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
