################################################################################
# pymyo.py
# A small module for interaction with a Myo band using raw bluetooth
# connection(s). It is build around cffi bindings for the myohw header
# and bluepy.
#
#-------------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
#
# <lbromo@protonmail.ch> wrote this file. As long as you retain this notice
# you can do whatever you want with this stuff. If we meet some day, and you
# think this stuff is worth it, you can buy me a beer in return.
#
# - Lasse Bromose
#-------------------------------------------------------------------------------
################################################################################
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

class EMG(object):

    def __init__(self, raw_emg_meas):
        self._myohw_emg_data_t = ffi.new('myohw_emg_data_t *', (raw_emg_meas[0:8], raw_emg_meas[8:]))
        self.sample1 = self._myohw_emg_data_t.sample1
        self.sample2 = self._myohw_emg_data_t.sample2

    def __repr__(self):
        return "EMG Measurement:\nsample1: {}\nsample2: {}".format(
            list(self.sample1),
            list(self.sample2))

class IMU(object):

    class Orientation(object):

        def __init__(self, w, x, y, z):
            self.w = w
            self.x = x
            self.y = y
            self.z = z

        def __repr__(self):
            return "Orientation: w={}, x={} y={} z={}".format(
                self.w, self.x, self.y, self.z
            )

    def __init__(self, raw_imu_meas):
        orientations_meas = raw_imu_meas[0:4*2]
        acc_meas = raw_imu_meas[4*2:4*2 + 3*2]
        gyro_meas = raw_imu_meas[4*2 + 3*2:]

        self._myohw_imu_data_t =  ffi.new('myohw_imu_data_t *',
                                          (
                                              struct.unpack('4h', orientations_meas),
                                              struct.unpack('3h', acc_meas),
                                              struct.unpack('3h', gyro_meas)
                                          )
        )
        self.orientation = IMU.Orientation(
            self._myohw_imu_data_t.orientation.w,
            self._myohw_imu_data_t.orientation.x,
            self._myohw_imu_data_t.orientation.y,
            self._myohw_imu_data_t.orientation.z,
        )
        self.accelorameter = self._myohw_imu_data_t.accelerometer
        self.gyroscope = self._myohw_imu_data_t.gyroscope

    def __repr__(self):
        orientation = str(self.orientation)
        acc = "Accelorameter: {}".format(list(self.accelorameter))
        gyro = "Gyroscope: {}".format(list(self.gyroscope))
        return "IMU Measurement\n" + orientation + "\n" + acc + "\n" + gyro

class PyMyo(btle.DefaultDelegate):

    _SERVICE_CLASS_UUID = '4248124a7f2c4847b9de04a9xxxx06d5'

    def __init__(self, on_emg=None, on_imu=None, iface='0'):
        assert callable(on_emg) or on_emg == None, 'on_emg must be callable'
        assert callable(on_imu) or on_imu == None, 'on_imu must be callable'
        self.on_emg = on_emg
        self.on_imu = on_imu

        self.iface = iface
        self.scanner = btle.Scanner()
        self.scanner.withDelegate(self)
        self.devs = []

        self.peripheral = btle.Peripheral()

    def connect(self):
        self.scanner.scan(2)

        for dev in self.devs:
            try:
                self.peripheral.connect(dev.addr, iface=self.iface)
            except Exception as e:
                print("error connection:\n", e)
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
            self.imu_handles = self.__enable_all_characteristic__(lib.ImuDataService)

        if emg_mode:
            self.emg_handles = self.__enable_all_characteristic__(lib.EmgDataService)

        self.peripheral.withDelegate(self)
   
    def waitForNotifications(self, timeout=1):
        self.peripheral.waitForNotifications(timeout)

    def handleNotification(self, cHandle, data):
        if self.on_emg and cHandle in self.emg_handles:
            emg = EMG(data)
            self.on_emg(emg)
        elif self.on_imu and cHandle in self.imu_handles:
            imu = IMU(data)
            self.on_imu(imu)
        else:
            self.__default_on_data__(cHandle, data)

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

    def __enable_all_characteristic__(self, service_myohw_id):
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

        return [c.getHandle() for c in chars]

    def __default_on_data__(self, cHandle, data):
        if cHandle in self.emg_handles:
            emg = struct.unpack('16b', data)
            print(self.peripheral.iface, time.time(), cHandle, ' '.join([str(e) for e in emg]))
        elif cHandle in self.imu_handles:
            imu = struct.unpack('20b', data)
            print(self.peripheral.iface, time.time(), cHandle, ' '.join([str(e) for e in imu]))


    def __get_uuid__(self, myohw_id):
        tmp = '{0:04x}'.format(myohw_id)
        val = ''.join(reversed([tmp[i:i+2] for i in range(0, len(tmp), 2)]))
        tmp_UUID = PyMyo._SERVICE_CLASS_UUID.replace('xxxx', val)
        UUID = ''.join(reversed([tmp_UUID[i:i+2] for i in range(0, len(tmp_UUID), 2)]))

        return UUID

    def __set_sleep_mode__(self, sleep_mode):
        set_cmd = create_command(
            lib.myohw_command_set_sleep_mode, 1, # header
            sleep_mode # payload
        )

        service_UUID = self.__get_uuid__(lib.ControlService)
        service = self.peripheral.getServiceByUUID(service_UUID)

        char_UUID = self.__get_uuid__(lib.CommandCharacteristic)
        char = service.getCharacteristics(char_UUID)[0]

        cmd = to_bytes(set_cmd)
        self.peripheral.writeCharacteristic(char.getHandle(), cmd, True)

        self.peripheral.withDelegate(self) 


if __name__ == '__main__':
    on_meas = lambda m: print(m) 
    m1 = PyMyo(iface='0', on_emg=on_meas, on_imu=on_meas)
    m1.connect()

    # m2 = PyMyo(iface='1')
    # m2.connect()

    m1.enable_services(imu_mode=0)
    m1.__set_sleep_mode__(sleep_mode=lib.myohw_sleep_mode_never_sleep)
    # m2.enable_services(imu_mode=1)
    while True:
        m1.waitForNotifications()
        # m2.waitForNotifications()
