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
        self.running = True

    def stop(self):
        self.running = False

    def run(self):
        while self.running:
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
    stop_tracking = QtCore.pyqtSignal()

    def __init__(self, bus_stop):
        super().__init__()
        self.currently_tracking = None
        self.bus_stop = bus_stop
        self.aboutToShow.connect(self.update_buses)

    def update_buses(self):
        self.clear()
        self.title_widget()
        live_times = self.bus_stop.get_live_times()
        for bus in live_times:
            if bus.identifier == self.currently_tracking:
                self.addAction(QtGui.QIcon(str(bus.icon)), f'✓ {bus.name} - {bus.due} minutes ({bus.time})',
                               self.untrack)
            else:
                self.addAction(QtGui.QIcon(str(bus.icon)), f'{bus.name} - {bus.due} minutes ({bus.time})',
                               lambda: self.track(bus))

    def title_widget(self):
        widget = QtWidgets.QWidgetAction(self)
        label = QtWidgets.QLabel(self.bus_stop.name)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setStyleSheet('font-weight: bold;'
                            'padding: 0.2em;'
                            'background: #393939;'
                            'color: #fff;'
                            'margin-bottom: 0.2em;')
        widget.setDefaultWidget(label)
        self.addAction(widget)

    def track(self, bus):
        self.currently_tracking = bus.identifier
        self.begin_tracking.emit(bus)

    def untrack(self):
        self.currently_tracking = None
        self.stop_tracking.emit()

class TrentBartonSystemTray(QtWidgets.QSystemTrayIcon):
    def __init__(self, bus_stop):
        super().__init__()
        self.bus_stop = bus_stop
        self.watcher = None
        self.menu = BusStopMenu(self.bus_stop)
        self.menu.begin_tracking.connect(self.start_watching)
        self.menu.stop_tracking.connect(self.stop_watching)
        self.setContextMenu(self.menu)
        self.reset()

    def reset(self):
        self.setIcon(QtGui.QIcon('systemtrayicon.png'))
        self.setToolTip(f'Not tracking any buses at the moment ({self.bus_stop})')

    def start_watching(self, bus):
        """Start watching and tracking a bus"""
        if self.watcher and self.watcher.isRunning():
            self.stop_watching()
        self.watcher = TrentBartonThread(bus)
        self.watcher.reminder.connect(self.notify)
        self.watcher.status.connect(self.setToolTip)
        self.watcher.bus_icon.connect(self.setIcon)
        self.watcher.stop_tracking.connect(self.menu.untrack)
        self.watcher.start()

    def stop_watching(self):
        self.watcher.stop()
        self.reset()

    def notify(self, bus):
        """Notify how close a bus is with toast notifications"""
        toaster = ToastNotifier()
        toaster.show_toast(bus.bus_stop.name, f'{bus} is {bus.due} minutes away',
                           icon_path=bus.icon, duration=7, threaded=True)