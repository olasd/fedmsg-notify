# This file is a part of fedmsg-notify.
#
# fedmsg-notify is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# fedmsg-notify is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with fedmsg-notify.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2012 Red Hat, Inc.
# Author: Luke Macken <lmacken@redhat.com>

import sys
import dbus
import fedmsg.text

from gi.repository import Gtk, Gio


class FedmsgNotifyConfigWindow(Gtk.ApplicationWindow):
    bus_name = 'org.fedoraproject.fedmsg.notify'
    obj_path = '/org/fedoraproject/fedmsg/notify'

    _switches = {}  # {Gtk.Switch: signal connection}

    def __init__(self, app):
        Gtk.Window.__init__(self, title="fedmsg-notify-config", application=app)
        self.set_default_size(300, 100)
        self.set_border_width(10)
        self.settings = Gio.Settings.new(self.bus_name)

        self.bus = dbus.SessionBus()
        running = self.bus.name_has_owner(self.bus_name)

        self.all_switch = Gtk.Switch()
        self.all_toggle_label = Gtk.Label()
        self.all_toggle_label.set_text("Fedmsg Desktop Notifications")
        self.grid = Gtk.Grid()
        self.grid.set_column_spacing(10)
        self.grid.attach(self.all_toggle_label, 1, 0, 1, 1)
        self.grid.attach(self.all_switch, 0, 0, 1, 1)
        self.add(self.grid)
        self.scan_text_processors()

        self.connect_signal_handlers()

        enabled = self.settings.get_boolean('enabled')
        if enabled and not running:
            self.toggle_service(True)
        elif running and not enabled:
            self.toggle_service(False)
        elif enabled and running:
            self.disconnect_signal_handlers()
            self.all_switch.set_active(True)
            self.connect_signal_handlers()

    def scan_text_processors(self):
        """ Create an on/off switch for each fedmsg text processor """
        top_label = self.all_toggle_label
        top_switch = self.all_switch
        for i, processor in enumerate(fedmsg.text.processors):
            label = Gtk.Label()
            label.set_text(processor.__obj__)
            switch = Gtk.Switch()
            switch.__name__ = processor.__obj__
            self._switches[switch] = None
            self.grid.attach_next_to(label, top_label,
                                     Gtk.PositionType.BOTTOM, 1, 1)
            self.grid.attach_next_to(switch, top_switch,
                                     Gtk.PositionType.BOTTOM, 1, 1)
            top_label = label
            top_switch = switch

    def activate_filter_switch(self, button, active):
        """ Called when the text processor specific filters are selected """
        print(button.__name__)

    def activate_cb(self, button, active):
        self.toggle_service(button.get_active())

    def toggle_service(self, state):
        try:
            notify_obj = self.bus.get_object(self.bus_name, self.obj_path)
        except dbus.exceptions.DBusException, e:
            print(str(e))
            self.all_switch.set_active(False)
            return False
        notify_iface = dbus.Interface(notify_obj, self.bus_name)
        if state:
            notify_iface.Enable()
        else:
            notify_iface.Disable()
        self.all_switch.set_active(state)
        self.disconnect_signal_handlers()
        self.settings.set_boolean('enabled', state)
        self.connect_signal_handlers()

    def connect_signal_handlers(self):
        self.setting_conn = self.settings.connect(
            'changed::enabled', self.settings_changed)
        self.switch_conn = self.all_switch.connect(
            "notify::active", self.activate_cb)
        for switch in self._switches:
            self._switches[switch] = switch.connect(
                'notify::active', self.activate_filter_switch)

    def disconnect_signal_handlers(self):
        self.settings.disconnect(self.setting_conn)
        self.all_switch.disconnect(self.switch_conn)
        for switch, switch_conn in self._switches.iteritems():
            print(repr(switch_conn))
            switch.disconnect(switch_conn)
            self._switches[switch] = None

    def settings_changed(self, settings, key):
        self.disconnect_signal_handlers()
        self.all_switch.set_active(settings.get_boolean(key))
        self.connect_signal_handlers()


class FedmsgNotifyConfigApp(Gtk.Application):

    def do_activate(self):
        win = FedmsgNotifyConfigWindow(self)
        win.show_all()

    def do_startup(self):
        Gtk.Application.do_startup(self)


def main():
    app = FedmsgNotifyConfigApp()
    sys.exit(app.run(sys.argv))

if __name__ == '__main__':
    main()

# vim: ts=4 sw=4 expandtab ai
