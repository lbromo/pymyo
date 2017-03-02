from bluepy import btle
from myohw import ffi, lib

import struct
import time

__DEBUG__ = 1

_create_cmd={
    lib.myohw_command_set_mode: lambda cmd, payload_size, payload: ffi.new('myohw_command_set_mode_t *', ((cmd, payload_size), *payload)),
    lib.myohw_command_vibrate: lambda cmd, payload_size, payload: ffi.new('myohw_command_vibrate_t *', ((cmd, payload_size), *payload)),
    lib.myohw_command_deep_sleep: lambda cmd, payload_size, payload: ffi.new('myohw_command_deep_sleep_t *', ((cmd, payload_size), *payload)),
    lib.myohw_command_vibrate2: lambda cmd, payload_size, payload: ffi.new('myohw_command_vibrate2_t *', ((cmd, payload_size), *payload)),
    lib.myohw_command_set_sleep_mode: lambda cmd, payload_size, payload: ffi.new('myohw_command_set_sleep_mode_t *', ((cmd, payload_size), *payload)),
    lib.myohw_command_unlock: lambda cmd, payload_size, payload: ffi.new('myohw_command_unlock_t *', ((cmd, payload_size), *payload)),
    lib.myohw_command_user_action: lambda cmd, payload_size, payload: ffi.new('myohw_command_user_action_t *', ((cmd, payload_size), *payload)),
}

def create_command(command, payload_size, *payload):
    return _create_cmd[command](command, payload_size, payload)

def to_bytes(cmd):
    buf = ffi.buffer(cmd)
    return bytes(buf)

class PyMyo(btle.DefaultDelegate):

    _SERVICE_CLASS_UUID = '4248124a7f2c4847b9de04a9xxxx06d5'

    def __init__(self, iface='/dev/vhci'):
        self.iface = iface
        self.scanner = btle.Scanner()
        self.scanner.withDelegate(self)
        self.devs = []

        self.peripheral = btle.Peripheral()
        self.peripheral.withDelegate(self)

    def connect(self):
        self.scanner.scan(2)

        for dev in self.devs:
            try:
                self.peripheral.connect(dev.addr, iface=self.iface)
            except:
                print("error connection")
            else:
                break

    def enable_services(self,
                     emg_mode=lib.myohw_emg_mode_send_emg,
                     imu_mode=lib.myohw_imu_mode_none,
                     classifier_mode=lib.myohw_classifier_mode_disabled
    ):
        set_cmd = create_command(
            lib.myohw_command_set_mode, 3, # header
            emg_mode, imu_mode, classifier_mode # payload
        )

        service_UUID = self.__get_uuid__(lib.ControlService)
        service = self.peripheral.getServiceByUUID(service_UUID)

        char_UUID = self.__get_uuid__(lib.CommandCharacteristic)
        char = service.getCharacteristics(char_UUID)[0]

        cmd = to_bytes(set_cmd)
        self.peripheral.writeCharacteristic(char.getHandle(), cmd, True)

        if imu_mode:
            self.enable_all_characteristic(lib.ImuDataService)

        if emg_mode:
            self.enable_all_characteristic(lib.EmgDataService)

    def enable_all_characteristic(self, service_myohw_id):
        service_UUID = self.__get_uuid__(service_myohw_id)
        service = self.peripheral.getServiceByUUID(service_UUID)
        chars = service.getCharacteristics()

        for char in chars:
            # add one according to http://stackoverflow.com/questions/32807781/ble-subscribe-to-notification-using-gatttool-or-bluepy
            client_handle = char.getHandle() + 1
            if __DEBUG__:
                print(char.uuid)
                print('%x' % (client_handle) )
            self.peripheral.writeCharacteristic(client_handle, b'\x01\x00')

    def waitForNotifications(self, timeout=1):
        self.peripheral.waitForNotifications(timeout)

    def handleNotification(self, cHandle, data):
        emg = struct.unpack('16b', data)
        print(self.peripheral.iface, time.time(), cHandle, ' '.join([str(e) for e in emg]))

    def handleDiscovery(self, scanEntry, isNewDev, isNewData):
        tmp = '{0:04x}'.format(lib.ControlService)
        service_val = ''.join(reversed([tmp[i:i+2] for i in range(0, len(tmp), 2)]))
        UUID = PyMyo._SERVICE_CLASS_UUID.replace('xxxx', service_val)
        if isNewDev:
            if scanEntry.getValueText(0x06) == UUID:
                if scanEntry.connectable:
                   if __DEBUG__:
                       print('Myo found. Addr:', scanEntry.addr)
                   self.devs.append(scanEntry)

    def __get_uuid__(self, myohw_id):
        tmp = '{0:04x}'.format(myohw_id)
        val = ''.join(reversed([tmp[i:i+2] for i in range(0, len(tmp), 2)]))
        tmp_UUID = PyMyo._SERVICE_CLASS_UUID.replace('xxxx', val)
        UUID = ''.join(reversed([tmp_UUID[i:i+2] for i in range(0, len(tmp_UUID), 2)]))

        return UUID


if __name__ == '__main__':
    m1 = PyMyo(iface='0')
    m1.connect()

    m2 = PyMyo(iface='1')
    m2.connect()


    m1.enable_services()
    m2.enable_services()
    while True:
        m1.waitForNotifications()
        m2.waitForNotifications()
