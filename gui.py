from PyQt5 import QtWidgets, QtGui, QtCore
from win10toast import ToastNotifier
import trentbarton
import time


class TrentBartonThread(QtCore.QThread):

    reminder = QtCore.pyqtSignal(trentbarton.Bus)
    bus_icon = QtCore.pyqtSignal(QtGui.QIcon)
    stop_tracking = QtCore.pyqtSignal()
    status = QtCore.pyqtSignal(str)

    def __init__(self, bus, remind_at=5):
        super().__init__()
        self.bus_identifier = bus.identifier
        self.bus_stop = bus.bus_stop
        self.remind_at = remind_at

    def run(self):
        while True:
            live_times = self.bus_stop.get_live_times()
            if live_times:
                for bus in live_times:
                    if bus.identifier == self.bus_identifier:
                        tracked_bus = bus
                        break
                else:
                    break
                self.bus_icon.emit(QtGui.QIcon(str(tracked_bus.icon)))

                if tracked_bus.due <= self.remind_at and tracked_bus.identifier not in self.reminded:
                    self.reminder.emit(tracked_bus)
                    self.reminded.append(tracked_bus.identifier)
                else:
                    self.status.emit(f'{tracked_bus.name} is {tracked_bus.due} minutes away from {self.bus_stop}')

            else:
                self.status.emit(f'There are no buses for {self.bus_stop} within the hour.')
                self.bus_icon.emit(QtGui.QIcon('trentbarton.png'))

            time.sleep(30)
        self.stop_tracking.emit()


class BusStopMenu(QtWidgets.QMenu):

    begin_tracking = QtCore.pyqtSignal(trentbarton.Bus)

    def __init__(self, bus_stop):
        super().__init__()
        self.bus_stop = bus_stop
        self.aboutToShow.connect(self.update_buses)

    def update_buses(self):
        self.clear()
        self.title_widget()
        live_times = self.bus_stop.get_live_times()
        for bus in live_times:
            self.addAction(QtGui.QIcon(str(bus.icon)), f'{bus.name} - {bus.due} minutes',
                           lambda: self.begin_tracking.emit(bus))

    def title_widget(self):
        widget = QtWidgets.QWidgetAction(self)
        label = QtWidgets.QLabel(self.bus_stop.name)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setStyleSheet('font-weight: bold; padding: 0.2em;')
        widget.setDefaultWidget(label)
        self.addAction(widget)

class TrentBartonSystemTray(QtWidgets.QSystemTrayIcon):
    def __init__(self, bus_stop):
        super().__init__()
        self.setIcon(QtGui.QIcon('trentbarton.png'))
        self.bus_stop = bus_stop
        self.menu = BusStopMenu(self.bus_stop)
        self.menu.begin_tracking.connect(self.start_watching)
        self.setContextMenu(self.menu)
        self.setToolTip(f'Not tracking any buses at the moment ({self.bus_stop})')

    def start_watching(self, bus):
        """Start watching and tracking a bus"""
        self.watcher = TrentBartonThread(bus)
        self.watcher.reminder.connect(self.notify)
        self.watcher.status.connect(self.setToolTip)
        self.watcher.bus_icon.connect(self.setIcon)
        self.watcher.start()

    def notify(self, bus):
        """Notify how close a bus is with toast notifications"""
        toaster = ToastNotifier()
        toaster.show_toast(bus.bus_stop.name, f'{bus} is {bus.due} minutes away',
                           icon_path=bus.icon, duration=7, threaded=True)