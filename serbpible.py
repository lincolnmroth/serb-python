#!/usr/bin/env python3
"""
BLE based on and using classes, functions from
https://git.kernel.org/pub/scm/bluetooth/bluez.git/tree/test/example-gatt-server
"""

import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GObject
import sys
from example_gatt_server import (Application as ExApplication, Service,
                                 Characteristic,
                                 find_adapter as find_adapter_gatt,
                                 BLUEZ_SERVICE_NAME, GATT_MANAGER_IFACE)
from example_advertisement import (Advertisement,
                                   find_adapter as find_adapter_ad,
                                   LE_ADVERTISING_MANAGER_IFACE)
import serbpictrl as s

DEV_ALL = 0
DEV_FRONT = 1
DEV_REAR = 2
DEV_TURN = 3
DEV_LOCK = 4
STATE_OFF = 0
STATE_ON = 1
STATE_LOW = 2
STATE_BLINK = 3
STATE_LEFT = 4
STATE_RIGHT = 5


class Application(ExApplication):
    def __init__(self, bus):
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)
        self.add_service(LightService(bus, 0))


class SerbAdvertisement(Advertisement):
    def __init__(self, bus, index):
        super().__init__(bus, index, 'peripheral')
        self.add_service_uuid(LightService.UUID)
        self.include_tx_power = True


class LightService(Service):
    UUID = 'fadedfad-edfa-dedf-aded-fadedfaded00'

    def __init__(self, bus, index):
        super().__init__(bus, index, self.UUID, True)
        self.add_characteristic(LightCharacteristic(bus, 0, self))


class LightCharacteristic(Characteristic):
    UUID = 'fadedfad-edfa-dedf-aded-fadedfaded01'

    def __init__(self, bus, index, service):
        super().__init__(bus, index, self.UUID, ['write'], service)

    def WriteValue(self, value, options):
        print('Write: ' + repr(value))
        device = value[0]
        state = value[1]
        if device == DEV_ALL:
            if state == STATE_ON:
                s.hazardLights()
            elif state == STATE_OFF:
                s.offAll()
        elif device == DEV_FRONT:
            if state == STATE_OFF:
                s.setFrontMode(s.MODE_OFF)
            elif state == STATE_ON:
                s.setFrontMode(s.MODE_HIGH)
            elif state == STATE_LOW:
                s.setFrontMode(s.MODE_LOW)
            elif state == STATE_BLINK:
                s.setFrontMode(s.MODE_BLINK)
        elif device == DEV_REAR:
            if state == STATE_OFF:
                s.offRear()
            elif state == STATE_ON:
                s.onRear()
            elif state == STATE_BLINK:
                s.startBlinkRear()
        elif device == DEV_TURN:
            if state == STATE_OFF:
                s.doneLeftTurn()
                s.doneRightTurn()
            elif state == STATE_LEFT:
                s.doneRightTurn()
                s.turnLeft()
            elif state == STATE_RIGHT:
                s.doneLeftTurn()
                s.turnRight()
        elif device == DEV_LOCK:
            if state == STATE_OFF:
                s.unlock()
            elif state == STATE_ON:
                s.lock()


def main():
    def register_ad_cb():
        print('Advertisement registered')

    def register_ad_error_cb(error):
        print('Failed to register advertisment: ' + str(error))
        mainloop.quit()

    def register_app_cb():
        print('GATT application registered')

    def register_app_error_cb(error):
        print('Failed to register application: ' + str(error))
        mainloop.quit()

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    adapter_gatt = find_adapter_gatt(bus)
    adapter_ad = find_adapter_ad(bus)
    if not adapter_gatt:
        print('Cannot find gatt adapter')
        sys.exit(1)
    if not adapter_ad:
        print('Cannot find ad adapter')
        sys.exit(1)
    adapter_props = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME,
                                                  adapter_ad),
                                   'org.freedesktop.DBus.Properties')
    adapter_props.Set('org.bluez.Adapter1', 'Powered', dbus.Boolean(1))
    service_manager = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME,
                                                    adapter_gatt),
                                     GATT_MANAGER_IFACE)
    ad_manager = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, adapter_ad),
                                LE_ADVERTISING_MANAGER_IFACE)
    app = Application(bus)
    ad = SerbAdvertisement(bus, 0)
    mainloop = GObject.MainLoop()
    service_manager.RegisterApplication(app.get_path(), {},
                                        reply_handler=register_app_cb,
                                        error_handler=register_app_error_cb)
    ad_manager.RegisterAdvertisement(ad.get_path(), {},
                                     reply_handler=register_ad_cb,
                                     error_handler=register_ad_error_cb)
    try:
        mainloop.run()
    except KeyboardInterrupt:
        pass
    finally:
        mainloop.quit()


if __name__ == '__main__':
    main()
