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
        if self.TESTMODE:
            result = random.randint(0, 1)
            if result == 1:
                return self.HOMESTATE
            else:
                return self.AWAYSTATE
        elif has_bt:
            mac = device.get('mac')
            if mac:
                bt_unavailable = True
                got_result = True
                attempts = 0
                result = None
                while bt_unavailable:
                    try:
                        result = bluetooth.lookup_name(
                            mac, timeout=self.TIMEOUT)
                    except IndexError:
                        got_result = False
                    if not got_result and attempts < 6:
                        time.sleep(10)
                        attempts = attempts + 1
                    else:
                        bt_unavailable = False
                if result:
                    return self.HOMESTATE
                else:
                    return self.AWAYSTATE
        return 'error'
